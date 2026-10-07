# ------------------------------------------------------------------
# Flask application
# ------------------------------------------------------------------

from datetime import datetime, timezone
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
from backend.services.reports.report_queue_runner import ReportQueueRunner
from backend.services.seismic_observatory_service import SeismicObservatoryService
from backend.services.scenario.scenario_errors import ScenarioValidationError
from backend.services.socket.realtime_service import init_realtime
from backend.services.event_engine import EventEngine
from backend.services.ai_client.event_generator_client import AIEventClient
from backend.services.stress.stress_mode_service import StressModeService
from backend.services.scenario.scenario_generator_service import ScenarioGeneratorService
from backend.services.scenario.scenario_validator import ScenarioValidator
from backend.services.socket.socket_broadcaster import SocketBroadcaster
from backend.services.ai_client.event_bus import mode_changed, scenario_loaded
from backend.services.parameters.scenario_parameters_service import ScenarioParametersService
from backend.services.json_export_service import JSONExportService
from backend.services.ai_client.ai_generation_loop import AiGenerationLoop


# ------------------------------------------------------------------
# App setup
# ------------------------------------------------------------------

app = Flask(__name__)
CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
init_realtime(socketio)


# ------------------------------------------------------------------
# Service wiring
# ------------------------------------------------------------------

parameters_service = ScenarioParametersService()
obs_service = SeismicObservatoryService(parameters_service=parameters_service)
event_engine = EventEngine(
    socketio=socketio,
    service=obs_service,
    mode_changed=mode_changed,
    stress_mode_manager=StressModeService(),
    parameters_service=parameters_service,
)
socket_broadcaster = SocketBroadcaster(mode_changed, scenario_loaded)
ai_client = AIEventClient()
ai_loop = AiGenerationLoop(socketio, event_engine)
event_engine.set_ai_generation_loop(ai_loop)
scenario_validator = ScenarioValidator(parameters_service=parameters_service)
json_export_service = JSONExportService(parameters_service=parameters_service)

generator_manager = ScenarioGeneratorService(ai_client=ai_client, engine=event_engine)
event_engine.set_scenario_manager(generator_manager)
event_engine.set_scenario_validator(scenario_validator)
event_engine.set_scenario_loaded_notifier(scenario_loaded)

# Keep one queue facade attached to the active EventEngine.
report_queue_runner = ReportQueueRunner(event_engine)
manual_event_minimums = {}


# ------------------------------------------------------------------
# REST routes: scenario and export
# ------------------------------------------------------------------

# Return the active observatory as a dictionary
@app.route("/api/seismic-observatory", methods=["GET"])
def getSeismicObservatory():
    return jsonify(event_engine.get_or_load_observatory().toDict())


# Export the active scenario as JSON and register a new version
@app.route("/api/export/json", methods=["GET"])
def export_scenario_json():
    observatory = event_engine.get_or_load_observatory()
    with event_engine.lock:
        if observatory is None or observatory.getScenarioId() is None:
            return jsonify({"ok": False, "reason": "no_scenario"}), 404
        data = json_export_service.export(observatory)
    return jsonify(data)


# Return the current scenario snapshot without registering a version
@app.route("/api/scenario/snapshot", methods=["GET"])
def get_scenario_snapshot():
    observatory = event_engine.get_or_load_observatory()
    with event_engine.lock:
        if observatory is None or observatory.getScenarioId() is None:
            return jsonify({"ok": False, "reason": "no_scenario"}), 404
        data = json_export_service.snapshot(observatory)
    return jsonify(data)


# Legacy JSON loading endpoint retained for API compatibility.
@app.route("/api/scenario", methods=["GET"])
def load_scenario():
    # Keep this legacy endpoint compatible while using the active validator.
    data = request.get_json(silent=True)
    stress_mode = isinstance(data, dict) and data.get("execution_mode") == "stress"
    result = scenario_validator.load(data, stress_mode)
    return jsonify(result)


# ------------------------------------------------------------------
# REST routes: parameters
# ------------------------------------------------------------------

# Return the current scenario parameters
@app.route("/api/parameters", methods=["GET"])
def get_parameters():
    return jsonify(event_engine.get_parameters())


# Update the scenario parameters
@app.route("/api/parameters", methods=["PATCH"])
def update_parameters():
    result = event_engine.update_parameters(request.get_json(silent=True))
    status_code = 200 if result.get("ok") else 400
    return jsonify(result), status_code


# ------------------------------------------------------------------
# REST routes: events
# ------------------------------------------------------------------

# Create an event from the frontend request
@app.route("/api/events", methods=["POST"])
def createEvent():
    # The request body is the object received from the frontend.
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "reason": "Request body must be a JSON object",
        }), 400

    # Validate the transport-level required fields before entering the engine.
    required_fields = [
        "id",
        "magnitude",
        "depth",
        "epicenter_x",
        "epicenter_y",
        "datetime",
        "revision",
        "station"
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({
                "success": False,
                "reason": f"Missing field: {field}"
            }), 400

    response = event_engine.create_event_from_api(data)

    if not response["success"]:
        return jsonify(response), 400
    return jsonify(response), 201


# Return the list of active events
@app.route("/api/events-list", methods=["GET"])
def getEvents():
    return jsonify(event_engine.get_active_events())


# Return one active event by its id (used for editing)
@app.route("/api/events/<int:event_id>", methods=["GET"])
def get_event_by_id(event_id):
    event = event_engine.get_active_event(event_id)
    if event is None:
        return jsonify({
            "ok": False,
            "reason": "event_not_found"
        }), 404
    return jsonify(event)


# Mark an event as reviewed
@app.route("/api/events/<int:event_id>/attention-status", methods=["PATCH"])
def update_event_attention_status(event_id):
    result = event_engine.mark_event_as_reviewed(event_id)

    if not result["ok"]:
        if result["reason"] == "no_event":
            status_code = 404
        else:
            status_code = 400
        return jsonify(result), status_code

    return jsonify(result["event"])


# Delete an event by its id
@app.route("/api/events/<int:event_id>", methods=["DELETE"])
def delete_event(event_id):
    result = event_engine.delete_event_by_id(event_id)

    if not result["ok"]:
        if result["reason"] == "event_not_found":
            return jsonify(result), 404
        if result["reason"] in ["busy", "no_scenario"]:
            return jsonify(result), 404

        return jsonify(result), 400

    return jsonify(result), 200


# ------------------------------------------------------------------
# REST routes: history
# ------------------------------------------------------------------

# Return the historical counters
@app.route("/api/history", methods=["GET"])
def get_history_summary():
    result = event_engine.get_history_summary()
    status_code = 200 if result.get("ok") else 404
    return jsonify(result), status_code


# Return the archived events
@app.route("/api/history/archived-events", methods=["GET"])
def get_archived_events():
    result = event_engine.get_archived_events()
    status_code = 200 if result.get("ok") else 404
    return jsonify(result), status_code


# Return the deleted events
@app.route("/api/history/deleted-events", methods=["GET"])
def get_deleted_events():
    result = event_engine.get_deleted_events()
    status_code = 200 if result.get("ok") else 404
    return jsonify(result), status_code


# Return the identifiers kept by the historical index
@app.route("/api/history/identifiers", methods=["GET"])
def get_historical_ids():
    result = event_engine.get_historical_ids()
    status_code = 200 if result.get("ok") else 404
    return jsonify(result), status_code


# ------------------------------------------------------------------
# REST routes: associations and queries
# ------------------------------------------------------------------

# Return the current W and R association limits
@app.route("/api/associations/limits", methods=["GET"])
def get_association_limits():
    result = event_engine.get_association_limits()
    status_code = 200 if result.get("ok") else 404
    return jsonify(result), status_code


# Update the W and R association limits
@app.route("/api/associations/limits", methods=["PATCH"])
def update_association_limits():
    result = event_engine.update_association_limits(request.get_json(silent=True))
    status_code = 200 if result.get("ok") else 400
    if result.get("reason") == "no_scenario":
        status_code = 404
    return jsonify(result), status_code


# Read-only query endpoint. The engine remains the single application coordinator.
@app.route("/api/queries", methods=["POST"])
def execute_query():
    result = event_engine.execute_query(request.get_json(silent=True))
    if not result.get("ok"):
        status_code = 404 if result.get("reason") == "no_scenario" else 400
        return jsonify(result), status_code
    return jsonify(result)


# Return height, depth, priority, and costly-access status by tree
@app.route("/api/tree-characteristics", methods=["GET"])
def get_tree_characteristics():
    result = event_engine.get_tree_characteristics()
    status_code = 200 if result.get("ok") else 404
    return jsonify(result), status_code


# ------------------------------------------------------------------
# Socket handlers: connection
# ------------------------------------------------------------------

# Log a client connection
@socketio.on("connect")
def handle_connect():
    print("Cliente conectado por WebSocket")


# Forget the client's manual session and log the disconnection
@socketio.on("disconnect")
def handle_disconnect():
    manual_event_minimums.pop(request.sid, None)
    print("Cliente desconectado del WebSocket")


# ------------------------------------------------------------------
# Socket handlers: manual events
# ------------------------------------------------------------------

# Start a manual event session and return its minimum allowed datetime
@socketio.on("manual-event:begin")
def handle_manual_event_begin(_data=None):
    observatory = event_engine.get_observatory()
    if observatory is None:
        return {"ok": False, "reason": "no_scenario"}

    # Manual events must start from the active simulation clock, not wall time.
    # The browser input has minute precision. Use the beginning of the
    # current simulated minute so that a value such as 10:00:00 remains valid
    # while the authoritative clock is already at 10:00:57.
    minimum = observatory.getClock().getCurrentTime().replace(second=0, microsecond=0)
    manual_event_minimums[request.sid] = minimum
    return {"ok": True, "minimumDatetime": minimum.isoformat()}


# Create a manual event if its datetime respects the session minimum
@socketio.on("manual-event:create")
def handle_manual_event_create(data):
    minimum = manual_event_minimums.get(request.sid)
    if minimum is None:
        return {"ok": False, "reason": "manual_session_required"}

    try:
        event_datetime = datetime.fromisoformat(str(data.get("datetime", "")).replace("Z", "+00:00"))
        if event_datetime.tzinfo is None:
            event_datetime = event_datetime.replace(tzinfo=timezone.utc)
        if event_datetime.astimezone(timezone.utc) < minimum:
            return {"ok": False, "reason": "datetime_before_form"}
        operation = event_engine.create_manual_event(data)
    except (AttributeError, TypeError, ValueError) as error:
        return {"ok": False, "reason": str(error)}

    return {"ok": True, "operation": operation}


# Receptor of the manual event update change or solicitude
@socketio.on("manual-event:update")
def handle_manual_event_update(data):
    if not isinstance(data, dict):
        return {
            "ok": False,
            "Reason": "invalid_request"
        }
    return event_engine.update_manual_event(data)


# ------------------------------------------------------------------
# Socket handlers: generation and execution mode
# ------------------------------------------------------------------

# Start the event generator for the active scenario
@socketio.on("generation:start")
def handle_generation_start(_data=None):
    if event_engine.get_observatory() is None:
        return {"ok": False, "reason": "no_scenario"}
    ok, reason = generator_manager.start()
    return {"ok": ok, "reason": reason}


# Switch the execution mode between normal and stress
@socketio.on("mode:set")
def handle_mode_set(data):
    mode = data.get("mode") if isinstance(data, dict) else None
    print(f"Solicitud de cambio de modo hacia: {mode}")
    return event_engine.request_mode(mode)


# ------------------------------------------------------------------
# Socket handlers: scenario
# ------------------------------------------------------------------

# Return whether a scenario is loaded, with its id and current time
@socketio.on("scenario:status")
def handle_scenario_status():
    observatory = event_engine.get_observatory()
    return {
        "loaded": observatory is not None,
        "scenarioId": observatory.getScenarioId() if observatory is not None else None,
        "currentTime": (
            observatory.getClock().getCurrentTimeText()
            if observatory is not None else None
        ),
    }


# Load a scenario from a file or from the AI generator
@socketio.on("scenario:load")
def handle_scenario_load(data):
    if not isinstance(data, dict):
        return {"ok": False, "reason": "invalid_request"}

    source = data.get("source")
    print(f"Solicitud de carga de escenario. Tipo: {source}")

    if source not in ["file", "ai"]:
        return {"ok": False, "reason": "invalid_source"}

    if event_engine.recovering:
        return {"ok": False, "reason": "busy"}

    try:
        if source == "file":
            observatory = event_engine.load_scenario_from_text(data.get("content"))
        else:
            # The frontend sends the AI mode in "aiMode" or "content".
            observatory = event_engine.load_scenario_from_ai(data.get("content"))

    except ScenarioValidationError as error:
        return {"ok": False, "reason": "invalid_scenario", "issues": error.issues}

    except Exception as error:
        print(f"Error cargando el escenario: {error}")
        return {"ok": False, "reason": "server_error"}

    # The engine has validated and activated the scenario before this response.
    payload = {
        "scenarioId": observatory.scenario_id,
        "mode": observatory.getExecutionMode(),
        "stations": len(observatory.getStations()),
        "events": len(observatory.getAVLTree().index),
        "currentTime": observatory.getClock().getCurrentTimeText(),
    }
    print(f"Escenario cargado: {payload}")
    return {"ok": True, "scenario": payload}


# ------------------------------------------------------------------
# Socket handlers: clock
# ------------------------------------------------------------------

# Advance the simulation clock through the engine-owned API
@socketio.on("clock:advance")
def handle_clock_advance(data=None):
    data = data if isinstance(data, dict) else {}
    if "hours" in data:
        try:
            return event_engine.advance_clock_hours(data["hours"])
        except (TypeError, ValueError) as error:
            return {"ok": False, "reason": str(error)}

    if "datetime" in data:
        try:
            return event_engine.advance_clock_to(data["datetime"])
        except (TypeError, ValueError) as error:
            return {"ok": False, "reason": str(error)}

    return {"ok": False, "reason": "missing_clock_advance_value"}


# ------------------------------------------------------------------
# Socket handlers: undo and audit
# ------------------------------------------------------------------

# Undo the latest completed action through the Event Engine
@socketio.on("action:undo")
def handle_action_undo(_data=None):
    return event_engine.undo_action()


# Delegate the read-only audit to the engine-owned service boundary
@socketio.on("structure:audit")
def handle_structure_audit(_data=None):
    print("Solicitud de auditar estructura")
    return event_engine.audit_structure()


# ------------------------------------------------------------------
# Socket handlers: archiving
# ------------------------------------------------------------------

# Select and preview the subtree to archive
@socketio.on("paint:tree")
def handle_paint_tree(data=None):
    data = data if isinstance(data, dict) else {}
    return event_engine.prepare_archive_tree(data.get("T"), request.sid)


# Apply the client's archive decision
@socketio.on("archive:decision")
def handle_archive_decision(data=None):
    data = data if isinstance(data, dict) else {}
    return event_engine.decide_archive_tree(data.get("archive"), request.sid)


# ------------------------------------------------------------------
# Socket handlers: reports
# ------------------------------------------------------------------

# Validate and enqueue a complete report batch
@socketio.on("reports:prepare")
def prepare_reports(data):
    # The engine validates the complete batch before adding it to the FIFO queue.
    if not isinstance(data, dict) or "reports" not in data:
        return {
            "ok": False,
            "enqueued": 0,
            "issues": ["La solicitud debe contener una propiedad reports"],
        }
    return report_queue_runner.prepare_reports(data["reports"])


# Receive one manual report through the same engine queue flow
@socketio.on("reports:create")
def create_manual_report(data=None):
    return event_engine.create_manual_report(data)


# Start continuous AI report generation through the EventEngine
@socketio.on("reports:ai_start")
def handle_ai_generation_start(payload=None):
    return event_engine.start_ai_report_generation(payload)


# Stop continuous AI report generation through the EventEngine
@socketio.on("reports:ai_stop")
def handle_ai_generation_stop(_data=None):
    return event_engine.stop_ai_report_generation()


# Return the AI report worker status through the EventEngine
@socketio.on("reports:ai_status_get")
def handle_ai_generation_status(_data=None):
    return event_engine.ai_report_generation_status()


# Process exactly one report through the engine-owned lifecycle
@socketio.on("reports:step")
def process_report_step(data=None):
    return report_queue_runner.process_next()


# Start the background loop; it stops automatically when the queue is empty
@socketio.on("reports:start")
def start_report_processing(data=None):
    return report_queue_runner.start_continuous()


# Pause processing without removing pending reports
@socketio.on("reports:pause")
def pause_report_processing(data=None):
    return report_queue_runner.pause()


# Read the queue under the same lock used by report processing
@socketio.on("reports:snapshot")
def report_queue_snapshot(data=None):
    return report_queue_runner.snapshot()


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    event_engine.start()
    socketio.run(app, debug=True, use_reloader=False)
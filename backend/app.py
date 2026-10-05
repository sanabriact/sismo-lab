from datetime import datetime, timezone
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
from backend.services.reports.report_queue_runner import ReportQueueRunner
from backend.utils.json_utils import objectToDict
from backend.services.seismic_observatory_service import SeismicObservatoryService, ScenarioValidationError
from backend.services.socket.realtime_service import init_realtime
from backend.services.event_engine import EventEngine
from backend.services.ai_client.event_generator_client import AIEventClient 
from backend.managers.stress_mode_manager import StressModeManager
from backend.managers.scenario_generator_manager import ScenarioGeneratorManager
from backend.managers.load_scenario_manager import LoadScenarioManager
from backend.services.socket.socket_broadcaster import SocketBroadcaster
from backend.services.ai_client.event_bus import mode_changed, scenario_loaded
from backend.services.parameters.scenario_parameters_service import ScenarioParametersService
from backend.services.json_export_service import JSONExportService
from backend.helpers.ai_generation_loop import AiGenerationLoop

app = Flask(__name__)
CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
init_realtime(socketio)
parameters_service = ScenarioParametersService()
obs_service = SeismicObservatoryService(parameters_service=parameters_service)
event_engine = EventEngine(
    socketio=socketio,
    service=obs_service,
    mode_changed=mode_changed,
    stress_mode_manager=StressModeManager(),
    parameters_service=parameters_service,
)
socket_broadcaster = SocketBroadcaster(mode_changed, scenario_loaded)
ai_client = AIEventClient()
ai_loop = AiGenerationLoop(socketio, event_engine)
MIN_INTERVAL_SECONDS = 2
load_scenario_manager = LoadScenarioManager(parameters_service=parameters_service)
json_export_service = JSONExportService(parameters_service=parameters_service)

generator_manager = ScenarioGeneratorManager( ai_client=ai_client, engine=event_engine)
event_engine.set_scenario_manager(generator_manager)
event_engine.set_scenario_validator(load_scenario_manager)
event_engine.set_scenario_loaded_notifier(scenario_loaded)

# Keep one queue facade attached to the active EventEngine.
report_queue_runner = ReportQueueRunner(event_engine)
manual_event_minimums = {}

"""Flask REST API routes."""
@app.route("/api/seismic-observatory", methods=["GET"])
def getSeismicObservatory():
    return jsonify(event_engine.get_or_load_observatory().toDict())

@app.route("/api/export/json", methods=["GET"])
def export_scenario_json():
    observatory = event_engine.get_or_load_observatory()
    with event_engine.lock:
        if observatory is None or observatory.getScenarioId() is None:
            return jsonify({"ok": False, "reason": "no_scenario"}), 404
        data = json_export_service.export(observatory)
    return jsonify(data)

@app.route("/api/parameters", methods=["GET"])
def get_parameters():
    return jsonify(event_engine.get_parameters())

@app.route("/api/parameters", methods=["PATCH"])
def update_parameters():
    result = event_engine.update_parameters(request.get_json(silent=True))
    status_code = 200 if result.get("ok") else 400
    return jsonify(result), status_code

@app.route("/api/events", methods=["POST"])
def createEvent():
    # The request body is the object received from the frontend.
    data = request.json
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
 
# Legacy JSON loading endpoint retained for API compatibility.
@app.route("/api/scenario", methods=["GET"])
def load_scenario():
    data = request.get_json()
    result = load_scenario_manager.load(data)
    return jsonify(result)

@app.route("/api/events-list", methods=["GET"])
def getEvents():
    return jsonify(event_engine.get_active_events())

@app.route("/api/history", methods=["GET"])
def get_history_summary():
    result = event_engine.get_history_summary()
    status_code = 200 if result.get("ok") else 404
    return jsonify(result), status_code

@app.route("/api/history/archived-events", methods=["GET"])
def get_archived_events():
    result = event_engine.get_archived_events()
    status_code = 200 if result.get("ok") else 404
    return jsonify(result), status_code

@app.route("/api/history/deleted-events", methods=["GET"])
def get_deleted_events():
    result = event_engine.get_deleted_events()
    status_code = 200 if result.get("ok") else 404
    return jsonify(result), status_code

@app.route("/api/history/identifiers", methods=["GET"])
def get_historical_ids():
    result = event_engine.get_historical_ids()
    status_code = 200 if result.get("ok") else 404
    return jsonify(result), status_code

@app.route("/api/associations/limits", methods=["GET"])
def get_association_limits():
    result = event_engine.get_association_limits()
    status_code = 200 if result.get("ok") else 404
    return jsonify(result), status_code

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

@app.route("/api/tree-characteristics", methods=["GET"])
def get_tree_characteristics():
    result = event_engine.get_tree_characteristics()
    status_code = 200 if result.get("ok") else 404
    return jsonify(result), status_code

# Route for editing a event based on its id
@app.route("/api/events/<int:event_id>", methods=["GET"])
def get_event_by_id(event_id):
    event = event_engine.get_active_event(event_id)
    if event is None:
        return jsonify({
            "ok": False,
            "reason": "event_not_found"
        }), 404
    return jsonify(event)

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
    
@socketio.on("connect")
def handle_connect():
    print("Cliente conectado por WebSocket")

@socketio.on("disconnect")
def handle_disconnect():
    manual_event_minimums.pop(request.sid, None)
    print("Cliente desconectado del WebSocket")

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

@socketio.on("generation:start")
def handle_generation_start(_data=None):
    if event_engine.get_observatory() is None:
        return {"ok": False, "reason": "no_scenario"}
    ok, reason = generator_manager.start()
    return {"ok": ok, "reason": reason}

@socketio.on("mode:set")
def handle_mode_set(data):
    mode = data.get("mode") if isinstance(data, dict) else None
    print(f"Solicitud de cambio de modo hacia: {mode}")
    return event_engine.request_mode(mode)

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

@socketio.on("clock:advance")
def handle_clock_advance(data=None):
    """Advance the simulation clock through the engine-owned API."""
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

@socketio.on("action:undo")
def handle_action_undo(_data=None):
    """Undo the latest completed action through the Event Engine."""
    return event_engine.undo_action()
    
@socketio.on("structure:audit")
def handle_structure_audit(_data=None):
    """Delegate the read-only audit to the engine-owned service boundary."""
    print("Solicitud de auditar estructura")
    return event_engine.audit_structure()

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

@socketio.on("paint:tree")
def handle_paint_tree(data=None):
    data = data if isinstance(data, dict) else {}
    return event_engine.prepare_archive_tree(data.get("T"), request.sid)


@socketio.on("archive:decision")
def handle_archive_decision(data=None):
    data = data if isinstance(data, dict) else {}
    return event_engine.decide_archive_tree(data.get("archive"), request.sid)

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

@socketio.on("reports:create")
def create_manual_report(data=None):
    """Receive one manual report through the same engine queue flow."""
    return event_engine.create_manual_report(data)

@socketio.on("reports:ai_start")
def handle_ai_generation_start(payload=None):
    """Validate the configuration and start the continuous AI generation."""
    payload = payload if isinstance(payload, dict) else {}

    interval = max(
        MIN_INTERVAL_SECONDS,
        float(payload.get("intervalSeconds", 10))
    )

    known_stations = event_engine.observatory.getStations()
    known_ids = [station.getId() for station in known_stations]

    requested_ids = payload.get("stationIds")

    station_ids = (
        [station_id for station_id in requested_ids if station_id in known_ids]
        if requested_ids
        else known_ids
    )

    if not station_ids:
        return {
            "ok": False,
            "running": ai_loop.is_running(),
            "reason": "no_valid_stations"
        }

    started = ai_loop.start({
        "interval": interval,
        "station_ids": station_ids,
        "scenario": payload.get("scenario"),
        "seed": int(payload.get("seed", 42)),
    })

    socketio.emit("reports:ai_status", {"running": True})

    return {
        "ok": True,
        "running": True,
        "alreadyRunning": not started
    }

@socketio.on("reports:ai_stop")
def handle_ai_generation_stop(_data = None):
    """Stop the continuous AI generation."""
    ai_loop.stop()
    socketio.emit("reports:ai_status", {"running": False})
    return {"ok": True, "running": False}

@socketio.on("reports:ai_status_get")
def handle_ai_generation_status(_data = None):
    """Return whether the generator is running (used when a client reloads the page)."""
    return {"ok": True, "running": ai_loop.is_running()}

@socketio.on("reports:step")
def process_report_step(data=None):
    # Process exactly one report through the engine-owned lifecycle.
    return report_queue_runner.process_next()


@socketio.on("reports:start")
def start_report_processing(data=None):
    # Start the background loop; it stops automatically when the queue is empty.
    return report_queue_runner.start_continuous()


@socketio.on("reports:pause")
def pause_report_processing(data=None):
    # Pause processing without removing pending reports.
    return report_queue_runner.pause()


@socketio.on("reports:snapshot")
def report_queue_snapshot(data=None):
    # Read the queue under the same lock used by report processing.
    return report_queue_runner.snapshot()

if __name__ == "__main__":
    event_engine.start()
    socketio.run(app, debug = True, use_reloader=False)

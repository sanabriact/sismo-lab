from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
from backend.utils.json_utils import objectToDict
from backend.services.seismic_observatory_service import SeismicObservatoryService, ScenarioValidationError
from backend.services.realtime_service import init_realtime
from backend.services.event_engine import EventEngine
from backend.services.ai_client.event_generator_client import AIEventClient 
from backend.managers.stress_mode_manager import StressModeManager
from backend.managers.scenario_generator_manager import ScenarioGeneratorManager
from backend.managers.load_scenario_manager import LoadScenarioManager
from backend.services.socket.socket_broadcaster import SocketBroadcaster
from backend.services.ai_client.event_bus import mode_changed, scenario_loaded

app = Flask(__name__)
CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
init_realtime(socketio)
obs_service = SeismicObservatoryService()
event_engine = EventEngine(
    socketio=socketio,
    service=obs_service,
    mode_changed=mode_changed,
    stress_mode_manager=StressModeManager(),
)
socket_broadcaster = SocketBroadcaster(mode_changed, scenario_loaded)
ai_client = AIEventClient()
load_scenario_manager = LoadScenarioManager()

generator_manager = ScenarioGeneratorManager( ai_client=ai_client, engine=event_engine)

""" Rutas de FLASK (API rest) """
@app.route("/api/seismic-observatory", methods=["GET"])
def getSeismicObservatory():
    observatory = event_engine.get_observatory()
    if observatory is None:
        return jsonify(objectToDict(obs_service.getObservatory()))
    
    return jsonify(observatory.toDict())

@app.route("/api/events", methods=["POST"])
def createEvent():
    #data is the object that arrives here from the frontend
    data = request.json
    #VALIDATING FIELDS
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

    try:
        event_datetime = datetime.fromisoformat(data["datetime"])
        
    except ValueError:
        return jsonify({
            "success": False,
            "reason": "Invalid datetime format"
        }), 400
    #CREATING EVENT     
    response = obs_service.createEvent(
        data["id"],
        data["magnitude"],
        data["depth"],
        data["epicenter_x"],
        data["epicenter_y"],
        event_datetime,
        data["revision"],
        data["station"]
    )

    if not response["success"]:
        return jsonify(response), 400
    return jsonify(response), 201

""" @app.route("/api/scenario", methods=["POST"])
def load_scenario():
    data = request.get_json()
    Falta crear método loadScenario para obs_service (Lee, valida y construye un SeismicObservatory a partir de un JSON)
    observatory = obs_service.loadScenario(data)
    generator_manager.load_scenario(observatory)
    
    return jsonify({
        "message": "Escenario cargado correctamente",
        "stations": len(observatory.getStations())
    }), 200 """
    
# Method to load the JSON
@app.route("/api/scenario", methods=["GET"])
def load_scenario():
    data = request.get_json()
    result = load_scenario_manager.load(data)
    return jsonify(result)
    
@socketio.on("connect")
def handle_connect():
    print("Cliente conectado por WebSocket")

@socketio.on("disconnect")
def handle_disconnect():
    print("Cliente desconectado del WebSocket")

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
        "scenarioId": observatory.getScenarioId() if observatory is not None else None
    }

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
            observatory = obs_service.loadScenarioFromText(data.get("content"))
        else:
            # El frontend envía el modo en "aiMode" (o en "content").
            observatory = obs_service.loadScenarioFromAI(data.get("aiMode") or data.get("content"))

    except ScenarioValidationError as error:
        return {"ok": False, "reason": "invalid_scenario", "issues": error.issues}

    except Exception as error:
        print(f"Error cargando el escenario: {error}")
        return {"ok": False, "reason": "server_error"}

    # El escenario es válido: pasa a ser el escenario activo del motor.
    generator_manager.load_scenario(observatory)

    payload = {
        "scenarioId": observatory.scenario_id,
        "mode": observatory.getExecutionMode(),
        "stations": len(observatory.getStations()),
        "events": len(observatory.getAVLTree().index)
    }
    scenario_loaded.notify(payload)
    event_engine.announce_mode()

    print(f"Escenario cargado: {payload}")
    return {"ok": True, "scenario": payload}

if __name__ == "__main__":
    event_engine.start()
    socketio.run(app, debug = True, use_reloader=False)

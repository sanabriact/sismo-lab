from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
from backend.repositories.json_utils import objectToDict
from backend.services.seismic_observatory_service import SeismicObservatoryService
from backend.services.realtime_service import init_realtime
from backend.services.event_engine import EventEngine
from backend.services.ai_event_client import AIEventClient 
from backend.services.scenario_generator_manager import ScenarioGeneratorManager
from backend.services.load_scenario_manager import LoadScenarioManager

app = Flask(__name__)
CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
init_realtime(socketio)
obs_service = SeismicObservatoryService()
event_engine = EventEngine( socketio=socketio, repository=obs_service.repository)
ai_client = AIEventClient()
load_scenario_manager = LoadScenarioManager()

generator_manager = ScenarioGeneratorManager( ai_client=ai_client, engine=event_engine)


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
@app.route("/api/scenario", methods=["POST"])
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
    
if __name__ == "__main__":
    event_engine.start()
    socketio.run(app, debug = True, use_reloader=False)

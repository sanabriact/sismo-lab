from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
from backend.services.seismic_observatory_service import SeismicObservatoryService
from backend.services.realtime_service import init_realtime
from backend.services.event_engine import EventEngine
from backend.services.ai_event_client import AIEventClient 
from backend.services.scenario_generator_manager import ScenarioGeneratorManager

app = Flask(__name__)
CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
init_realtime(socketio)
obs_service = SeismicObservatoryService()
event_engine = EventEngine( socketio=socketio, repository=obs_service.repository)
ai_client = AIEventClient()

generator_manager = ScenarioGeneratorManager( ai_client=ai_client, engine=event_engine)

@app.route("/api/seismic-observatory", methods=["GET"])
def getSeismicObservatory():
    observatory = event_engine.get_observatory()
    if observatory is None:
        return jsonify(obs_service.getObservatory())
    
    return jsonify(observatory.toDict())

""" @app.route("/api/seismic-observatory", methods=["POST"])
def createSeismicObservatory() """

@app.route("/api/scenario", methods=["POST"])
def load_scenario():
    data = request.get_json()
    """ Falta crear método loadScenario para obs_service (Lee, valida y construye un SeismicObservatory a partir de un JSON)"""
    observatory = obs_service.loadScenario(data)
    generator_manager.load_scenario(observatory)
    
    return jsonify({
        "message": "Escenario cargado correctamente",
        "stations": len(observatory.getStations())
    }), 200

@socketio.on("connect")
def handle_connect():
    print("Cliente conectado por WebSocket")

@socketio.on("disconnect")
def handle_disconnect():
    print("Cliente desconectado del WebSocket")
    
if __name__ == "__main__":
    event_engine.start()
    socketio.run(app, debug = True, use_reloader=False)
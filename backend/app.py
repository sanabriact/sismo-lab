from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
from backend.services.seismic_observatory_service import SeismicObservatoryService
from backend.services.realtime_service import init_realtime

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
init_realtime(socketio)
obs_service = SeismicObservatoryService()

@app.route("/api/seismic-observatory", methods=["GET"])
def getSeismicObservatory():
    return jsonify(obs_service.getObservatory())

""" @app.route("/api/seismic-observatory", methods=["POST"])
def createSeismicObservatory() """

@socketio.on("connect")
def handle_connect():
    print("Cliente conectado por WebSocket")

if __name__ == "__main__":
    socketio.run(app, debug = True)
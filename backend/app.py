from datetime import datetime

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

@socketio.on("connect")
def handle_connect():
    print("Cliente conectado por WebSocket")

if __name__ == "__main__":
    socketio.run(app, debug = True)

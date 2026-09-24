from flask import Flask, jsonify, request
from flask_cors import CORS
from backend.services.seismic_observatory_service import SeismicObservatoryService
app = Flask(__name__)
CORS(app)
obs_service = SeismicObservatoryService()

@app.route("/api/seismic-observatory", methods=["GET"])
def getSeismicObservatory():
    return jsonify(obs_service.getObservatory())

""" @app.route("/api/seismic-observatory", methods=["POST"])
def createSeismicObservatory() """


if __name__ == "__main__":
    app.run(debug = True)
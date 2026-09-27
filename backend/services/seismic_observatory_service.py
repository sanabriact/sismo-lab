from uuid import uuid4
from backend.repositories.seismic_observatory_repository import SeismicObservatoryRepository
from backend.models.seismic_observatory import SeismicObservatory

class SeismicObservatoryService:
    def __init__(self):
        self.repository = SeismicObservatoryRepository()

    def getObservatory(self):
        observatory = self.repository.load()
        if observatory is None:
            observatory = SeismicObservatory()
        return observatory

    def load_scenario(self, data):
        if not isinstance(data, dict):
            raise ValueError("El escenario debe ser un JSON")

        # Permite recibir el escenario directo o dentro de la clave
        # seismic_observatory.
        if "seismic_observatory" in data:
            data = data["seismic_observatory"]

        if "stations" not in data:
            raise ValueError("El escenario no tiene estaciones")

        if len(data["stations"]) == 0:
            raise ValueError("El escenario debe tener al menos una estación")

        if "execution_mode" not in data:
            data["execution_mode"] = "normal"

        if data["execution_mode"] != "normal" and data["execution_mode"] != "stress":
            raise ValueError("El modo debe ser normal o stress")

        observatory = SeismicObservatory.fromDict(data)

        if "scenario_id" in data:
            observatory.scenario_id = data["scenario_id"]
        else:
            observatory.scenario_id = str(uuid4())

        self.repository.save(observatory)

        return observatory

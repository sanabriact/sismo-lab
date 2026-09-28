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

    def createEvent(self, id, magnitude, depth, epicenter_x, epicenter_y, datetime: datetime, revision, station):
        # load the observatory
        obs = self.getObservatory()
        try:
            # try of create the event
            event = obs.createEvent(
                id, magnitude, depth, epicenter_x, epicenter_y, datetime, revision, station)
        except ValueError as error:
            # if we have an error return an object with false and the reason
            return {
                "success": False,
                "reason": str(error)
            }

        if not event:
            # if createEvent() return False the id already exists
            return {
                "success": False,
                "reason": "The id belongs to another event created, archived or deleted"
            }
        # Saving the observatory
        self.repository.save(obs)
        event_ = obs.searchEventById(id)
        return {
            "success": True,
            "event": event_.toDict()
        }

    def searchEventById(self, id):
        obs = self.getObservatory()
        event = obs.searchEventById(id)
        if event is None:
            return {
                "success": False,
                "reason": "The event doesn't exist"
            }

        return {
            "success": True,
            "event": event.toDict()
        }

    def deleteEventById(self, id):
        obs = self.getObservatory()
        event = obs.searchEventById(id)
        if event is None:
            return {
                "success": False,
                "reason": "The event doesn't exist"
            }
        deleted = obs.deleteEventById(id)
        if not deleted:
            return {
                "success": False,
                "reason": "An error has occurred."
            }

        self.repository.save(obs)
        return {
                "success": True,
                "event": event.toDict()
            }

    def markAsRevised(self, id):
        obs = self.getObservatory()
        event = obs.searchEventById(id)
        if event is None:
            return {
                "success": False,
                "reason": "The event doesn't exist"
            }
        event.setAttentionStatus("revised")
        self.repository.save(obs)
        return {
            "success": True,
            "event": event.toDict()
        }
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

from datetime import datetime

from backend.models.seismic_observatory import SeismicObservatory
from backend.repositories.seismic_observatory_repository import SeismicObservatoryRepository


class SeismicObservatoryService():
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

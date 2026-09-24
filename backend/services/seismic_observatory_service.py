from backend.repositories.seismic_observatory_repository import SeismicObservatoryRepository
class SeismicObservatoryService():
    def __init__(self):
        self.repository = SeismicObservatoryRepository()

    def getObservatory(self):
        return self.repository.getAll()

    def postObservatory(self, data):
        return self.repository.post(data)
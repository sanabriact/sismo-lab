from backend.repositories.json_repository import JSONRepository
from backend.models.seismic_observatory import SeismicObservatory

class SeismicObservatoryRepository(JSONRepository):

    # Initialize the repository with the name of its JSON file
    def __init__(self):
        super().__init__("seismic_observatory.json")

    # -------------------------------------------------------------------------
    # Saving and loading the observatory
    # -------------------------------------------------------------------------

    # Save the observatory to the JSON file
    def save(self, observatory):
        data = observatory.toDict()
        return self._write(data)

    # Load the observatory from the JSON file, or return None if there is no data
    def load(self):
        data = self._read()
        if not data:
            return None
        observatory = SeismicObservatory.fromDict(data)
        return observatory
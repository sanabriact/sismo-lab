from backend.models.association_manager import AssociationManager
from backend.models.clock import SimulationClock
from backend.models.history import History
from backend.models.metrics import Metrics
from backend.models.station import Station
from backend.models.zone import Zone
from backend.repositories.json_repository import JSONRepository
from backend.models.seismic_observatory import SeismicObservatory
from backend.structures.avl import AVL
from backend.structures.bst import BST
from backend.structures.queue import Queue
from backend.structures.stack import Stack

class SeismicObservatoryRepository(JSONRepository):
    def __init__(self):
        super().__init__("seismic_observatory.json")

    def save(self, observatory):
        data = observatory.toDict()
        return self._write(data)

    def load(self):
        data = self._read()
        if not data:
            return None
        observatory = SeismicObservatory.fromDict(data)
        return observatory
        
        
    def getAll(self):
        return self._read()

    def post(self, object):
        data = self._read()
        observatory = data.setdefault("seismic_observatory",{})

        return self._write(data)

    
    #def get by id 
    #def post para cada clase
    #def delete para cada clase
    #def put para cada clase
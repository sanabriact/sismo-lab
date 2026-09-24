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
    """
    Responsible only for translating between the SeismicObservatory
    domain object and its JSON representation on disk.
 
    It does not know about business rules (creating an event, processing
    a report, etc.). That belongs to SeismicObservatory (the domain) and
    to SeismicObservatoryService (the use-case orchestration layer).
    """

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
        

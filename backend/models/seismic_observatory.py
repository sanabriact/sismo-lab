from datetime import datetime, timezone
from backend.structures.avl import AVL
from backend.structures.bst import BST
from backend.structures.queue import Queue
from backend.structures.stack import Stack
from backend.models.history import History
from backend.models.clock import SimulationClock
from backend.models.association_manager import AssociationManager
from backend.models.metrics import Metrics
from backend.models.event import Event

class SeismicObservatory:
    def __init__(self):
        # ===================== estructuras centrales =====================
        self.avl_tree = AVL()
        self.bst_tree = BST()

        # ===================== datos fijos del escenario =====================
        self.stations = []          
        self.zones = []             
        # ===================== historial y control =====================
        self.history = History()
        self.report_queue = Queue()
        self.action_stack = Stack()
        self.clock = SimulationClock(datetime.now(timezone.utc))

        # ===================== parámetros configurables =====================
        self.w = 48.0     
        self.r = 40.0     
        self.l = 3       
        self.t = 72.0     

        # ===================== servicios de negocio =====================
        self.association_manager = AssociationManager()
        self.metrics = Metrics()

        # ===================== versiones y modo de ejecución =====================
        self.saved_versions = []          
        self.execution_mode = "normal"  

    def getAVLTree(self):
        return self.avl_tree
    def getBSTTree(self):
        return self.bst_tree
    def getStations(self):
        return self.stations
    def getZones(self):
        return self.zones
    def getHistory(self):
        return self.history 
    def getReportQueue(self):
        return self.report_queue
    def getActionStack(self):
        return self.action_stack
    def getClock(self):
        return self.clock
    def getW(self):
        return self.w
    def setW(self, w):
        self.w = w
    def getR(self):
        return self.r
    def setR(self, r):
        self.r = r
    def getL(self):
        return self.l
    def setL(self, l):
        self.l = l
    def getT(self):
        return self.t
    def setT(self, t):
        self.t = t
    def getAssociationManager(self):
        return self.association_manager
    def getMetrics(self):
        return self.metrics
    def getSavedVersions(self):
        return self.saved_versions
    def getExecutionMode(self):
        return self.execution_mode

    def createEvent(self, id, magnitude, depth, epicenter_x, epicenter_y, datetime: datetime, revision, station):
        if self.avl_tree.searchById(id) is not None:
            return False
        #Validar que no este en historico
        if id in self.history.getArchived():
            return False
        if id in self.history.getDeletedIds():
            return False
        event = Event(id, magnitude, depth, epicenter_x, epicenter_y, datetime, revision, station, self.zones)
        self.avl_tree.insert(event)
        return True

    def searchEventById(self, id):
        node = self.avl_tree.searchById(id)
        if node is not None:
            return node.getValue()
        return None

    def deleteEventById(self, id):
        node = self.avl_tree.searchById(id)
        if node is not None: 
            return self.avl_tree.delete(id)
        return False

    #def markAsReviewed()
    
    #def archiveSubTree() lo hace el viejo


from datetime import datetime, timezone
from backend.structures.avl import AVL
from backend.structures.bst import BST
from backend.structures.queue import Queue
from backend.structures.stack import Stack
from history import History
from clock import SimulationClock
from association_manager import AssociationManager
from metrics import Metrics

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
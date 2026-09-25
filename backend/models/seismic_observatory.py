from datetime import datetime, timezone
from backend.models.zone import Zone
from backend.structures.avl import AVL
from backend.structures.bst import BST
from backend.structures.queue import Queue
from backend.structures.stack import Stack
from backend.models.history import History
from backend.models.clock import SimulationClock
from backend.models.association_manager import AssociationManager
from backend.models.metrics import Metrics
from backend.models.event import Event
from backend.models.station import Station
from backend.repositories.json_utils import objectToDict

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
    def setAVLTree(self, avl):
        self.avl_tree = avl
    def getBSTTree(self):
        return self.bst_tree
    def setBSTTree(self, bst):
        self.bst_tree = bst
    def getStations(self):
        return self.stations
    def setStations(self,stations):
        self.stations = stations
    def addStation(self,station):
        self.stations.append(station)
    def deleteStation(self,station):
        if station in self.stations:
            self.stations.remove(station)
            return True
        return False
    def getZones(self):
        return self.zones
    def setZones(self, zones):
        self.zones = zones
    def addZone(self,zone):
        self.zones.append(zone)
    def deleteZone(self,zone):
        if zone in self.zones:
            self.zones.remove(zone)
            return True
        return False
    def getHistory(self):
        return self.history 
    def setHistory(self, history):
        self.history = history
    def getReportQueue(self):
        return self.report_queue
    def setReportQueue(self,queue):
        self.report_queue = queue
    def getActionStack(self):
        return self.action_stack
    def setActionStack(self,stack):
        self.action_stack = stack
    def getClock(self):
        return self.clock
    def setClock(self,clock):
        self.clock = clock
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
    def setAssociationManager(self,manager):
        self.association_manager = manager
    def getMetrics(self):
        return self.metrics
    def setMetrics(self,metrics):
        self.metrics = metrics
    def getSavedVersions(self):
        return self.saved_versions
    def setSavedVersions(self,versions):
        self.saved_versions = versions
    def getExecutionMode(self):
        return self.execution_mode
    def setExecutionMode(self, mode):
        self.execution_mode = mode

    def createEvent(self, id, magnitude, depth, epicenter_x, epicenter_y, datetime: datetime, revision, station):
        if self.avl_tree.searchById(id) is not None and self.bst_tree.searchById(id) is not None:
            return False
        #Validar que no este en historico
        if id in self.history.getArchived():
            return False
        if id in self.history.getDeletedIds():
            return False
        event = Event(id, magnitude, depth, epicenter_x, epicenter_y, datetime, revision, station, self.zones)
        return self.avl_tree.insert(event), self.bst_tree.insert(event)
        

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

    def editEvent(self,report):
        #Al crearse un reporte, sus datos ya están validados
        event = self.searchEventById(report.getEventId())
        if event is not None:
            oldKey = event.getKey()
            event.updateEventData(report)
            if event.getKey() != oldKey:
                self.deleteEventById(report.getEventId())
                self.avl_tree.insert(event)
                #RECALCULAR ASOCIACIONES Y METRICAS

                return True
        return False


    #def markAsReviewed()
    
    #def archiveSubTree() lo hace el viejo

    def enqueueReport(self, report):
        self.report_queue.enqueue(report)

    def toVersion(self):
        return {
                    "avl_tree": objectToDict(self.avl_tree),
                    "bst_tree":objectToDict(self.bst_tree),
                    "history": objectToDict(self.history),
                    "clock":objectToDict(self.clock),
                    "l":self.l,
                    "t":self.t,
                    "association_manager":objectToDict(self.association_manager),
                    "metrics": objectToDict(self.metrics),
                    "execution_mode":self.execution_mode
                }

    def toDict(self):
        return {
            "avl_tree": objectToDict(self.avl_tree),
            "bst_tree":objectToDict(self.bst_tree),
            "stations":[objectToDict(station) for station in self.stations],
            "zones":[objectToDict(zone) for zone in self.zones],
            "history": objectToDict(self.history),
            "report_queue": objectToDict(self.report_queue),
            "action_stack": objectToDict(self.action_stack),
            "clock":objectToDict(self.clock),
            "l":self.l,
            "t":self.t,
            "association_manager":objectToDict(self.association_manager),
            "metrics": objectToDict(self.metrics),
            "saved_versions":[objectToDict(version) for version in self.saved_versions],
            "execution_mode":self.execution_mode
        }

    @classmethod
    def fromDict(cls,data):
        observatory = cls()
        observatory.avl_tree = AVL.fromDict(data["avl_tree"])
        observatory.bst_tree = BST.fromDict(data["bst_tree"])
        observatory.stations = [Station.fromDict(station) for station in data["stations"]]
        observatory.zones = [Zone.fromDict(zone) for zone in data["zones"]]
        observatory.history = History.fromDict(data["history"])
        observatory.report_queue = Queue.fromDict(data["report_queue"])
        observatory.action_stack = Stack.fromDict(data["action_stack"])
        observatory.clock = SimulationClock.fromDict(data["clock"])
        observatory.l = data["l"]
        observatory.t = data["t"]
        observatory.association_manager = AssociationManager.fromDict(data["association_manager"])
        observatory.metrics = Metrics.fromDict(data["metrics"])
        observatory.saved_versions = data["saved_versions"]
        return observatory



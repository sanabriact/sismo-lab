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
from backend.persistence.json_utils import objectToDict

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
    def getBSTTree(self):
        return self.bst_tree
    def getStations(self):
        return self.stations
    def addStation(self,station):
        self.stations.append(station)
    def deleteStation(self,station):
        if station in self.stations:
            self.stations.remove(station)
            return True
        return False
    def getZones(self):
        return self.zones
    def addZone(self,zone):
        self.zones.append(zone)
    def deleteZone(self,zone):
        if zone in self.zones:
            self.zones.remove(zone)
            return True
        return False
    def getHistory(self):
        return self.history 
    def getReportQueue(self):
        return self.report_queue
    def getActionStack(self):
        return self.action_stack
    def getClock(self):
        return self.clock
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
        return self.avl_tree.insert(event)
        

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


    def toDict(self):
        return {
            "avl_tree": objectToDict(self.avl_tree),
            "bst":objectToDict(self.bst_tree),
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
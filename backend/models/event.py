from datetime import datetime

class Event:

    def __init__(self, id, magnitude, depth, epicenter_x, epicenter_y, datetime: datetime, revision, station, zones = None):
        self._validate_data(id, magnitude, depth, epicenter_x, epicenter_y, datetime)
        self.depth = round(depth, 1)  # float
        self.epicenter_x = round(epicenter_x, 1)  # float
        self.epicenter_y = round(epicenter_y)  # float
        self.populated_zone = self.calculatePopulatedZone(zones or [])  # bool
        priority = self.calculatePriority(magnitude)
        self.datetime = datetime  # datetime
        self.revision = revision  # int
        self.reporting_stations = {station}  # station
        self.attention_status = "pending"  # str
        self.event_status = "active"  # str
        self.expensive_access = False  # bool
        self.key = (priority, round(magnitude, 1), id)  # tupla

    def getKey(self):
        return self.key
    def setKey(self,key):
        self.key = key

    def getDepth(self):
        return self.depth
    def setDepth(self, depth):
        self.depth = depth

    def getEpicenterX(self):
        return self.epicenter_x
    def setEpicenterX(self,x):
        self.epicenter_x = x

    def getEpicenterY(self):
        return self.epicenter_y
    def setEpicenterY(self,y):
        self.epicenter_y = y

    def getDateTime(self):
        return self.datetime
    def setDateTime(self, date):
        self.datetime = date
    
    def getCurrentRevision(self):
        return self.current_revision
    def setCurrentRevision(self, revision):
        self.current_revision = revision

    def getReportingStations(self):
        return self.reporting_stations
    def addReportingStation(self, station):
        self.reporting_stations.add(station)
        
    def getAttentionStatus(self):
        return self.attention_status
    def setAttentionStatus(self,status):
        self.attention_status = status

    def getEventStatus(self):
        return self.event_status
    def setEventStatus(self,status):
        self.event_status = status

    def getPopulatedZone(self):
        return self.populated_zone
    def setPopilatedZone(self,populated):
        self.populated_zone = populated

    def getExpensiveAccess(self):
        return self.expensive_access
    def setExpensiveAccess(self,expensive):
        self.expensive_access = expensive

    #Calculate Priority
    def calculatePriority(self, magnitude):
        priority = None
        if magnitude >=6 or (magnitude >= 4.5 and self.depth <= 30 and self.populated_zone == True):
            priority = 3
        elif magnitude >= 4.5:
            priority = 2
        else:
            priority = 1
        return priority

    def calculatePopulatedZone(self, zones):
        belongs_to_any_zone = False
        belongs_to_populated_zone = False
        for zone in zones:
            if zone.contains(self.epicenter_x, self.epicenter_y):
                belongs_to_any_zone = True
                if zone.getIsPopulated():
                    belongs_to_populated_zone = True
                    break 
        return belongs_to_populated_zone if belongs_to_any_zone else False

    
    def updateEventData(self, report, zones = None):
        self._validate_data(report.getEventId(), report.getMagnitude(), report.getDepth(), report.getEpicenterX(), report.getEpicenterY(), report.getDatetime())
        self.revision+=1
        self.depth = round(report.getDepth(), 1)
        self.epicenter_x = round(report.getEpicenterX(), 1)
        self.epicenter_y = round(report.getEpicenterY(), 1)
        self.datetime = report.getDatetime()
        self.populated_zone = self.calculatePopulatedZone(zones or [])
        self.key = (self.calculatePriority(report.getMagnitude()), round(report.getMagnitude(), 1), self.key[2])


    def _validate_data(self,id, magnitude, depth, epicenter_x, epicenter_y, date):
        if not (-2 <= magnitude <= 10):
            raise ValueError("magnitud debe estar entre -2 y 10")
        if not isinstance(id, int) or not (1 <= id <= 999999):
            raise ValueError("Id debe estar entre 1 y 999999")
        if not (0 <= depth <= 700):
            raise ValueError("Profundidad debe estar entre 0 y 700")
        if not (0 <= epicenter_x <= 1000) and not (0 <= epicenter_y <= 1000):
            raise ValueError("Epicentro debe estar entre 0 y 1000")
        if not isinstance(date, datetime):
            raise TypeError("La fecha debe ser de tipo datetime")

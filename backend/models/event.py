from datetime import datetime
from backend.utils.quantities import normalizeDatetime, parseDatetime


class Event:

    # Initialize the event from the first report received
    def __init__(self, id, magnitude, depth, epicenter_x, epicenter_y, datetime: datetime, revision, station, zones = None):
        self._validate_data(id, magnitude, depth, epicenter_x, epicenter_y, datetime)
        self.depth = round(depth, 1)  # float
        self.epicenter_x = round(epicenter_x, 1)  # float
        self.epicenter_y = round(epicenter_y, 1)  # float
        self.populated_zone = self.calculatePopulatedZone(zones or [])  # bool
        priority = self.calculatePriority(magnitude)
        self.datetime = normalizeDatetime(datetime)  # datetime
        self.revision = revision  # int
        self.reporting_stations = {station}  # station id
        self.attention_status = "pending"  # str pending or revised
        self.event_status = "active"  # str active, archived, deleted
        self.expensive_access = False  # bool
        self.key = (priority, round(magnitude, 1), id)  # tuple

    # -------------------------------------------------------------------------
    # Validates the data used to create or update an event
    # -------------------------------------------------------------------------

    # Validate the ranges and types of the event data
    def _validate_data(self, id, magnitude, depth, epicenter_x, epicenter_y, date):
        if not (-2 <= magnitude <= 10):
            raise ValueError("magnitud debe estar entre -2 y 10")
        if not isinstance(id, int) or not (1 <= id <= 999999):
            raise ValueError("Id debe estar entre 1 y 999999")
        if not (0 <= depth <= 700):
            raise ValueError("Profundidad debe estar entre 0 y 700")
        if not (0 <= epicenter_x <= 1000) or not (0 <= epicenter_y <= 1000):
            raise ValueError("Epicentro debe estar entre 0 y 1000")
        if not isinstance(date, datetime):
            raise TypeError("La fecha debe ser de tipo datetime")

    # ------------------------------------------------------------------
    # Reading and writing the event attributes
    # ------------------------------------------------------------------

    # Get the sorting key (priority, magnitude, id)
    def getKey(self):
        return self.key

    # Set the sorting key
    def setKey(self, key):
        self.key = key

    # ------------------------------------------------------------------

    # Get the depth of the event
    def getDepth(self):
        return self.depth

    # Set the depth of the event
    def setDepth(self, depth):
        self.depth = depth

    # ------------------------------------------------------------------

    # Get the x coordinate of the epicenter
    def getEpicenterX(self):
        return self.epicenter_x

    # Set the x coordinate of the epicenter
    def setEpicenterX(self, x):
        self.epicenter_x = x

    # Get the y coordinate of the epicenter
    def getEpicenterY(self):
        return self.epicenter_y

    # Set the y coordinate of the epicenter
    def setEpicenterY(self, y):
        self.epicenter_y = y

    # ------------------------------------------------------------------

    # Get the instant when the event occurred
    def getDateTime(self):
        return self.datetime

    # Set the instant when the event occurred
    def setDateTime(self, date):
        self.datetime = date

    # ------------------------------------------------------------------

    # Get the current revision number
    def getCurrentRevision(self):
        return self.revision

    # Set the current revision number
    def setCurrentRevision(self, revision):
        self.revision = revision

    # ------------------------------------------------------------------

    # Get the set of stations that reported the event
    def getReportingStations(self):
        return self.reporting_stations

    # Add a station to the set of reporting stations
    def addReportingStation(self, station):
        self.reporting_stations.add(station)

    # ------------------------------------------------------------------

    # Get the attention status (pending or revised)
    def getAttentionStatus(self):
        return self.attention_status

    # Set the attention status (pending or revised)
    def setAttentionStatus(self, status):
        self.attention_status = status

    # Get the event status (active, archived or deleted)
    def getEventStatus(self):
        return self.event_status

    # Set the event status (active, archived or deleted)
    def setEventStatus(self, status):
        self.event_status = status

    # ------------------------------------------------------------------

    # Get whether the epicenter is in a populated zone
    def getPopulatedZone(self):
        return self.populated_zone

    # Set whether the epicenter is in a populated zone
    def setPopilatedZone(self, populated):
        self.populated_zone = populated

    # Get whether the access to the event is expensive
    def getExpensiveAccess(self):
        return self.expensive_access

    # Set whether the access to the event is expensive
    def setExpensiveAccess(self, expensive):
        self.expensive_access = expensive

    # ------------------------------------------------------------------
    # Calculations derived from the event data
    # ------------------------------------------------------------------

    # Calculate the priority (1 to 3) from the magnitude, depth and zone
    def calculatePriority(self, magnitude):
        priority = None
        if magnitude >= 6 or (magnitude >= 4.5 and self.depth <= 30 and self.populated_zone == True):
            priority = 3
        elif magnitude >= 4.5:
            priority = 2
        else:
            priority = 1
        return priority

    # Check if the epicenter belongs to a populated zone
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

    # ------------------------------------------------------------------
    # Updating the event (the user action)
    # ------------------------------------------------------------------

    # Update the event with a new report and recalculate its derived data
    def updateEventData(self, report, zones = None):
        self._validate_data(report.getEventId(), report.getMagnitude(), report.getDepth(), report.getEpicenterX(), report.getEpicenterY(), report.getDatetime())
        # The revision comes from the report, it is NOT incremented locally
        self.revision = report.getRevision()
        self.depth = round(report.getDepth(), 1)
        self.epicenter_x = round(report.getEpicenterX(), 1)
        self.epicenter_y = round(report.getEpicenterY(), 1)
        self.datetime = normalizeDatetime(report.getDatetime())
        self.populated_zone = self.calculatePopulatedZone(zones or [])
        self.key = (self.calculatePriority(report.getMagnitude()), round(report.getMagnitude(), 1), self.key[2])
        self.attention_status = "pending"
        self.addReportingStation(report.getStation().getId())

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    # Convert object to dictionary
    def toDict(self):
        return {
            "key": self.key,
            "depth": self.depth,
            "epicenter_x": self.epicenter_x,
            "epicenter_y": self.epicenter_y,
            "datetime": self.datetime.isoformat(),
            "revision": self.revision,
            "reporting_stations": [station for station in self.reporting_stations],
            "attention_status": self.attention_status,
            "event_status": self.event_status,
            "populated_zone": self.populated_zone,
            "expensive_access": self.expensive_access
        }

    # Convert dictionary to object
    @classmethod
    def fromDict(cls, data):
        event = cls.__new__(cls)
        event.key = tuple(data["key"])
        event.depth = data["depth"]
        event.epicenter_x = data["epicenter_x"]
        event.epicenter_y = data["epicenter_y"]
        event.datetime = parseDatetime(data["datetime"])
        event.revision = data["revision"]
        event.reporting_stations = set(data["reporting_stations"])
        event.attention_status = data["attention_status"]
        event.event_status = data["event_status"]
        event.populated_zone = data["populated_zone"]
        event.expensive_access = data["expensive_access"]
        return event
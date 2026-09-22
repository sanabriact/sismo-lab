from datetime import datetime


class Report:
    def __init__(self, event_id, revision, station,magnitude, depth, epicenter_x, epicenter_y, datetime_: datetime):

        self._validateData(event_id, revision, magnitude, depth,epicenter_x, epicenter_y, datetime_, station)

        self.event_id = event_id
        self.revision = revision
        self.station = station
        self.magnitude = round(magnitude, 1)
        self.depth = round(depth, 1)
        self.epicenter_x = round(epicenter_x, 1)
        self.epicenter_y = round(epicenter_y, 1)
        self.datetime = datetime_

    def getEventId(self):
        return self.event_id
    def setEventId(self, id):
        self.event_id = id

    def getRevision(self):
        return self.revision
    def setRevision(self, number):
        self.revision = number

    def getStation(self):
        return self.station
    def setStation(self, station):
        self.station = station

    def getMagnitude(self):
        return self.magnitude
    def setMagnitude(self, magnitude):
        self.magnitude = magnitude

    def getDepth(self):
        return self.depth
    def setDepth(self, depth):
        self.depth = depth

    def getEpicenterX(self):
        return self.epicenter_x
    def setEpicenterX(self, x):
        self.epicenter_x = x

    def getEpicenterY(self):
        return self.epicenter_y
    def serEpicenterY(self, y):
        self.epicenter_y = y

    def getDatetime(self):
        return self.datetime
    def setDatetime(self, date):
        self.datetime = date

    def _validateData(self, event_id, revision, magnitude, depth,epicenter_x, epicenter_y, datetime, station):

        if not isinstance(event_id, int) or not (1 <= event_id <= 999999):
            raise ValueError("event_id must be an integer between 1 and 999999")

        if not isinstance(revision, int) or revision <= 0:
            raise ValueError("revision must be a positive integer")

        if not (-2.0 <= magnitude <= 10.0):
            raise ValueError("magnitude must be between -2.0 and 10.0")

        if not (0.0 <= depth <= 700.0):
            raise ValueError("depth must be between 0.0 and 700.0 km")

        if not (0.0 <= epicenter_x <= 1000.0) or not (0.0 <= epicenter_y <= 1000.0):
            raise ValueError("epicenter must be within the 0 to 1000 km plane")

        if not isinstance(datetime, datetime):
            raise TypeError("occurrenceDateTime must be a datetime object, not a string")

        if not station or not isinstance(station, str):
            raise ValueError("issuingStation code must be provided")
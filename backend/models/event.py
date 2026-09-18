from datetime import datetime


class Event:

    def __init__(self, key, depth, epicenter_x, epicenter_y, datetime: datetime, current_revision, reporting_station):
        self._validate_data(key, depth, epicenter_x, epicenter_y, datetime)
        self.key = (key[0], round(key[1], 1), key[2])  # tupla
        self.depth = round(depth, 1)  # float
        self.epicenter_x = round(epicenter_x, 1)  # float
        self.epicenter_y = round(epicenter_y)  # float
        self.datetime = datetime  # datetime
        self.current_revision = current_revision  # int
        self.reporting_stations = {reporting_station}  # station
        self.attention_satus = "pending"  # str
        self.event_status = "active"  # str
        self.populated_zone = False  # bool
        self.expensive_access = False  # bool


def _validate_data(self, key, depth, epicenter_x, epicenter_y, date):
    priority = key[0]
    magnitude = key[1]
    id = key[2]
    if not isinstance(priority, int) or not (1 <= priority <= 3):
        raise ValueError("prioridad debe estar entre 1 y 3")
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

from datetime import datetime
from backend.utils.json_utils import objectToDict
from backend.utils.quantities import normalizeDatetime, parseDatetime

class Action:
    def __init__(self, acction_type, datetime:datetime, before_snapshot):
        self.action_type = acction_type
        self.datetime = normalizeDatetime(datetime)
        self.before_snapshot = before_snapshot

    def getActionType(self):
        return self.action_type
    def setActionType(self, type):
        self.action_type = type

    def getDateTime(self):
        return self.datetime
    def setDateTime(self, date):
        self.datetime = normalizeDatetime(date)

    def getBeforeSnapshot(self):
        return self.before_snapshot
    def setBeforeSnapshot(self, snapshot):
        self.before_snapshot = snapshot

    def toDict(self):
        return {
            "action_type": self.action_type,
            "datetime": self.datetime.isoformat(),
            "before_snapshot": self.before_snapshot   # already a plain dict
        }

    @classmethod
    def fromDict(cls, data):
        action = cls.__new__(cls)
        action.action_type = data["action_type"]
        action.datetime = parseDatetime(data["datetime"])
        action.before_snapshot = data["before_snapshot"]
        return action

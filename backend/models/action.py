from datetime import datetime
from backend.persistence.json_utils import objectToDict

class Action:
    def __init__(self, acction_type, datetime:datetime, before_snapshot):
        self.action_type = acction_type
        self.datetime = datetime
        self.before_snapshot = before_snapshot

    def getActionType(self):
        return self.action_type
    def setActionType(self, type):
        self.action_type = type

    def getDateTime(self):
        return self.datetime
    def setDateTime(self, date):
        self.datetime = date

    def getBeforeSnapshot(self):
        return self.before_snapshot
    def setBeforeSnapshot(self, snapshot):
        self.before_snapshot = snapshot

    def toDict(self):
        return {
            "action_type": self.action_type,
            "datetime": self.datetime.isoformat(),
            "before_snapshot": objectToDict(self.before_snapshot)
        }
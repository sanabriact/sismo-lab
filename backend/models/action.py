from datetime import datetime

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
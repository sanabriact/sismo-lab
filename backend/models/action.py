from datetime import datetime

class Action:
    def __init__(self, acction_type, datetime:datetime, before_snapshot):
        self.acction_type = acction_type
        self.datetime = datetime
        self.before_snapshot = before_snapshot
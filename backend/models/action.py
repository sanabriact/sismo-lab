from datetime import datetime
from backend.utils.json_utils import objectToDict
from backend.utils.quantities import normalizeDatetime, parseDatetime

class Action:
    def __init__(self,action_type,datetime_value,before_snapshot,metadata=None,):
        self.action_type = action_type
        self.datetime = normalizeDatetime(datetime_value)
        self.before_snapshot = before_snapshot

        if metadata is None:
            self.metadata = {}
        else:
            self.metadata = metadata

    def getActionType(self):
        return self.action_type

    def setActionType(self, action_type):
        self.action_type = action_type

    def getDateTime(self):
        return self.datetime
    def setDateTime(self, date):
        self.datetime = normalizeDatetime(date)

    def getBeforeSnapshot(self):
        return self.before_snapshot

    def setBeforeSnapshot(self, snapshot):
        self.before_snapshot = snapshot

    def getMetadata(self):
        return self.metadata

    def setMetadata(self, metadata):
        if metadata is None:
            self.metadata = {}
            return

        self.metadata = metadata

    def toDict(self):
        return {
            "action_type": self.action_type,
            "datetime": self.datetime.isoformat(),
            "before_snapshot": self.before_snapshot,
            "metadata": self.metadata,
        }

    @classmethod
    def fromDict(cls, data):
        action_type = data["action_type"]
        datetime_value = parseDatetime(data["datetime"])
        before_snapshot = data["before_snapshot"]
        metadata = data.get("metadata", {})

        return cls(
            action_type=action_type,
            datetime_value=datetime_value,
            before_snapshot=before_snapshot,
            metadata=metadata,
        )

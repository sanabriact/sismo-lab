from backend.utils.json_utils import objectToDict
from backend.utils.quantities import normalizeDatetime, parseDatetime

class Action:
    def __init__(
        self,
        action_type,
        datetime_value,
        before_snapshot=None,
        metadata=None,
        inverse_action=None,
        undo_data=None,
    ):
        self.action_type = action_type
        self.datetime = normalizeDatetime(datetime_value)
        # Kept only for backwards compatibility with old persisted actions.
        # New actions use the compact inverse data below.
        self.before_snapshot = before_snapshot
        self.inverse_action = inverse_action
        self.undo_data = undo_data

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

    def getInverseAction(self):
        return self.inverse_action

    def setInverseAction(self, inverse_action):
        self.inverse_action = inverse_action

    def getUndoData(self):
        return self.undo_data

    def setUndoData(self, undo_data):
        self.undo_data = undo_data

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
            "inverse_action": self.inverse_action,
            "undo_data": self.undo_data,
            "metadata": self.metadata,
        }

    @classmethod
    def fromDict(cls, data):
        action_type = data["action_type"]
        datetime_value = parseDatetime(data["datetime"])
        before_snapshot = data.get("before_snapshot")
        metadata = data.get("metadata", {})

        return cls(
            action_type=action_type,
            datetime_value=datetime_value,
            before_snapshot=before_snapshot,
            metadata=metadata,
            inverse_action=data.get("inverse_action"),
            undo_data=data.get("undo_data"),
        )

from backend.utils.quantities import normalizeDatetime, parseDatetime


class Action:

    # Initialize the action with its type, instant and undo information
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

    # -------------------------------------------------------------------------
    # Reading and writing the action attributes
    # -------------------------------------------------------------------------

    # Get the type of the action
    def getActionType(self):
        return self.action_type

    # Set the type of the action
    def setActionType(self, action_type):
        self.action_type = action_type

    # ------------------------------------------------------------------

    # Get the instant when the action happened
    def getDateTime(self):
        return self.datetime

    # Set the instant when the action happened
    def setDateTime(self, date):
        self.datetime = normalizeDatetime(date)

    # ------------------------------------------------------------------

    # Get the snapshot taken before the action (legacy)
    def getBeforeSnapshot(self):
        return self.before_snapshot

    # Set the snapshot taken before the action (legacy)
    def setBeforeSnapshot(self, snapshot):
        self.before_snapshot = snapshot

    # ------------------------------------------------------------------

    # Get the action that reverts this one
    def getInverseAction(self):
        return self.inverse_action

    # Set the action that reverts this one
    def setInverseAction(self, inverse_action):
        self.inverse_action = inverse_action

    # Get the data needed to undo the action
    def getUndoData(self):
        return self.undo_data

    # Set the data needed to undo the action
    def setUndoData(self, undo_data):
        self.undo_data = undo_data

    # ------------------------------------------------------------------

    # Get the extra information of the action
    def getMetadata(self):
        return self.metadata

    # Set the extra information of the action, an empty one if None
    def setMetadata(self, metadata):
        if metadata is None:
            self.metadata = {}
            return

        self.metadata = metadata

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    # Convert object to dictionary
    def toDict(self):
        return {
            "action_type": self.action_type,
            "datetime": self.datetime.isoformat(),
            "before_snapshot": self.before_snapshot,
            "inverse_action": self.inverse_action,
            "undo_data": self.undo_data,
            "metadata": self.metadata,
        }

    # Convert dictionary to object
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

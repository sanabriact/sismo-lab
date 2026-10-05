from copy import deepcopy
from backend.models.action import Action
from backend.models.seismic_observatory import SeismicObservatory


# Raised when an action cannot be inspected or restored
class ActionStackError(Exception):
    pass


class ActionStackService:

    # Public action types accepted by the stack
    ACTION_TYPES = {
        "CREATE_EVENT",
        "UPDATE_EVENT",
        "DELETE_EVENT",
        "ARCHIVE_BRANCH",
        "MARK_REVIEWED",
        "ADVANCE_CLOCK",
        "CHANGE_PARAMETER",
        "LOAD_SCENARIO",
        "PROCESS_REPORT",
        "RECOVER_AVL",
    }

    # Existing operation names are kept as aliases so current services do not
    # need to change their business logic just to register an action.
    ACTION_ALIASES = {
        "create_event": "CREATE_EVENT",
        "create_manual_event": "CREATE_EVENT",
        "updated_event": "UPDATE_EVENT",
        "delete_event": "DELETE_EVENT",
        "mass_archive": "ARCHIVE_BRANCH",
        "mark_reviewed": "MARK_REVIEWED",
        "advance_clock": "ADVANCE_CLOCK",
        "advance_clock_to": "ADVANCE_CLOCK",
        "change_parameter": "CHANGE_PARAMETER",
        "load_scenario": "LOAD_SCENARIO",
        "queue_step": "PROCESS_REPORT",
        "process_report": "PROCESS_REPORT",
        "recover_avl_balance": "RECOVER_AVL",
        "recover_avl": "RECOVER_AVL",
    }

    # Inverse action associated with each action type
    INVERSE_ACTIONS = {
        "CREATE_EVENT": "REMOVE_CHANGE",
        "UPDATE_EVENT": "RESTORE_CHANGE",
        "DELETE_EVENT": "RESTORE_CHANGE",
        "ARCHIVE_BRANCH": "RESTORE_CHANGE",
        "MARK_REVIEWED": "RESTORE_CHANGE",
        "ADVANCE_CLOCK": "RESTORE_CHANGE",
        "CHANGE_PARAMETER": "RESTORE_CHANGE",
        "LOAD_SCENARIO": "CLEAR_SCENARIO",
        "PROCESS_REPORT": "RESTORE_CHANGE",
        "RECOVER_AVL": "RESTORE_CHANGE",
    }

    # -------------------------------------------------------------------------
    # Action type validation
    # -------------------------------------------------------------------------

    # Return the public action name or reject an unknown operation
    def normalize_type(self, action_type):
        if not isinstance(action_type, str):
            raise ActionStackError("El tipo de acción debe ser texto")

        normalized = self.ACTION_ALIASES.get(action_type, action_type.upper())
        if normalized not in self.ACTION_TYPES:
            raise ActionStackError(f"Tipo de acción inválido: {action_type}")
        return normalized

    # -------------------------------------------------------------------------
    # Registering actions
    # -------------------------------------------------------------------------

    # Push one completed action onto the observatory-owned stack
    def push_action(self, observatory, action):
        if not isinstance(action, Action):
            raise ActionStackError("La pila solo acepta objetos Action")
        action_type = self.normalize_type(action.getActionType())
        action.setActionType(action_type)

        # Older callers still provide a complete before-version. Compress it
        # before it reaches the stack, so persisted actions store only the
        # values that must be restored by undo.
        if action.getUndoData() is None:
            before_snapshot = action.getBeforeSnapshot()
            if not isinstance(before_snapshot, dict):
                raise ActionStackError("La acción no contiene datos para deshacer")

            if action_type == "LOAD_SCENARIO":
                undo_data = {"version": 1, "changes": []}
            else:
                undo_data = self._build_undo_data(
                    before_snapshot,
                    observatory.toVersion(),
                )

            action.setUndoData(undo_data)
            action.setInverseAction(self.INVERSE_ACTIONS[action_type])
            # Do not persist the complete state after compacting it.
            action.setBeforeSnapshot(None)

        observatory.getActionStack().push(action)
        return action

    # Build and push an action after its operation has succeeded
    def record_action(self, observatory, action_type, before_snapshot, metadata=None):
        action = Action(
            action_type=self.normalize_type(action_type),
            datetime_value=observatory.getClock().getCurrentTime(),
            before_snapshot=before_snapshot,
            metadata=metadata or {},
        )
        return self.push_action(observatory, action)

    # -------------------------------------------------------------------------
    # Compact undo data
    # -------------------------------------------------------------------------

    # Build a small list containing only values changed by the action
    def _build_undo_data(self, before, after):
        changes = []
        self._collect_changes(before, after, [], changes)
        return {"version": 1, "changes": changes}

    # Compare dictionaries recursively and keep the old changed value
    def _collect_changes(self, before, after, path, changes):
        if isinstance(before, dict) and isinstance(after, dict):
            keys = set(before.keys()) | set(after.keys())
            for key in keys:
                child_path = path + [key]
                if key not in before:
                    changes.append({"path": child_path, "exists": False})
                elif key not in after:
                    changes.append({
                        "path": child_path,
                        "exists": True,
                        "value": deepcopy(before[key]),
                    })
                else:
                    self._collect_changes(before[key], after[key], child_path, changes)
            return

        # Lists are restored as one field. This keeps queue and station data
        # easy to understand while avoiding a copy of unrelated observatory
        # fields.
        if before != after:
            changes.append({
                "path": path,
                "exists": True,
                "value": deepcopy(before),
            })

    # Apply compact inverse values to a serializable observatory dict
    def _apply_undo_data(self, data, undo_data):
        if not isinstance(undo_data, dict) or undo_data.get("version") != 1:
            raise ActionStackError("Datos de deshacer inválidos")

        for change in undo_data.get("changes", []):
            path = change.get("path", [])
            if not path:
                raise ActionStackError("Ruta de deshacer inválida")
            parent = data
            for key in path[:-1]:
                if not isinstance(parent, dict) or key not in parent:
                    raise ActionStackError("No se encontró el estado a restaurar")
                parent = parent[key]

            key = path[-1]
            if not isinstance(parent, dict):
                raise ActionStackError("No se encontró el estado a restaurar")
            if change.get("exists"):
                parent[key] = deepcopy(change.get("value"))
            else:
                parent.pop(key, None)
        return data

    # -------------------------------------------------------------------------
    # Queries about the stack
    # -------------------------------------------------------------------------

    # Return the next action to undo without removing it
    def peek(self, observatory):
        try:
            return observatory.getActionStack().peek()
        except IndexError as error:
            raise ActionStackError("No hay acciones para deshacer") from error

    # Check if there is at least one action to undo
    def can_undo(self, observatory):
        return not observatory.getActionStack().is_empty()

    # Get the number of actions in the stack
    def size(self, observatory):
        return observatory.getActionStack().size()

    # Remove all the actions from the stack
    def clear(self, observatory):
        observatory.getActionStack().items.clear()

    # -------------------------------------------------------------------------
    # Undoing actions
    # -------------------------------------------------------------------------

    # Execute the compact inverse operation for the latest action
    def undo(self, observatory):
        stack = observatory.getActionStack()
        if stack.is_empty():
            raise ActionStackError("No hay acciones para deshacer")

        action = stack.pop()
        if action.getActionType() == "LOAD_SCENARIO":
            # Loading a scenario is intentionally undone by returning to the
            # empty state so the user can choose another JSON scenario.
            return SeismicObservatory(), action

        try:
            undo_data = action.getUndoData()
            if undo_data is None:
                # Read old persisted actions during the transition to the
                # compact format. New actions never use this path.
                snapshot = action.getBeforeSnapshot()
                if not isinstance(snapshot, dict):
                    raise ActionStackError("La acción no contiene datos para deshacer")
                data = observatory.toDict()
                data.update(snapshot)
            else:
                data = self._apply_undo_data(observatory.toDict(), undo_data)

            # The popped stack is the exact history from before this action.
            data["action_stack"] = stack.toDict()
            restored = SeismicObservatory.fromDict(data)
            if action.getActionType() == "CREATE_EVENT":
                restored.deleteLastId()

        except (KeyError, TypeError, ValueError, AttributeError, ActionStackError) as error:
            # Put the action back if restoration fails, leaving the live state
            # and the undo history unchanged.
            stack.push(action)
            raise ActionStackError(f"No se pudo restaurar la acción: {error}") from error

        return restored, action
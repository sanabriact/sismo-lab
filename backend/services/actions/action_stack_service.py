from backend.models.action import Action
from backend.models.seismic_observatory import SeismicObservatory


class ActionStackError(Exception):
    """Raised when an action cannot be inspected or restored."""


class ActionStackService:
    """Manage the observatory's explicit LIFO action stack."""

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

    def normalize_type(self, action_type):
        """Return the public action name or reject an unknown operation."""
        if not isinstance(action_type, str):
            raise ActionStackError("El tipo de acción debe ser texto")

        normalized = self.ACTION_ALIASES.get(action_type, action_type.upper())
        if normalized not in self.ACTION_TYPES:
            raise ActionStackError(f"Tipo de acción inválido: {action_type}")
        return normalized

    def push_action(self, observatory, action):
        """Push one completed action onto the observatory-owned stack."""
        if not isinstance(action, Action):
            raise ActionStackError("La pila solo acepta objetos Action")
        action.setActionType(self.normalize_type(action.getActionType()))
        observatory.getActionStack().push(action)
        return action

    def record_action(self, observatory, action_type, before_snapshot, metadata=None):
        """Build and push an action after its operation has succeeded."""
        action = Action(
            action_type=self.normalize_type(action_type),
            datetime_value=observatory.getClock().getCurrentTime(),
            before_snapshot=before_snapshot,
            metadata=metadata or {},
        )
        return self.push_action(observatory, action)

    def peek(self, observatory):
        """Return the next action to undo without removing it."""
        try:
            return observatory.getActionStack().peek()
        except IndexError as error:
            raise ActionStackError("No hay acciones para deshacer") from error

    def can_undo(self, observatory):
        return not observatory.getActionStack().is_empty()

    def size(self, observatory):
        return observatory.getActionStack().size()

    def clear(self, observatory):
        observatory.getActionStack().items.clear()

    def undo(self, observatory):
        """Restore the snapshot belonging to the latest completed action."""
        stack = observatory.getActionStack()
        if stack.is_empty():
            raise ActionStackError("No hay acciones para deshacer")

        action = stack.pop()
        snapshot = action.getBeforeSnapshot()
        if not isinstance(snapshot, dict):
            stack.push(action)
            raise ActionStackError("La acción no contiene un estado anterior")

        if action.getActionType() == "LOAD_SCENARIO":
            # Loading a scenario is intentionally undone by returning to the
            # empty state so the user can choose another JSON scenario.
            return SeismicObservatory(), action

        try:
            # toVersion() intentionally excludes the action stack. The stack
            # after popping is therefore the exact stack that existed before
            # the action being undone.
            data = observatory.toDict()
            data.update(snapshot)
            data["scenario_id"] = snapshot.get(
                "scenario_id", observatory.getScenarioId()
            )
            data["action_stack"] = snapshot.get("action_stack", stack.toDict())
            data["saved_versions"] = snapshot.get(
                "saved_versions", observatory.getSavedVersions()
            )
            restored = SeismicObservatory.fromDict(data)
        except (KeyError, TypeError, ValueError, AttributeError) as error:
            # Put the action back if restoration fails, leaving the live state
            # and the undo history unchanged.
            stack.push(action)
            raise ActionStackError(f"No se pudo restaurar la acción: {error}") from error

        return restored, action

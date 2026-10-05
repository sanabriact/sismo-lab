import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.models.action import Action
from backend.models.seismic_observatory import SeismicObservatory
from backend.models.station import Station
from backend.services.actions.action_stack_service import ActionStackError, ActionStackService
from backend.services.reports.report_processor import ReportProcessor
from backend.services.reports.report_queue_service import ReportQueueService
from backend.utils.quantities import parseDatetime


NOW = parseDatetime("2026-09-07T10:00:00Z")


def make_observatory():
    observatory = SeismicObservatory()
    observatory.setClock(type(observatory.getClock())(NOW))
    observatory.addStation(Station(1, "North", 100, 800))
    return observatory


def test_push_and_lifo_order():
    stack = make_observatory().getActionStack()
    moment = NOW
    stack.push(Action("CREATE_EVENT", moment, {}))
    stack.push(Action("UPDATE_EVENT", moment, {}))
    stack.push(Action("DELETE_EVENT", moment, {}))

    assert stack.size() == 3
    assert stack.pop().getActionType() == "DELETE_EVENT"
    assert stack.pop().getActionType() == "UPDATE_EVENT"
    assert stack.pop().getActionType() == "CREATE_EVENT"


def test_empty_undo_returns_a_domain_error():
    with pytest.raises(ActionStackError, match="No hay acciones"):
        ActionStackService().undo(make_observatory())


def test_create_event_undo_restores_the_previous_state():
    observatory = make_observatory()
    service = ActionStackService()
    before = observatory.toVersion()

    observatory.createEvent(7, 4.8, 70.0, 200.0, 200.0, NOW, 1, 1)
    service.record_action(observatory, "CREATE_EVENT", before)

    restored, action = service.undo(observatory)

    assert action.getActionType() == "CREATE_EVENT"
    assert restored.searchEventById(7) is None
    assert restored.getHistory().getDeletedIds() == set()
    assert restored.getHistory().listHistoricIds == []
    assert service.size(restored) == 0


def test_process_report_undo_restores_report_position_and_tree():
    observatory = make_observatory()
    queue_service = ReportQueueService()
    raw = {
        "event_id": 7,
        "revision": 1,
        "station": 1,
        "magnitude": 4.8,
        "depth": 70.0,
        "epicenter_x": 200.0,
        "epicenter_y": 200.0,
        "datetime": "2026-09-07T09:00:00Z",
    }
    queue_service.prepare(observatory, [raw])
    before = observatory.toVersion()
    report = observatory.getReportQueue().dequeue()
    ReportProcessor().apply(observatory, report)

    service = ActionStackService()
    service.record_action(observatory, "PROCESS_REPORT", before)
    restored, action = service.undo(observatory)

    assert action.getActionType() == "PROCESS_REPORT"
    assert restored.searchEventById(7) is None
    assert restored.getReportQueue().size() == 1


def test_load_scenario_undo_returns_to_an_empty_scenario():
    observatory = make_observatory()
    observatory.createEvent(7, 4.8, 70.0, 200.0, 200.0, NOW, 1, 1)
    service = ActionStackService()
    service.record_action(observatory, "LOAD_SCENARIO", observatory.toVersion())

    restored, action = service.undo(observatory)

    assert action.getActionType() == "LOAD_SCENARIO"
    assert restored.getScenarioId() is None
    assert restored.getStations() == []
    assert restored.getAVLTree().root is None
    assert restored.getBSTTree().root is None


def test_unknown_action_type_is_rejected():
    service = ActionStackService()
    with pytest.raises(ActionStackError, match="Tipo de acción inválido"):
        service.record_action(make_observatory(), "ROTATE_LEFT", {})


def test_all_actions_store_compact_inverse_data():
    action_types = [
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
    ]

    for action_type in action_types:
        observatory = make_observatory()
        service = ActionStackService()
        before = observatory.toVersion()

        # The service receives the legacy input shape and compacts it before
        # the action becomes part of the persisted stack.
        service.record_action(observatory, action_type, before)
        action = observatory.getActionStack().peek()

        assert action.getBeforeSnapshot() is None
        assert action.getUndoData()["version"] == 1
        assert action.getInverseAction() is not None

        restored, undone = service.undo(observatory)
        assert undone.getActionType() == action_type
        assert service.size(restored) == 0

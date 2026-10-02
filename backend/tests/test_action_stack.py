import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.models.action import Action
from backend.models.report import Report
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


def test_unknown_action_type_is_rejected():
    service = ActionStackService()
    with pytest.raises(ActionStackError, match="Tipo de acción inválido"):
        service.record_action(make_observatory(), "ROTATE_LEFT", {})

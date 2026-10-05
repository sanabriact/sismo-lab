from datetime import datetime, timezone
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.models.seismic_observatory import SeismicObservatory
from backend.models.station import Station
from backend.models.report import Report
from backend.services.metrics.metrics_service import MetricsService
from backend.services.reports.report_processor import ReportProcessor
from backend.services.reports.report_queue_runner import ReportQueueRunner
from backend.services.reports.report_queue_service import ReportQueueService
from backend.services.event_engine import EventEngine
from backend.services.seismic_observatory_service import SeismicObservatoryService
from backend.utils.quantities import parseDatetime


UTC_CLOCK = parseDatetime("2026-09-07T10:00:00Z")


class FakeSocket:
    def __init__(self):
        self.emitted = []

    def emit(self, name, payload):
        self.emitted.append((name, payload))

    def sleep(self, _interval):
        return None

    def start_background_task(self, target):
        return target()


class FakeService:
    def __init__(self):
        self.metrics_service = MetricsService()
        self.saved = 0

    def saveObservatory(self, _observatory):
        self.saved += 1
        return True

    def build_manual_update_report(self, observatory, event_id, data):
        return SeismicObservatoryService.build_manual_update_report(self, observatory, event_id, data)


class FakeEngine(EventEngine):
    def __init__(self, observatory):
        super().__init__(
            FakeSocket(),
            FakeService(),
            type("ModeNotifier", (), {"notify": lambda self, payload: None})(),
            object(),
        )
        self.observatory = observatory
        self.scenario_id = "test-scenario"


def make_observatory():
    observatory = SeismicObservatory()
    observatory.setClock(type(observatory.getClock())(UTC_CLOCK))
    observatory.addStation(Station(1, "North", 100, 800))
    observatory.addStation(Station(2, "South", 100, 200))
    return observatory


def raw(event_id, revision=1, station=1, magnitude=4.8, depth=70.0, when="2026-09-07T09:00:00Z"):
    return {
        "event_id": event_id,
        "revision": revision,
        "station": station,
        "magnitude": magnitude,
        "depth": depth,
        "epicenter_x": 200.0,
        "epicenter_y": 200.0,
        "datetime": when,
    }


def report_from(data, observatory):
    station = next(item for item in observatory.getStations() if item.getId() == data["station"])
    return Report(
        data["event_id"], data["revision"], station, data["magnitude"],
        data["depth"], data["epicenter_x"], data["epicenter_y"],
        parseDatetime(data["datetime"]),
    )


def test_fifo_preserves_received_order():
    observatory = make_observatory()
    result = ReportQueueService().prepare(observatory, [raw(3, magnitude=6.2), raw(1)])
    assert result["ok"] is True
    assert observatory.getReportQueue().peek().getEventId() == 3
    assert observatory.getReportQueue().dequeue().getEventId() == 3
    assert observatory.getReportQueue().dequeue().getEventId() == 1


def test_prepare_is_atomic_when_one_report_is_invalid():
    observatory = make_observatory()
    result = ReportQueueService().prepare(observatory, [raw(1), raw(2, station=99)])
    assert result["ok"] is False
    assert result["enqueued"] == 0
    assert observatory.getReportQueue().is_empty()


def test_prepare_rejects_future_dates_and_extra_precision():
    observatory = make_observatory()
    result = ReportQueueService().prepare(observatory, [raw(1, magnitude=4.81)])
    assert result["ok"] is False
    assert observatory.getReportQueue().is_empty()
    result = ReportQueueService().prepare(observatory, [raw(1, when="2026-09-07T11:00:00Z")])
    assert result["ok"] is True
    engine = FakeEngine(observatory)
    runner = ReportQueueRunner(engine, ReportQueueService(), ReportProcessor())
    assert runner.process_next()["decision"] == "rejected_invalid"


def test_unknown_id_accepts_a_first_revision_greater_than_one():
    observatory = make_observatory()
    result = ReportProcessor().apply(
        observatory,
        report_from(raw(7, revision=3), observatory),
    )
    assert result.decision == "created"
    assert observatory.searchEventById(7).getCurrentRevision() == 3


def test_unknown_id_revision_one_creates_event():
    observatory = make_observatory()
    result = ReportProcessor().apply(
        observatory,
        report_from(raw(7, revision=1), observatory),
    )
    event = observatory.searchEventById(7)
    assert result.decision == "created"
    assert event.getCurrentRevision() == 1
    assert event.getAttentionStatus() == "pending"


def test_correction_changes_key_and_counts_accepted_correction():
    observatory = make_observatory()
    observatory.createEvent(7, 4.8, 70.0, 200.0, 200.0, parseDatetime("2026-09-07T08:00:00Z"), 1, 1)
    report = report_from(raw(7, revision=2, magnitude=6.2, depth=15.0), observatory)
    result = ReportProcessor().apply(observatory, report)
    assert result.decision == "updated"
    assert observatory.getMetrics().getAcceptedCorrections() == 1
    assert observatory.searchEventById(7).getKey() == (3, 6.2, 7)


def test_old_report_is_discarded_without_reverting_event():
    observatory = make_observatory()
    observatory.createEvent(7, 4.8, 70.0, 200.0, 200.0, parseDatetime("2026-09-07T08:00:00Z"), 2, 1)
    result = ReportProcessor().apply(observatory, report_from(raw(7, revision=1), observatory))
    assert result.decision == "stale"
    assert observatory.searchEventById(7).getCurrentRevision() == 2
    assert observatory.getMetrics().getDiscardedReports() == 1


def test_confirmation_does_not_duplicate_station():
    observatory = make_observatory()
    observatory.createEvent(7, 4.8, 70.0, 200.0, 200.0, parseDatetime("2026-09-07T08:00:00Z"), 1, 1)
    report = report_from(raw(7, station=2), observatory)
    assert ReportProcessor().apply(observatory, report).decision == "conflict"
    same = report_from(raw(7, station=1, when="2026-09-07T08:00:00Z"), observatory)
    assert ReportProcessor().apply(observatory, same).decision == "confirmed"
    assert observatory.searchEventById(7).getReportingStations() == {1}


def test_same_revision_different_data_is_conflict():
    observatory = make_observatory()
    observatory.createEvent(7, 4.8, 70.0, 200.0, 200.0, parseDatetime("2026-09-07T08:00:00Z"), 1, 1)
    result = ReportProcessor().apply(observatory, report_from(raw(7, magnitude=5.0), observatory))
    assert result.decision == "conflict"
    assert observatory.getMetrics().getConflicts() == 1


def test_deleted_id_is_rejected():
    observatory = make_observatory()
    observatory.getHistory().addDeletedId(7)
    result = ReportProcessor().apply(observatory, report_from(raw(7), observatory))
    assert result.decision == "rejected_deleted"


def test_runner_processes_one_report_and_emits_queue_events():
    observatory = make_observatory()
    engine = FakeEngine(observatory)
    runner = ReportQueueRunner(engine, ReportQueueService(), ReportProcessor())
    assert runner.prepare_reports([raw(7)])["ok"] is True
    result = runner.process_next()
    assert result["ok"] is True
    assert result["decision"] == "created"
    assert result["remaining"] == 0
    assert any(name == "tree:operation" for name, _ in engine.socketio.emitted)
    assert engine.service.saved == 2


def test_snapshot_keeps_positions_and_stress_mode_keeps_result():
    observatory = make_observatory()
    observatory.getAVLTree().setBalance(False)
    engine = FakeEngine(observatory)
    runner = ReportQueueRunner(engine, ReportQueueService(), ReportProcessor())
    runner.prepare_reports([raw(7), raw(8, station=2)])
    snapshot = runner.queue_service.snapshot(observatory)
    assert [item["position"] for item in snapshot["items"]] == [1, 2]
    assert runner.process_next()["decision"] == "created"
    assert runner.process_next()["decision"] == "created"
    assert observatory.getAVLTree().audit()["issues"] == []


def test_archived_event_can_be_reactivated():
    observatory = make_observatory()
    observatory.createEvent(7, 4.8, 70.0, 200.0, 200.0, parseDatetime("2026-09-07T08:00:00Z"), 1, 1)
    event = observatory.searchEventById(7)
    observatory.getAVLTree().delete(7)
    observatory.getBSTTree().delete(7)
    event.setEventStatus("archived")
    observatory.getHistory().addArchived(7, event)
    result = ReportProcessor().apply(observatory, report_from(raw(7, revision=2, magnitude=6.2, depth=15.0), observatory))
    assert result.decision == "reactivated"
    updated = observatory.searchEventById(7)
    assert updated.getAttentionStatus() == "pending"
    assert updated.getCurrentRevision() == 2
    assert updated.getKey() == (3, 6.2, 7)
    assert updated.getEventStatus() == "active"
    assert observatory.getHistory().getArchived().get(7) is None


def test_manual_edit_updates_archived_event_with_higher_revision():
    observatory = make_observatory()
    observatory.createEvent(7, 4.8, 70.0, 200.0, 200.0, parseDatetime("2026-09-07T08:00:00Z"), 1, 1)
    archived = observatory.searchEventById(7)
    observatory.getAVLTree().delete(7)
    observatory.getBSTTree().delete(7)
    archived.setEventStatus("archived")
    observatory.getHistory().addArchived(7, archived)

    engine = FakeEngine(observatory)
    response = engine.update_manual_event({
        "event_id": 7,
        "magnitude": 6.2,
        "depth": 15.0,
        "epicenter_x": 220.0,
        "epicenter_y": 210.0,
        "datetime": "2026-09-07T08:30:00Z",
        "station": 2,
    })

    updated = observatory.searchEventById(7)
    assert response["ok"] is True
    assert response["queued"] is False
    assert updated is not None
    assert updated.getCurrentRevision() == 2
    assert updated.getKey() == (3, 6.2, 7)
    assert updated.getEventStatus() == "active"
    assert observatory.getHistory().getArchived().get(7) is None


def test_main():
    tests = [value for name, value in globals().items() if name.startswith("test_") and callable(value) and name != "test_main"]
    for test in tests:
        test()
    print(f"passed {len(tests)} report queue tests")


if __name__ == "__main__":
    test_main()

# ------------------------------------------------------------------
# t es t r eq ui re d c or re ct io n a nd r ec ov er y
# ------------------------------------------------------------------

"""Reproducible checks for the correction and AVL recovery requirements."""

from datetime import timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.models.event import Event
from backend.models.report import Report
from backend.models.seismic_observatory import SeismicObservatory
from backend.models.station import Station
from backend.services.stress.stress_mode_service import StressModeService
from backend.services.reports.report_processor import ReportProcessor
from backend.utils.quantities import parseDatetime


NOW = parseDatetime("2026-09-07T10:00:00Z")


def test_correction_then_older_report_keeps_one_corrected_event():
    observatory = SeismicObservatory()
    observatory.setClock(type(observatory.getClock())(NOW))
    station = Station(1, "North", 100, 800)
    observatory.addStation(station)
    observatory.createEvent(7, 4.8, 70.0, 200.0, 200.0, parseDatetime("2026-09-07T09:00:00Z"), 1, 1)
    processor = ReportProcessor()

    corrected_report = Report(
        7, 2, station, 6.2, 15.0, 220.0, 210.0,
        parseDatetime("2026-09-07T09:00:00Z"),
    )
    correction = processor.apply(observatory, corrected_report)

    stale_report = Report(
        7, 1, station, 4.8, 70.0, 200.0, 200.0,
        parseDatetime("2026-09-07T09:00:00Z"),
    )
    stale = processor.apply(observatory, stale_report)

    event = observatory.searchEventById(7)
    assert correction.decision == "updated"
    assert correction.key_before == [2, 4.8, 7]
    assert correction.key_after == [3, 6.2, 7]
    assert stale.decision == "stale"
    assert event.getCurrentRevision() == 2
    assert event.getKey() == (3, 6.2, 7)
    assert len(observatory.getAVLTree().index) == 1
    assert len(observatory.getBSTTree().index) == 1


def _event(event_id):
    return Event(
        event_id, 5.0, 50.0, 100.0 + event_id, 100.0,
        parseDatetime("2026-09-07T08:00:00Z"), 1, 1,
    )


def test_all_four_avl_rotation_cases_are_reported():
    cases = {
        "LL": (30, 20, 10),
        "RR": (10, 20, 30),
        "LR": (30, 10, 20),
        "RL": (10, 30, 20),
    }

    for expected_rotation, insertion_order in cases.items():
        tree = SeismicObservatory().getAVLTree()
        tree.begin_visual_operation()
        for event_id in insertion_order:
            assert tree.insert(_event(event_id)) is True

        steps = tree.finish_visual_operation()
        observed = [
            step["rotation"]["type"]
            for step in steps
            if step.get("kind") == "rotation"
        ]
        assert observed == [expected_rotation]
        assert tree.audit()["ok"] is True


def test_stress_recovery_preserves_event_identity_order_and_associations():
    observatory = SeismicObservatory()
    observatory.setClock(type(observatory.getClock())(NOW))
    observatory.addStation(Station(1, "North", 100, 800))
    tree = observatory.getAVLTree()
    tree.setBalance(False)

    for event_id in range(1, 16):
        magnitude = 6.0 if event_id == 15 else 4.0 + event_id / 10
        observatory.createEvent(
            event_id, magnitude, 50.0, 100.0 + event_id, 100.0,
            parseDatetime("2026-09-07T09:00:00Z") - timedelta(minutes=event_id), 1, 1,
        )

    identity_by_id = {event_id: observatory.searchEventById(event_id) for event_id in range(1, 16)}
    node_by_id = {event_id: tree.searchById(event_id) for event_id in range(1, 16)}
    order_before = [event.getKey() for event in tree.inorder()]
    associations_before = observatory.getAssociationManager().toDict()
    stress_audit = tree.audit("stress")

    assert stress_audit["max_imbalance"] > 2
    assert stress_audit["warnings"]
    assert associations_before["selected_references"]

    recovery = StressModeService().deactivateStressMode(observatory)
    steps = recovery["steps"]
    normal_audit = tree.audit("normal")
    order_after = [event.getKey() for event in tree.inorder()]

    assert normal_audit["ok"] is True
    assert recovery["ok"] is True
    assert observatory.getExecutionMode() == "normal"
    assert tree.getBalance() is True
    assert order_after == order_before
    assert set(tree.index) == set(identity_by_id)
    assert all(tree.searchById(event_id).getValue() is event for event_id, event in identity_by_id.items())
    assert all(tree.searchById(event_id) is node for event_id, node in node_by_id.items())
    assert any(step.get("kind") == "rotation" for step in steps)
    assert observatory.getAssociationManager().toDict() == associations_before

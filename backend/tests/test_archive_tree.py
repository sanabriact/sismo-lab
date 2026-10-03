"""Tests for the two-phase AVL/BST subtree archive flow."""

from datetime import datetime, timedelta, timezone

from backend.models.event import Event
from backend.models.seismic_observatory import SeismicObservatory
from backend.services.archive.archive_tree_service import ArchiveTreeService
from backend.services.event_engine import EventEngine


NOW = datetime(2026, 9, 7, 10, 0, tzinfo=timezone.utc)


def make_observatory(event_specs):
    observatory = SeismicObservatory()
    observatory.scenario_id = "archive-test"
    observatory.getClock().setCurrentTime(NOW)
    for event_id, magnitude, age_hours in event_specs:
        event = Event(
            event_id,
            magnitude,
            100.0,
            100.0,
            100.0,
            NOW - timedelta(hours=age_hours),
            1,
            "station-1",
        )
        assert observatory.getAVLTree().insert(event)
        assert observatory.getBSTTree().insert(event)
    return observatory


def test_affirmative_decision_removes_selected_events_from_both_trees_and_archives_them():
    observatory = make_observatory(
        [(10, 2.5, 100), (5, 2.0, 100), (15, 3.0, 100)]
    )
    service = ArchiveTreeService()

    preview = service.prepare(observatory, NOW, 72, "client-a")

    assert preview["ok"] is True
    assert preview["tree"]["number_nodes"] == 3
    assert set(preview["tree"]["affected_ids"]) == {5, 10, 15}
    assert len(observatory.getAVLTree().index) == 3
    assert len(observatory.getBSTTree().index) == 3

    result = service.decide(observatory, True, "client-a")

    assert result["ok"] is True
    assert result["archived"] is True
    assert result["subtree"]["number_nodes"] == 3
    assert observatory.getAVLTree().index == {}
    assert observatory.getBSTTree().index == {}
    assert set(observatory.getHistory().getArchived()) == {5, 10, 15}
    assert all(
        event.getEventStatus() == "archived"
        for event in observatory.getHistory().getArchived().values()
    )


def test_declining_preview_keeps_both_trees_and_history_unchanged():
    observatory = make_observatory([(7, 2.0, 100)])
    service = ArchiveTreeService()

    assert service.prepare(observatory, NOW, 72, "client-a")["ok"] is True
    result = service.decide(observatory, False, "client-a")

    assert result == {"ok": True, "archived": False}
    assert set(observatory.getAVLTree().index) == {7}
    assert set(observatory.getBSTTree().index) == {7}
    assert observatory.getHistory().getArchived() == {}


def test_no_eligible_subtree_returns_normal_result_and_creates_no_pending_selection():
    observatory = make_observatory([(7, 2.0, 72)])
    service = ArchiveTreeService()

    result = service.prepare(observatory, NOW, 72, "client-a")

    assert result == {"ok": False, "reason": "nothing_to_archive"}
    assert service.decide(observatory, True, "client-a")["reason"] == "no_pending_archive"
    assert set(observatory.getAVLTree().index) == {7}
    assert set(observatory.getBSTTree().index) == {7}


def test_selection_uses_avl_tie_break_and_leaves_unselected_events_in_both_trees():
    observatory = make_observatory(
        [(20, 2.0, 10), (10, 1.0, 100), (30, 3.0, 100)]
    )
    service = ArchiveTreeService()

    preview = service.prepare(observatory, NOW, 72, "client-a")

    assert preview["ok"] is True
    assert preview["tree"]["affected_ids"] == [30]
    result = service.decide(observatory, True, "client-a")

    assert result["ok"] is True
    assert set(observatory.getAVLTree().index) == {10, 20}
    assert set(observatory.getBSTTree().index) == {10, 20}
    assert set(observatory.getHistory().getArchived()) == {30}


def test_event_engine_coordinates_preview_confirmation_and_persistence():
    class FakeSocket:
        def emit(self, *_args, **_kwargs):
            pass

    class FakeMetrics:
        def __init__(self):
            self.operations = []

        def capture_display(self, observatory):
            return {
                "tree": {"active_events": len(observatory.getAVLTree().index)},
                "counters": {
                    "mass_archives": observatory.getMetrics().getMassArchives(),
                    "archived_events": observatory.getMetrics().getArchivedEvents(),
                },
            }

        def refresh_derived_metrics(self, _observatory):
            pass

        def record_operation(self, **operation):
            self.operations.append(operation)

    class FakeService:
        def __init__(self):
            self.metrics_service = FakeMetrics()
            self.saved = []

        def saveObservatory(self, observatory):
            self.saved.append(observatory)

    observatory = make_observatory([(7, 2.0, 100)])
    backend_service = FakeService()
    engine = EventEngine(FakeSocket(), backend_service, object(), object())
    engine.set_observatory(observatory)

    preview = engine.prepare_archive_tree(72, "client-a")
    result = engine.decide_archive_tree(True, "client-a")

    assert preview["ok"] is True
    assert result["ok"] is True
    assert backend_service.saved == [observatory]
    assert len(backend_service.metrics_service.operations) == 1
    assert observatory.getMetrics().getMassArchives() == 1
    assert observatory.getMetrics().getArchivedEvents() == 1

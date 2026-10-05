"""Specification-focused tests for queries, persistence, and recovery data."""

from datetime import datetime, timedelta, timezone

from backend.models.event import Event
from backend.models.report import Report
from backend.models.seismic_observatory import SeismicObservatory
from backend.models.station import Station
from backend.repositories.seismic_observatory_repository import SeismicObservatoryRepository
from backend.services.archive.archive_tree_service import ArchiveTreeService
from backend.services.query.query_service import QueryService


UTC = timezone.utc
BASE_TIME = datetime(2026, 9, 7, 10, 0, tzinfo=UTC)


def add_event(observatory, event_id, magnitude, hours_after=0, depth=10.0):
    """Create one event through the domain model used by the application."""
    result = observatory.createEvent(
        event_id,
        magnitude,
        depth,
        100.0,
        100.0,
        BASE_TIME + timedelta(hours=hours_after),
        1,
        1,
    )
    assert result[0] is True


def test_all_queries_report_examined_nodes_and_compare_insertion_orders():
    observatory = SeismicObservatory()
    add_event(observatory, 10, 6.0, 0)
    add_event(observatory, 20, 4.0, 1)
    add_event(observatory, 30, 5.0, 2)
    add_event(observatory, 40, 3.0, 3)

    service = QueryService()
    responses = [
        service.execute(observatory, "by_id", {"event_id": 20}),
        service.execute(observatory, "top_pending", {"k": 2}),
        service.execute(observatory, "magnitude_range", {"minimum": 4, "maximum": 5}),
        service.execute(observatory, "date_depth_range", {
            "start_date": "2026-09-07",
            "end_date": "2026-09-07",
            "maximum_depth": 10,
        }),
        service.execute(observatory, "associations", {"event_id": 20}),
        service.execute(observatory, "expensive_access", {}),
        service.execute(observatory, "tree_comparison", {}),
    ]

    assert all("examined_nodes" in response for response in responses)
    comparison = responses[-1]["comparison"]
    assert len(comparison["runs"]) == 7
    assert {run["order"] for run in comparison["runs"]} == {
        "current_order",
        "ascending_key",
        "descending_key",
        "ascending_id",
        "descending_id",
        "ascending_magnitude",
        "descending_magnitude",
    }
    assert all("height" in run["avl"] and "leaves" in run["bst"]
               for run in comparison["runs"])


def test_persistence_round_trip_keeps_queue_associations_metrics_and_parameters(tmp_path):
    observatory = SeismicObservatory()
    observatory.scenario_id = "persistence-test"
    station = Station(1, "Station 1", 100.0, 100.0)
    observatory.addStation(station)
    add_event(observatory, 1, 6.0, 0)
    add_event(observatory, 2, 4.0, 1)
    observatory.setL(7)
    observatory.setT(96)
    observatory.getAssociationManager().setLimits(12, 25)
    observatory.recalculateAssociations()
    observatory.getClock().setCurrentTime(BASE_TIME + timedelta(hours=8))
    observatory.setExecutionMode("stress")
    observatory.getMetrics().setConflicts(3)
    observatory.getMetrics().setArchivedEvents(2)
    observatory.getReportQueue().enqueue(
        Report(2, 2, station, 4.2, 11, 100, 100, BASE_TIME)
    )

    repository = SeismicObservatoryRepository()
    repository.path = str(tmp_path / "observatory.json")
    assert repository.save(observatory) is True
    restored = repository.load()

    assert restored.getScenarioId() == "persistence-test"
    assert restored.getL() == 7
    assert restored.getT() == 96
    assert restored.getExecutionMode() == "stress"
    assert restored.getClock().getCurrentTime() == BASE_TIME + timedelta(hours=8)
    assert restored.getReportQueue().size() == 1
    assert restored.getReportQueue().peek().getEventId() == 2
    assert restored.getAssociationManager().getLimits() == {"W": 12.0, "R": 25.0}
    assert restored.getAssociationManager().getSelectedReferences() == \
        observatory.getAssociationManager().getSelectedReferences()
    assert restored.getMetrics().getConflicts() == 3
    assert restored.getMetrics().getArchivedEvents() == 2


def test_archive_moves_a_complete_branch_to_history_without_losing_associations():
    observatory = SeismicObservatory()
    observatory.scenario_id = "archive-test"
    observatory.getClock().setCurrentTime(BASE_TIME)
    add_event(observatory, 1, 2.0, -100)
    add_event(observatory, 2, 2.1, -99)
    add_event(observatory, 3, 6.0, -98)
    service = ArchiveTreeService()

    preview = service.prepare(observatory, BASE_TIME, 72, "test-client")
    assert preview["ok"] is True
    selected_ids = set(preview["tree"]["affected_ids"])
    result = service.decide(observatory, True, "test-client")

    assert result["ok"] is True
    assert selected_ids == set(observatory.getHistory().getArchived())
    assert selected_ids.isdisjoint(observatory.getAVLTree().index)
    assert all(
        event_id in observatory.getAssociationManager().getCandidates()
        for event_id in selected_ids
    )


def test_persisted_stress_topology_can_be_loaded_for_recovery():
    observatory = SeismicObservatory()
    observatory.scenario_id = "stress-recovery-test"
    observatory.setExecutionMode("stress")
    for event_id in (1, 2, 3, 4):
        add_event(observatory, event_id, 2.0 + event_id / 10, event_id)

    data = observatory.toDict()
    restored = SeismicObservatory.fromDict(data)

    assert restored.getExecutionMode() == "stress"
    assert set(restored.getAVLTree().index) == {1, 2, 3, 4}
    assert restored.toDict()["avl_tree"] == observatory.toDict()["avl_tree"]


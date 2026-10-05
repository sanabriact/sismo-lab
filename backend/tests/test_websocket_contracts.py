"""WebSocket contract tests for the public backend events."""

import backend.app as app_module


def test_websocket_mutation_and_query_events_return_engine_results(monkeypatch):
    """Each public event must accept the browser payload and return an ACK."""
    engine = app_module.event_engine
    socket_client = app_module.socketio.test_client(app_module.app)
    assert socket_client.is_connected() is True

    monkeypatch.setattr(engine, "advance_clock_hours", lambda hours: {
        "ok": True,
        "operation": "clock",
        "hours": hours,
    })
    monkeypatch.setattr(engine, "undo_action", lambda: {"ok": True, "operation": "undo"})
    monkeypatch.setattr(engine, "audit_structure", lambda: {"ok": True, "balanced": True})
    monkeypatch.setattr(engine, "get_observatory", lambda: None)
    monkeypatch.setattr(engine, "get_parameters", lambda: {"ok": True, "L": 3})
    monkeypatch.setattr(engine, "report_queue_snapshot", lambda: {"ok": True, "items": []})
    monkeypatch.setattr(engine, "process_report_step", lambda: {"ok": True, "processed": 1})
    monkeypatch.setattr(engine, "start_report_processing", lambda: {"ok": True, "started": True})
    monkeypatch.setattr(engine, "pause_report_processing", lambda: {"ok": True, "paused": True})

    assert socket_client.emit("clock:advance", {"hours": 1}, callback=True) == {
        "ok": True, "operation": "clock", "hours": 1,
    }
    assert socket_client.emit("action:undo", {}, callback=True)["ok"] is True
    assert socket_client.emit("structure:audit", {}, callback=True)["balanced"] is True
    assert socket_client.emit("reports:step", {}, callback=True)["processed"] == 1
    assert socket_client.emit("reports:start", {}, callback=True)["started"] is True
    assert socket_client.emit("reports:pause", {}, callback=True)["paused"] is True
    assert socket_client.emit("reports:snapshot", {}, callback=True)["items"] == []

    socket_client.disconnect()


def test_websocket_scenario_status_and_missing_scenario_are_stable(monkeypatch):
    engine = app_module.event_engine
    monkeypatch.setattr(engine, "get_observatory", lambda: None)
    socket_client = app_module.socketio.test_client(app_module.app)

    assert socket_client.emit("scenario:status", callback=True) == {
        "loaded": False,
        "scenarioId": None,
        "currentTime": None,
    }
    assert socket_client.emit("generation:start", {}, callback=True) == {
        "ok": False,
        "reason": "no_scenario",
    }

    socket_client.disconnect()


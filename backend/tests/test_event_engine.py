"""Focused tests for the EventEngine ownership boundaries."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.models.seismic_observatory import SeismicObservatory
from backend.services.event_engine import EventEngine
from backend.services.report_queue_runner import ReportQueueRunner
from backend.services.seismic_observatory_service import ScenarioValidationError


class FakeSocket:
    def __init__(self):
        self.emitted = []
        self.started = []

    def emit(self, name, payload):
        self.emitted.append((name, payload))

    def start_background_task(self, target):
        self.started.append(target)

    def sleep(self, _interval):
        return None


class Notifier:
    def __init__(self):
        self.payloads = []

    def notify(self, payload):
        self.payloads.append(payload)


class FakeValidator:
    def __init__(self, valid=True):
        self.valid = valid
        self.errors = ["invalid scenario"]
        self.calls = []

    def loadFromText(self, content, stress_mode=False):
        self.calls.append((content, stress_mode))
        return {"content": content} if self.valid else None


class FakeManager:
    def __init__(self):
        self.loaded = []

    def load_scenario(self, observatory):
        self.loaded.append(observatory)


class FakeService:
    def __init__(self, observatory=None):
        self.observatory = observatory
        self.loaded_text = []

    def loadScenarioFromText(self, content):
        self.loaded_text.append(content)
        return self.observatory

    def auditBalance(self, _observatory):
        return {
            "balanced": True,
            "maxImbalance": 0,
            "rotations": 0,
            "issues": [],
        }


def make_engine(observatory=None):
    socketio = FakeSocket()
    mode_changed = Notifier()
    service = FakeService(observatory)
    engine = EventEngine(socketio, service, mode_changed, object())
    if observatory is not None:
        engine.set_observatory(observatory)
    return engine, socketio, service, mode_changed


def test_runner_is_only_a_facade_over_engine_methods():
    class SpyEngine:
        report_queue_service = object()
        report_processor = object()
        report_queue_running = True

        def __init__(self):
            self.calls = []

        def prepare_reports(self, reports):
            self.calls.append(("prepare", reports))
            return "prepared"

        def process_report_step(self):
            self.calls.append(("step",))
            return "processed"

        def start_report_processing(self):
            self.calls.append(("start",))
            return "started"

        def pause_report_processing(self, reason="paused"):
            self.calls.append(("pause", reason))
            return "paused"

        def resume_report_processing(self):
            self.calls.append(("resume",))
            return "resumed"

        def report_queue_snapshot(self):
            self.calls.append(("snapshot",))
            return "snapshot"

    engine = SpyEngine()
    runner = ReportQueueRunner(engine)

    assert runner.prepare_reports([1]) == "prepared"
    assert runner.process_next() == "processed"
    assert runner.start_continuous() == "started"
    assert runner.pause() == "paused"
    assert runner.pause_for_recovery() == "paused"
    assert runner.resume() == "resumed"
    assert runner.snapshot() == "snapshot"
    assert runner.is_running() is True
    assert engine.calls == [
        ("prepare", [1]),
        ("step",),
        ("start",),
        ("pause", "paused"),
        ("pause", "recovering"),
        ("resume",),
        ("snapshot",),
    ]


def test_invalid_scenario_is_rejected_before_service_builds_it():
    engine, _socketio, service, _mode_changed = make_engine(SeismicObservatory())
    validator = FakeValidator(valid=False)
    engine.set_scenario_validator(validator)

    try:
        engine.load_scenario_from_text("bad json")
        assert False, "Expected ScenarioValidationError"
    except ScenarioValidationError as error:
        assert error.issues == validator.errors

    assert validator.calls == [("bad json", False)]
    assert service.loaded_text == []


def test_valid_scenario_is_activated_and_announced_by_engine():
    observatory = SeismicObservatory()
    engine, _socketio, service, _mode_changed = make_engine(observatory)
    validator = FakeValidator(valid=True)
    manager = FakeManager()
    scenario_loaded = Notifier()
    engine.set_scenario_validator(validator)
    engine.set_scenario_manager(manager)
    engine.set_scenario_loaded_notifier(scenario_loaded)

    result = engine.load_scenario_from_text("valid json")

    assert result is observatory
    assert service.loaded_text == ["valid json"]
    assert manager.loaded == [observatory]
    assert scenario_loaded.payloads[0]["stations"] == 0
    assert scenario_loaded.payloads[0]["events"] == 0


def test_engine_reports_no_scenario_without_touching_runner_state():
    engine, socketio, _service, _mode_changed = make_engine()
    runner = ReportQueueRunner(engine)

    result = runner.prepare_reports([])

    assert result["ok"] is False
    assert result["reason"] == "no_scenario"
    assert socketio.emitted == []
    assert runner.is_running() is False


def test_engine_pause_and_resume_are_the_single_queue_lifecycle():
    engine, socketio, _service, _mode_changed = make_engine(SeismicObservatory())
    runner = ReportQueueRunner(engine)

    assert runner.start_continuous()["ok"] is True
    assert len(socketio.started) == 1
    assert runner.pause_for_recovery() == {"ok": True, "reason": "recovering"}
    assert engine.report_queue_paused is True


def test_main():
    tests = [
        value
        for name, value in globals().items()
        if name.startswith("test_") and callable(value) and name != "test_main"
    ]
    for test in tests:
        test()
    print(f"passed {len(tests)} event engine tests")


if __name__ == "__main__":
    test_main()

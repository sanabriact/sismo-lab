class ReportQueueRunner:
    """Coordinates one-step and continuous report processing."""

    def __init__(self, engine, queue_service, processor, interval=1.5):
        self.engine = engine
        self.queue_service = queue_service
        self.processor = processor
        self.interval = interval
        self._running = False
        self._paused = False

    def prepare_reports(self, raw_reports):
        with self.engine.lock:
            if self.engine.observatory is None:
                return {"ok": False, "reason": "no_scenario", "enqueued": 0, "issues": []}
            result = self.queue_service.prepare(self.engine.observatory, raw_reports)
            if result["ok"]:
                self.engine.service.saveObservatory(self.engine.observatory)
            snapshot = self.queue_service.snapshot(self.engine.observatory)
        self.engine.socketio.emit("queue:updated", snapshot)
        return {**result, "snapshot": snapshot}

    def process_next(self):
        with self.engine.lock:
            if self.engine.observatory is None:
                return {"ok": False, "reason": "no_scenario"}
            if self.engine.recovering:
                return {"ok": False, "reason": "recovering"}
            queue = self.engine.observatory.getReportQueue()
            if queue.is_empty():
                return {"ok": False, "reason": "empty_queue"}

            observatory = self.engine.observatory
            before_version = observatory.toVersion()
            before_indicators = self.engine.service.metrics_service.capture_display(observatory)
            report_position = 1
            report = queue.dequeue()
            observatory.begin_visual_operation()
            try:
                result = self.processor.apply(observatory, report, self.engine.service.metrics_service)
            finally:
                result_steps = observatory.finish_visual_operation()
            result.steps = result_steps
            result.rotations = [
                step.get("rotation", {}).get("type")
                for step in result_steps
                if step.get("kind") == "rotation"
            ]

            metrics_service = self.engine.service.metrics_service
            metrics_service.refresh_derived_metrics(observatory)
            metrics_service.register_rotation_steps(observatory.getMetrics(), result_steps)
            metrics_service.record_operation(
                observatory=observatory,
                action_type="queue_step",
                before_version=before_version,
                before_indicators=before_indicators,
                details={
                    "event_id": result.event_id,
                    "revision": result.revision,
                    "station_id": result.station_id,
                    "decision": result.decision,
                    "reason": result.reason,
                    "rotations": result.rotations,
                    "report_position": report_position,
                },
            )
            self.engine.service.saveObservatory(observatory)

            event = observatory.searchEventById(result.event_id) if result.tree_changed else None
            if result.tree_changed:
                self.engine.sequence += 1
                tree_payload = {
                    "scenarioId": self.engine.scenario_id,
                    "sequence": self.engine.sequence,
                    "mode": observatory.getExecutionMode(),
                    "stationId": result.station_id,
                    "event": event.toDict() if event is not None else None,
                    "steps": result.steps,
                }
            else:
                tree_payload = None
            remaining = queue.size()
            step_payload = {
                "decision": result.decision,
                "reason": result.reason,
                "eventId": result.event_id,
                "revision": result.revision,
                "stationId": result.station_id,
                "rotations": result.rotations,
                "remaining": remaining,
            }
            snapshot = self.queue_service.snapshot(observatory)

        if tree_payload is not None:
            self.engine.socketio.emit("tree:operation", tree_payload)
        self.engine.socketio.emit("queue:step", step_payload)
        self.engine.socketio.emit("queue:updated", snapshot)
        return {"ok": True, **step_payload}

    def start_continuous(self):
        with self.engine.lock:
            if self._running:
                return {"ok": False, "reason": "already_running"}
            if self.engine.observatory is None:
                return {"ok": False, "reason": "no_scenario"}
            self._running = True
            self._paused = False
        self.engine.socketio.start_background_task(self._run)
        return {"ok": True}

    def _run(self):
        try:
            while True:
                if self._paused:
                    self.engine.socketio.emit("queue:paused", {"reason": "paused"})
                    return
                result = self.process_next()
                if result.get("reason") in ("empty_queue", "no_scenario"):
                    return
                if result.get("reason") == "recovering":
                    self.engine.socketio.emit("queue:paused", {"reason": "recovering"})
                    return
                self.engine.socketio.sleep(self.interval)
        finally:
            self._running = False

    def pause(self):
        self._paused = True
        return {"ok": True, "reason": "paused"}

    def pause_for_recovery(self):
        self._paused = True
        return {"ok": True, "reason": "recovering"}

    def resume(self):
        self._paused = False
        return self.start_continuous()

    def is_running(self):
        return self._running

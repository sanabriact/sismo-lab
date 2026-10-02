import queue
import threading
import time
from datetime import timedelta
from backend.models.seismic_observatory import SeismicObservatory
from backend.services.reports.report_processor import ReportProcessor
from backend.services.reports.report_queue_service import ReportQueueService
from backend.services.seismic_observatory_service import ScenarioValidationError
from backend.services.archive.archive_tree_service import ArchiveTreeService
from backend.services.actions.action_stack_service import ActionStackError, ActionStackService

class EventEngine:
    """
    Central coordinator for scenario, event, and report-queue operations.

    The engine owns synchronization, lifecycle state, persistence boundaries,
    metrics updates, and outbound notifications. Other layers only adapt
    transport requests to these engine methods.
    """

    def __init__(self, socketio, service, mode_changed, stress_mode_manager):
        self.socketio = socketio
        self.service = service
        self.mode_changed = mode_changed
        self.stress_mode_manager = stress_mode_manager
        self.observatory = None
        self.events = queue.Queue()
        self.lock = threading.Lock()
        self.paused = False
        self.recovering = False
        self.sequence = 0
        self.scenario_id = None
        self.report_queue_service = ReportQueueService()
        self.report_processor = ReportProcessor()
        self.archive_tree_service = ArchiveTreeService()
        self.action_stack_service = ActionStackService()
        if hasattr(self.service, "metrics_service"):
            self.service.metrics_service.action_stack_service = self.action_stack_service
        self.report_queue_interval = 1.5
        self.report_queue_running = False
        self.report_queue_paused = False
        self.scenario_manager = None
        self.scenario_validator = None
        self.scenario_loaded = None
        self._recovery_before_version = 0
        self._recovery_before_indicators = {}
        self.clock_realtime_interval = 1.0
        self.clock_realtime_running = False
        self._clock_realtime_anchor_monotonic = None
        self._clock_realtime_anchor_time = None

    def set_scenario_manager(self, manager):
        """Register the manager that prepares the generator after a load."""
        self.scenario_manager = manager

    def set_scenario_validator(self, validator):
        """Register the manager that validates uploaded scenario content."""
        self.scenario_validator = validator

    def set_scenario_loaded_notifier(self, notifier):
        """Register the event-bus callback used after a scenario is activated."""
        self.scenario_loaded = notifier

    def set_observatory(self, observatory):
        """Replace the active scenario and reset its event sequence."""
        with self.lock:
            self._stop_realtime_clock_locked()
            self.observatory = observatory
            self.sequence = 0
            self.scenario_id = observatory.scenario_id

    def get_observatory(self):
        """Return the active scenario without loading or mutating state."""
        return self.observatory

    def get_or_load_observatory(self):
        """Return the active scenario, falling back to the repository once."""
        with self.lock:
            if self.observatory is None:
                self.observatory = self.service.getObservatory()
                self.scenario_id = self.observatory.scenario_id
                self._start_realtime_clock_locked()
            return self.observatory
    
    def get_active_events(self):
        observatory = self.get_or_load_observatory()
        with self.lock:
            return {
                "events": self.service.getActiveEvents(observatory)
            }

    def prepare_archive_tree(self, threshold_hours=None, client_id=None):
        """Select and preview an archivable branch without changing the AVL."""
        with self.lock:
            if self.observatory is None:
                return {"ok": False, "reason": "no_scenario"}
            if self.recovering:
                return {"ok": False, "reason": "busy"}
            threshold = self.observatory.t if threshold_hours is None else threshold_hours
            actual_time = self.observatory.getClock().getCurrentTime()
            return self.archive_tree_service.prepare(
                self.observatory, actual_time, threshold, client_id
            )

    def decide_archive_tree(self, archive, client_id=None):
        """Apply a client's pending archive decision as one locked action."""
        with self.lock:
            if self.observatory is None:
                return {"ok": False, "reason": "no_scenario"}
            if self.recovering:
                return {"ok": False, "reason": "busy"}
            before_version = self.observatory.toVersion()
            before_indicators = self.service.metrics_service.capture_display(self.observatory)
            result = self.archive_tree_service.decide(
                self.observatory, archive, client_id
            )
            if not result.get("ok") or not result.get("archived"):
                return result

            metrics = self.observatory.getMetrics()
            metrics.incrementMassArchives()
            for _ in result["subtree"]["affected_ids"]:
                metrics.incrementArchivedEvents()
            self.service.metrics_service.refresh_derived_metrics(self.observatory)
            self.service.metrics_service.record_operation(
                observatory=self.observatory,
                action_type="mass_archive",
                before_version=before_version,
                before_indicators=before_indicators,
                details={"root_id": result["subtree"]["root_id"],
                         "affected_ids": result["subtree"]["affected_ids"]},
            )
            self.service.saveObservatory(self.observatory)
            return result

    def clock_snapshot(self):
        """Return the active simulation clock in the public UTC format."""
        if self.observatory is None:
            return None
        return {
            "scenarioId": self.scenario_id,
            "currentTime": self.observatory.getClock().getCurrentTimeText(),
        }

    def advance_clock_hours(self, hours):
        """Advance the simulation clock and persist the resulting action."""
        with self.lock:
            if self.observatory is None:
                return {"ok": False, "reason": "no_scenario"}
            if self.recovering:
                return {"ok": False, "reason": "busy"}

            before_version = self.observatory.toVersion()
            before_indicators = self.service.metrics_service.capture_display(
                self.observatory
            )
            current_time = self.observatory.getClock().advanceHours(hours)
            self._reset_realtime_anchor_locked(current_time)
            self.service.metrics_service.refresh_derived_metrics(self.observatory)
            self.service.metrics_service.record_operation(
                observatory=self.observatory,
                action_type="advance_clock",
                before_version=before_version,
                before_indicators=before_indicators,
                details={"hours": float(hours)},
            )
            self.service.saveObservatory(self.observatory)
            payload = {
                "scenarioId": self.scenario_id,
                "currentTime": self.observatory.getClock().getCurrentTimeText(),
            }

        self.socketio.emit("clock:updated", payload)
        return {"ok": True, "clock": payload, "currentTime": current_time.isoformat()}

    def advance_clock_to(self, moment):
        """Advance the simulation clock to a later absolute UTC instant."""
        with self.lock:
            if self.observatory is None:
                return {"ok": False, "reason": "no_scenario"}
            if self.recovering:
                return {"ok": False, "reason": "busy"}

            before_version = self.observatory.toVersion()
            before_indicators = self.service.metrics_service.capture_display(
                self.observatory
            )
            current_time = self.observatory.getClock().advanceTo(moment)
            self._reset_realtime_anchor_locked(current_time)
            self.service.metrics_service.refresh_derived_metrics(self.observatory)
            self.service.metrics_service.record_operation(
                observatory=self.observatory,
                action_type="advance_clock_to",
                before_version=before_version,
                before_indicators=before_indicators,
                details={"target": self.observatory.getClock().getCurrentTimeText()},
            )
            self.service.saveObservatory(self.observatory)
            payload = {
                "scenarioId": self.scenario_id,
                "currentTime": self.observatory.getClock().getCurrentTimeText(),
            }

        self.socketio.emit("clock:updated", payload)
        return {"ok": True, "clock": payload, "currentTime": current_time.isoformat()}

    def load_scenario_from_text(self, content):
        """Validate, build, activate and persist a text-based scenario."""
        previous = self.observatory
        previous_snapshot = self._snapshot_for_load(previous)
        with self.lock:
            if self.scenario_validator is not None:
                validated = self.scenario_validator.loadFromText(content, stress_mode=False)
                if validated is None:
                    raise ScenarioValidationError(self.scenario_validator.errors)
            observatory = self.service.loadScenarioFromText(content)

        if self.scenario_manager is not None:
            self.scenario_manager.load_scenario(observatory)
        else:
            self.set_observatory(observatory)
        self._announce_scenario_loaded(observatory)
        self._record_loaded_scenario(observatory, previous_snapshot)
        return observatory

    def create_event_from_api(self, data):
        """Create a manual event while keeping the active state in the engine."""
        try:
            operation = self.create_manual_event(data)
        except ValueError as error:
            return {"success": False, "reason": str(error)}
        return {"success": True, "event": operation["event"]}

    def load_scenario_from_ai(self, ai_mode):
        """Build, activate and persist an AI-provided scenario."""
        previous = self.observatory
        previous_snapshot = self._snapshot_for_load(previous)
        with self.lock:
            observatory = self.service.loadScenarioFromAI(ai_mode)
        if self.scenario_manager is not None:
            self.scenario_manager.load_scenario(observatory)
        else:
            self.set_observatory(observatory)
        self._announce_scenario_loaded(observatory)
        self._record_loaded_scenario(observatory, previous_snapshot)
        return observatory

    def undo_action(self):
        """Undo the latest completed operation through the action service."""
        with self.lock:
            if self.observatory is None:
                return {"ok": False, "reason": "no_scenario"}
            if self.recovering:
                return {"ok": False, "reason": "busy"}

            try:
                restored, action = self.action_stack_service.undo(self.observatory)
            except ActionStackError as error:
                return {"ok": False, "reason": str(error)}

            self.observatory = restored
            self.scenario_id = restored.scenario_id
            if self.scenario_id is None:
                self._stop_realtime_clock_locked()
            else:
                self._reset_realtime_anchor_locked(restored.getClock().getCurrentTime())
            if self.scenario_manager is not None:
                self.scenario_manager.stop()
                self.scenario_manager.stations = restored.getStations()
                self.scenario_manager.current_index = 0
                self.scenario_manager.event_count = 0
            self.service.metrics_service.refresh_derived_metrics(restored)
            self.service.saveObservatory(restored)
            payload = {
                "scenarioId": self.scenario_id,
                "actionType": action.getActionType(),
                "currentTime": restored.getClock().getCurrentTimeText(),
                "events": len(restored.getAVLTree().index),
                "remaining": self.action_stack_service.size(restored),
            }

        self.socketio.emit("action:undone", payload)
        self.socketio.emit("queue:updated", self.report_queue_service.snapshot(restored))
        return {"ok": True, "action": action.toDict(), "snapshot": payload}

    def audit_structure(self):
        """Audit the active scenario through the engine lock."""
        with self.lock:
            if self.observatory is None:
                return {"ok": False, "reason": "no_scenario"}
            return {"ok": True, "report": self.service.auditStructure(self.observatory)}

    def prepare_reports(self, raw_reports):
        """Validate and enqueue a complete report batch atomically."""
        with self.lock:
            if self.observatory is None:
                return {"ok": False, "reason": "no_scenario", "enqueued": 0, "issues": []}
            result = self.report_queue_service.prepare(self.observatory, raw_reports)
            if result["ok"]:
                self.service.saveObservatory(self.observatory)
            snapshot = self.report_queue_service.snapshot(self.observatory)
        self.socketio.emit("queue:updated", snapshot)
        return {**result, "snapshot": snapshot}

    def process_report_step(self):
        """Process exactly one queued report while owning the full lifecycle."""
        with self.lock:
            if self.observatory is None:
                return {"ok": False, "reason": "no_scenario"}
            if self.recovering:
                return {"ok": False, "reason": "recovering"}
            report_queue = self.observatory.getReportQueue()
            if report_queue.is_empty():
                return {"ok": False, "reason": "empty_queue"}

            before_version = self.observatory.toVersion()
            before_indicators = self.service.metrics_service.capture_display(self.observatory)
            report = report_queue.dequeue()
            self.observatory.begin_visual_operation()
            try:
                result = self.report_processor.apply(
                    self.observatory,
                    report,
                    self.service.metrics_service,
                )
            finally:
                result_steps = self.observatory.finish_visual_operation()

            result.steps = result_steps
            result.rotations = [
                step.get("rotation", {}).get("type")
                for step in result_steps
                if step.get("kind") == "rotation"
            ]
            metrics_service = self.service.metrics_service
            metrics_service.refresh_derived_metrics(self.observatory)
            metrics_service.register_rotation_steps(self.observatory.getMetrics(), result_steps)
            metrics_service.record_operation(
                observatory=self.observatory,
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
                    "report_position": 1,
                },
            )
            self.service.saveObservatory(self.observatory)

            event = self.observatory.searchEventById(result.event_id) if result.tree_changed else None
            tree_payload = None
            if result.tree_changed:
                self.sequence += 1
                tree_payload = {
                    "scenarioId": self.scenario_id,
                    "sequence": self.sequence,
                    "mode": self.observatory.getExecutionMode(),
                    "stationId": result.station_id,
                    "event": event.toDict() if event is not None else None,
                    "steps": result.steps,
                }

            step_payload = {
                "decision": result.decision,
                "reason": result.reason,
                "eventId": result.event_id,
                "revision": result.revision,
                "stationId": result.station_id,
                "rotations": result.rotations,
                "remaining": report_queue.size(),
            }
            snapshot = self.report_queue_service.snapshot(self.observatory)

        if tree_payload is not None:
            self.socketio.emit("tree:operation", tree_payload)
        self.socketio.emit("queue:step", step_payload)
        self.socketio.emit("queue:updated", snapshot)
        return {"ok": True, **step_payload}

    def start_report_processing(self):
        """Start one background queue loop owned by the engine."""
        with self.lock:
            if self.report_queue_running:
                return {"ok": False, "reason": "already_running"}
            if self.observatory is None:
                return {"ok": False, "reason": "no_scenario"}
            self.report_queue_running = True
            self.report_queue_paused = False
        self.socketio.start_background_task(self._run_report_queue)
        return {"ok": True}

    def _run_report_queue(self):
        try:
            while not self.report_queue_paused:
                result = self.process_report_step()
                if result.get("reason") in ("empty_queue", "no_scenario"):
                    return
                if result.get("reason") == "recovering":
                    self.socketio.emit("queue:paused", {"reason": "recovering"})
                    return
                self.socketio.sleep(self.report_queue_interval)
        finally:
            self.report_queue_running = False

    def pause_report_processing(self, reason="paused"):
        """Pause processing without changing the reports already queued."""
        self.report_queue_paused = True
        return {"ok": True, "reason": reason}

    def resume_report_processing(self):
        self.report_queue_paused = False
        return self.start_report_processing()

    def report_queue_snapshot(self):
        """Return a serialized queue snapshot under the engine lock."""
        with self.lock:
            if self.observatory is None:
                return {"ok": False, "reason": "no_scenario"}
            return self.report_queue_service.snapshot(self.observatory)

    def enqueue(self, station, data):
        """Queue one generated event for the engine's background worker."""
        if self.observatory is None:
            return
            
        self.events.put({
            "scenario_id": self.scenario_id,
            "station": station,
            "data": data,
        })

    def start(self):
        """Start the long-lived generated-event worker."""
        self.socketio.start_background_task(self.run)

    def run(self):
        """Consume generated events and publish the resulting tree operation."""
        while True:
            candidate = self.events.get()
            if candidate.get("scenario_id") != self.scenario_id:
                continue
            
            while self.paused:
                self.socketio.sleep(0.2)

            try:
                with self.lock:
                    operation = self.service.createGeneratedEvent(
                        self.observatory,
                        candidate["station"],
                        candidate["data"],
                    )

                    self.sequence += 1
                    operation["scenarioId"] = self.scenario_id
                    operation["sequence"] = self.sequence

                self.socketio.emit("tree:operation", operation)

            except Exception as error:
                self.emit_error(candidate["station"], str(error))

    def emit_error(self, station, message):
        """Publish a generation error associated with one station."""
        self.socketio.emit("tree:generation-error", {
            "scenarioId": self.scenario_id,
            "stationId": station.id,
            "message": message,
        })

    def create_manual_event(self, data):
        """Create one manual event atomically and publish its tree patch."""
        with self.lock:
            if self.observatory is None:
                raise ValueError("No hay un escenario cargado")
            if self.recovering:
                raise ValueError("La estructura se está recuperando; inténtalo de nuevo")

            operation = self.service.createManualEvent(self.observatory, data)
            self.sequence += 1
            operation["scenarioId"] = self.scenario_id
            operation["sequence"] = self.sequence

        self.socketio.emit("tree:operation", operation)
        return operation
    
    # Method for returning a event by searching first in the observatory and then converting it in a dict instance
    def get_active_event(self, event_id):
        observatory = self.get_or_load_observatory()
        with self.lock:
            event = observatory.searchEventById(event_id)
            if event is None:
                return None
            return event.toDict()

    # Method for updating manual events
    def update_manual_event(self, data):
        # Lock the update process to avoid simultaneous changes to the same data.
        with self.lock:
            # An event can only be updated when a scenario is loaded.
            if self.observatory is None:
                return {
                    "ok": False,
                    "reason": "no_scenario"
                }

            # Do not allow updates while the tree is being recovered.
            if self.recovering:
                return {
                    "ok": False,
                    "reason": "busy"
                }

            # Read and validate the immutable event ID sent by the client.
            event_id = data.get("event_id")
            if isinstance(event_id, bool) or not isinstance(event_id, int):
                return {
                    "ok": False,
                    "reason": "invalid_event_id"
                }

            # The event must still be active in the observatory.
            event = self.observatory.searchEventById(event_id)
            if event is None:
                return {
                    "ok": False,
                    "reason": "event_not_found"
                }

            try:
                # Build and validate the report for this correction.
                report = self.service.build_manual_update_report(
                    self.observatory,
                    event_id,
                    data
                )
            except ValueError as error:
                return {
                    "ok": False,
                    "reason": str(error)
                }

            # Save the current state before changing anything.
            # This allows the action to be undone later.
            before_version = self.observatory.toVersion()
            before_indicators = self.service.metrics_service.capture_display(
                self.observatory
            )
            queue = self.observatory.getReportQueue()

            # Keep a tree notification only when the event key changes.
            tree_operation = None

            # Keep FIFO order when reports are already pending.
            if not queue.is_empty():
                self.observatory.enqueueReport(report)

                # Save the queue change in the undo stack.
                self.service.metrics_service.record_operation(
                    observatory=self.observatory,
                    action_type="updated_event",
                    before_version=before_version,
                    before_indicators=before_indicators,
                    details={
                        "event_id": event_id,
                        "revision": report.getRevision(),
                        "queued": True
                    }
                )

                self.service.saveObservatory(self.observatory)
                snapshot = self.report_queue_service.snapshot(self.observatory)

                response = {
                    "ok": True,
                    "queued": True,
                    "revision": report.getRevision(),
                    "snapshot": snapshot
                }

            # Apply the correction immediately when the queue is empty.
            else:
                self.observatory.begin_visual_operation()
                try:
                    result = self.report_processor.apply(
                        self.observatory,
                        report
                    )
                finally:
                    # Always close the visual operation.
                    steps = self.observatory.finish_visual_operation()

                if result.decision != "updated":
                    return {
                        "ok": False,
                        "reason": result.reason,
                        "decision": result.decision
                    }

                self.service.metrics_service.refresh_derived_metrics(
                    self.observatory
                )
                self.service.metrics_service.register_rotation_steps(
                    self.observatory.getMetrics(),
                    steps
                )

                # Save the state before the direct update for undo.
                self.service.metrics_service.record_operation(
                    observatory=self.observatory,
                    action_type="updated_event",
                    before_version=before_version,
                    before_indicators=before_indicators,
                    details={
                        "event_id": event_id,
                        "revision": report.getRevision(),
                        "queued": False,
                        "key_changed": result.tree_changed
                    }
                )

                self.service.saveObservatory(self.observatory)
                snapshot = self.report_queue_service.snapshot(self.observatory)

                response = {
                    "ok": True,
                    "queued": False,
                    "revision": report.getRevision(),
                    "event": event.toDict(),
                    "snapshot": snapshot
                }

                # Build the tree notification only if the key changed.
                if result.tree_changed:
                    self.sequence += 1
                    tree_operation = {
                        "scenarioId": self.scenario_id,
                        "sequence": self.sequence,
                        "mode": self.observatory.getExecutionMode(),
                        "stationId": report.getStation().getId(),
                        "event": event.toDict(),
                        "steps": steps,
                    }

        # Emit Socket.IO events after releasing the lock.
        if tree_operation is not None:
            self.socketio.emit("tree:operation", tree_operation)

        self.socketio.emit("queue:updated", snapshot)
        self.socketio.emit("event:updated", {
            "eventId": event_id,
            "queued": response["queued"]
        })

        return response
    
    def mark_event_as_reviewed(self, event_id):
        with self.lock:
            if self.observatory is None:
                return {
                    "ok": False, 
                    "reason": "no_scenario"
                }

            if self.recovering:
                return {
                    "ok": False, 
                    "reason": "busy"
                }

            event = self.observatory.searchEventById(event_id)
            if event is None:
                return {
                    "ok": False, 
                    "reason": "event_not_found"
                }

            # No registrar una acción si no hay cambio real.
            if event.getAttentionStatus() == "reviewed":
                return {
                    "ok": True,
                    "changed": False,
                    "event": event.toDict(),
                }

            # 1. Guardar el estado ANTES del cambio.
            before_version = self.observatory.toVersion()
            before_indicators = self.service.metrics_service.capture_display(
                self.observatory
            )
            previous_status = event.getAttentionStatus()

            # 2. Ejecutar la operación.
            event.setAttentionStatus("reviewed")

            # 3. Recalcular indicadores y registrar la acción exitosa.
            self.service.metrics_service.refresh_derived_metrics(self.observatory)
            self.service.metrics_service.record_operation(
                observatory=self.observatory,
                action_type="mark_reviewed",
                before_version=before_version,
                before_indicators=before_indicators,
                details={
                    "event_id": event_id,
                    "previous_attention_status": previous_status,
                    "new_attention_status": "reviewed",
                },
            )

            # 4. Persistir tanto el cambio como la pila de acciones.
            self.service.saveObservatory(self.observatory)

            return {
                "ok": True,
                "changed": True,
                "event": event.toDict(),
            }
            
    # ===================== Execution mode (normal / stress) =====================

    def announce_mode(self):
        """Publish the current execution mode and tree-balance report."""
        with self.lock:
            if self.observatory is None:
                return
            report = self.service.auditBalance(self.observatory)
            mode = self.observatory.getExecutionMode()
        self._notify_mode(report, mode, "changed")

    def request_mode(self, mode):
        """
        Handle a frontend "mode:set" request and return its acknowledgement:
        {"ok": bool, "reason"?: str, "mode"?: str}.

        - Switching to stress mode is immediate.
        - Returning to normal mode requires background AVL recovery, with the
          result published through "mode:changed".
        """
        if mode not in ("normal", "stress"):
            return {"ok": False, "reason": "invalid_mode"}

        with self.lock:
            if self.observatory is None:
                return {"ok": False, "reason": "no_scenario"}

            if self.recovering:
                return {"ok": False, "reason": "busy"}

            current = self.observatory.getExecutionMode()
            if mode == current:
                return {"ok": True, "mode": current}

            if mode == "stress":
                before_version = self.observatory.toVersion()
                before_indicators = self.service.metrics_service.capture_display(
                    self.observatory
                )
                report = self.stress_mode_manager.activateStressMode(
                    self.observatory
                )
                self.service.saveObservatory(self.observatory)
                self._notify_mode(report, "stress", "changed")
                return {"ok": True, "mode": "stress"}

            # Pause both workers before recovering the tree in the background.
            self._recovery_before_version = self.observatory.toVersion()
            self._recovery_before_indicators = self.service.metrics_service.capture_display(
                self.observatory
            )
            self.recovering = True
            self.paused = True
            self.pause_report_processing("recovering")
            report = self.service.auditBalance(self.observatory)
            self._notify_mode(report, "stress", "recovering")

        self.socketio.start_background_task(self._recover)
        return {"ok": True, "mode": "stress"}

    def _recover(self):
        try:
            with self.lock:
                report = self.stress_mode_manager.deactivateStressMode(
                    self.observatory
                )
                self.service.metrics_service.refresh_derived_metrics(
                    self.observatory
                )
                self.service.metrics_service.register_rotation_steps(
                    self.observatory.getMetrics(),
                    report["steps"],
                )
                self.service.metrics_service.record_operation(
                    observatory=self.observatory,
                    action_type="recover_avl_balance",
                    before_version=self._recovery_before_version,
                    before_indicators=self._recovery_before_indicators,
                    details={
                        "mode_before": "stress",
                        "mode_after": self.observatory.getExecutionMode(),
                    },
                )
                self.service.saveObservatory(self.observatory)
                steps = report["steps"]
                payload = None

                if len(steps) > 0:
                    self.sequence += 1
                    payload = {
                        "scenarioId": self.scenario_id,
                        "sequence": self.sequence,
                        "mode": report["mode"],
                        "stationId": None,
                        "event": None,
                        "steps": steps,
                    }

            # The tree may have changed even when the audit reports failure.
            if payload is not None:
                self.socketio.emit("tree:operation", payload)

            status = "changed" if report["ok"] else "failed"
            self._notify_mode(report, report["mode"], status)

        except Exception as error:
            self.mode_changed.notify({
                "mode": "stress",
                "status": "failed",
                "balanced": False,
                "maxImbalance": 0,
                "rotations": 0,
                "issues": [str(error)],
            })

        finally:
            self.paused = False
            self.recovering = False
            self.resume_report_processing()

    def _notify_mode(self, report, mode, status):
        self.mode_changed.notify({
            "mode": mode,
            "status": status,
            "balanced": report["balanced"],
            "maxImbalance": report["maxImbalance"],
            "rotations": report.get("rotations", 0),
            "issues": report["issues"],
        })

    def _snapshot_for_load(self, observatory):
        """Capture the previous scenario when a load can be undone."""
        if observatory is None:
            empty = SeismicObservatory()
            snapshot = empty.toVersion()
            snapshot["scenario_id"] = None
            snapshot["action_stack"] = empty.getActionStack().toDict()
            snapshot["saved_versions"] = empty.getSavedVersions()
            return snapshot

        snapshot = observatory.toVersion()
        snapshot["scenario_id"] = observatory.getScenarioId()
        snapshot["action_stack"] = observatory.getActionStack().toDict()
        snapshot["saved_versions"] = observatory.getSavedVersions()
        return snapshot

    def _record_loaded_scenario(self, observatory, previous_snapshot):
        """Record a successful scenario replacement as one atomic action."""
        with self.lock:
            self.action_stack_service.record_action(
                observatory,
                "LOAD_SCENARIO",
                previous_snapshot,
                {"source": "scenario_load"},
            )
            if hasattr(self.service, "saveObservatory"):
                self.service.saveObservatory(observatory)

    def _announce_scenario_loaded(self, observatory):
        """Publish scenario activation from the engine, after all state is ready."""
        with self.lock:
            self._start_realtime_clock_locked()
        payload = {
            "scenarioId": observatory.scenario_id,
            "mode": observatory.getExecutionMode(),
            "stations": len(observatory.getStations()),
            "events": len(observatory.getAVLTree().index),
            "currentTime": observatory.getClock().getCurrentTimeText(),
        }
        if self.scenario_loaded is not None:
            self.scenario_loaded.notify(payload)
        self.announce_mode()

    # ------------------------------------------------------------------
    # Real-time simulation clock
    # ------------------------------------------------------------------

    def _start_realtime_clock_locked(self):
        """Start the authoritative clock loop after a scenario is available."""
        if self.observatory is None or self.clock_realtime_running:
            return

        self.clock_realtime_running = True
        self._clock_realtime_anchor_monotonic = time.monotonic()
        self._clock_realtime_anchor_time = self.observatory.getClock().getCurrentTime()
        self.socketio.start_background_task(self._run_realtime_clock)

    def _stop_realtime_clock_locked(self):
        """Stop the clock loop before replacing the active scenario."""
        self.clock_realtime_running = False
        self._clock_realtime_anchor_monotonic = None
        self._clock_realtime_anchor_time = None

    def _reset_realtime_anchor_locked(self, current_time):
        """Continue real-time progression from a manually selected instant."""
        self._clock_realtime_anchor_monotonic = time.monotonic()
        self._clock_realtime_anchor_time = current_time

    def _run_realtime_clock(self):
        """Advance and broadcast the simulation clock once per real second."""
        while True:
            self.socketio.sleep(self.clock_realtime_interval)

            with self.lock:
                if not self.clock_realtime_running or self.observatory is None:
                    return

                elapsed_seconds = int(
                    time.monotonic() - self._clock_realtime_anchor_monotonic
                )
                target_time = self._clock_realtime_anchor_time + timedelta(
                    seconds=elapsed_seconds
                )
                clock = self.observatory.getClock()

                if target_time <= clock.getCurrentTime():
                    continue

                clock.advanceTo(target_time)
                self.service.metrics_service.refresh_derived_metrics(self.observatory)
                self.service.saveObservatory(self.observatory)
                payload = {
                    "scenarioId": self.scenario_id,
                    "currentTime": clock.getCurrentTimeText(),
                }

            self.socketio.emit("clock:updated", payload)

import queue
import threading
from backend.models.seismic_observatory import SeismicObservatory
from backend.services.reports.report_processor import ReportProcessor
from backend.services.reports.report_queue_service import ReportQueueService
from backend.services.reports.report_processing_service import ReportProcessingService
from backend.services.archive.archive_tree_service import ArchiveTreeService
from backend.services.actions.action_stack_service import ActionStackError, ActionStackService
from backend.services.query.query_service import QueryService
from backend.services.history.history_service import HistoryService
from backend.services.parameters.scenario_parameters_service import ScenarioParametersService
from backend.services.ai_client.ai_report_service import AIReportService
from backend.services.scenario.scenario_load_service import ScenarioLoadService
from backend.services.clock.realtime_clock_service import RealtimeClockService
from backend.services.events.event_lifecycle_service import EventLifecycleService
from backend.services.mode.execution_mode_service import ExecutionModeService

class EventEngine:
    """
    Central coordinator for scenario, event, and report-queue operations.

    The engine owns synchronization, lifecycle state, persistence boundaries,
    metrics updates, and outbound notifications. Other layers only adapt
    transport requests to these engine methods.
    """

    def __init__(self, socketio, service, mode_changed, stress_mode_manager, parameters_service=None):
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
        self.report_processing_service = ReportProcessingService(
            self.report_queue_service,
            self.report_processor,
        )
        self.event_lifecycle_service = EventLifecycleService(
            service,
            self.report_processor,
            self.report_queue_service,
        )
        self.execution_mode_service = ExecutionModeService(
            stress_mode_manager,
            getattr(self.service, "metrics_service", None),
        )
        self.ai_report_service = AIReportService()
        self.archive_tree_service = ArchiveTreeService()
        self.action_stack_service = ActionStackService()
        # The engine owns the query service just like the other domain services.
        self.query_service = QueryService()
        self.history_service = HistoryService()
        self.parameters_service = parameters_service or ScenarioParametersService()
        self.query_service.parameters_service = self.parameters_service
        if hasattr(self.service, "metrics_service"):
            self.service.metrics_service.action_stack_service = self.action_stack_service
        self.report_queue_interval = 1.5
        self.report_queue_running = False
        self.report_queue_paused = False
        self.scenario_manager = None
        self.scenario_load_service = ScenarioLoadService(
            service,
            self.parameters_service,
        )
        self.scenario_loaded = None
        self.ai_generation_loop = None
        self._recovery_before_version = 0
        self._recovery_before_indicators = {}
        # The service owns automatic clock progression; the engine still
        # coordinates locks, actions, persistence, and public responses.
        self.clock_service = RealtimeClockService(
            socketio=socketio,
            lock=self.lock,
            get_observatory=self.get_observatory,
            get_scenario_id=lambda: self.scenario_id,
            save_observatory=self._save_observatory,
            refresh_metrics=self._refresh_clock_metrics,
        )

    def set_scenario_manager(self, manager):
        """Register the manager that prepares the generator after a load."""
        self.scenario_manager = manager

    def set_scenario_validator(self, validator):
        """Register the manager that validates uploaded scenario content."""
        self.scenario_load_service.set_validator(validator)

    def set_scenario_loaded_notifier(self, notifier):
        """Register the event-bus callback used after a scenario is activated."""
        self.scenario_loaded = notifier

    def set_ai_generation_loop(self, generation_loop):
        """Register the worker used by the continuous AI report generator."""
        self.ai_generation_loop = generation_loop

    def set_observatory(self, observatory):
        """Replace the active scenario and reset its event sequence."""
        with self.lock:
            self._stop_realtime_clock_locked()
            self.observatory = observatory
            self._load_parameters_from_observatory(observatory)
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
                self._load_parameters_from_observatory(self.observatory)
                self.scenario_id = self.observatory.scenario_id
                self._start_realtime_clock_locked()
            return self.observatory

    def _load_parameters_from_observatory(self, observatory):
        """Hydrate the shared parameter service from persisted scenario values."""
        self.parameters_service.update({
            "L": observatory.getL(),
            "W": observatory.getAssociationManager().getW(),
            "R": observatory.getAssociationManager().getR(),
            "T": observatory.getT(),
        })

    def _complete_operation(
        self,
        observatory,
        action_type,
        before_version,
        before_indicators,
        details=None,
        steps=None,
    ):
        """Apply the common post-operation metrics, action, and save steps."""
        metrics_service = getattr(self.service, "metrics_service", None)
        if metrics_service is not None:
            metrics_service.refresh_derived_metrics(observatory)
            if steps is not None:
                metrics_service.register_rotation_steps(
                    observatory.getMetrics(),
                    steps,
                )
            metrics_service.record_operation(
                observatory=observatory,
                action_type=action_type,
                before_version=before_version,
                before_indicators=before_indicators,
                details=details or {},
            )
        self._save_observatory(observatory)

    def _save_observatory(self, observatory):
        """Persist the active state through the service boundary."""
        save_method = getattr(self.service, "saveObservatory", None)
        if callable(save_method):
            return save_method(observatory)
        return False

    def _refresh_clock_metrics(self, observatory):
        """Refresh derived indicators after automatic clock progression."""
        metrics_service = getattr(self.service, "metrics_service", None)
        if metrics_service is not None:
            metrics_service.refresh_derived_metrics(observatory)

    @property
    def clock_realtime_running(self):
        """Expose the clock worker state for existing callers."""
        return self.clock_service.running

    def get_parameters(self):
        observatory = self.get_or_load_observatory()
        with self.lock:
            self._load_parameters_from_observatory(observatory)
            return {"ok": True, **self.parameters_service.getAll()}

    def update_parameters(self, data):
        observatory = self.get_or_load_observatory()
        with self.lock:
            if self.recovering:
                return {"ok": False, "reason": "busy"}
            before = self.parameters_service.getAll()
            before_version = observatory.toVersion()
            before_indicators = (
                self.service.metrics_service.capture_display(observatory)
                if hasattr(self.service, "metrics_service") else {}
            )
            try:
                after = self.parameters_service.update(data)
            except (TypeError, ValueError) as error:
                return {"ok": False, "reason": str(error), **before}
            if before == after:
                return {"ok": True, "changed": False, **after}
            observatory.setL(after["L"])
            observatory.setT(after["T"])
            observatory.setAssociationLimits(after["W"], after["R"])
            self._complete_operation(
                observatory,
                "change_parameter",
                before_version,
                before_indicators,
                {"parameters_before": before, "parameters_after": after},
            )
            return {"ok": True, "changed": True, **after}

    def getL(self):
        return self.parameters_service.getL()

    def getW(self):
        return self.parameters_service.getW()

    def getR(self):
        return self.parameters_service.getR()

    def getT(self):
        return self.parameters_service.getT()
    
    def get_active_events(self):
        observatory = self.get_or_load_observatory()
        with self.lock:
            return {
                "events": self.service.getActiveEvents(observatory)
            }

    def get_history_summary(self):
        """Return historical counters through the central application engine."""
        with self.lock:
            if self.observatory is None:
                return {"ok": False, "reason": "no_scenario"}
            return {
                "ok": True,
                **self.history_service.get_summary(self.observatory),
            }

    def get_archived_events(self):
        """Return archived events without changing observatory state."""
        with self.lock:
            if self.observatory is None:
                return {"ok": False, "reason": "no_scenario"}
            events = self.history_service.get_archived_events(self.observatory)
            return {"ok": True, "events": events, "count": len(events)}

    def get_deleted_events(self):
        """Return deleted events through the central application engine."""
        with self.lock:
            if self.observatory is None:
                return {"ok": False, "reason": "no_scenario"}
            events = self.history_service.get_deleted_events(self.observatory)
            return {"ok": True, "events": events, "count": len(events)}

    def get_historical_ids(self):
        """Return the identifiers maintained by the historical index."""
        with self.lock:
            if self.observatory is None:
                return {"ok": False, "reason": "no_scenario"}
            identifiers = self.history_service.get_historical_ids(self.observatory)
            return {"ok": True, "identifiers": identifiers, "count": len(identifiers)}

    def get_association_limits(self):
        """Return the current W and R values without changing the scenario."""
        with self.lock:
            if self.observatory is None:
                return {"ok": False, "reason": "no_scenario"}
            return {"ok": True, "W": self.getW(), "R": self.getR()}

    def update_association_limits(self, data):
        """Compatibility endpoint for clients that only edit association limits."""
        if not isinstance(data, dict):
            return {"ok": False, "reason": "invalid_parameters"}
        return self.update_parameters({key: data[key] for key in ("W", "R") if key in data})

    def execute_query(self, data):
        """Validate the request and delegate the read-only query to QueryService."""
        with self.lock:
            if self.observatory is None:
                return {"ok": False, "reason": "no_scenario"}
            if not isinstance(data, dict):
                return {"ok": False, "reason": "invalid_query"}

            query_type = data.get("type")
            parameters = data.get("parameters", {})
            if not isinstance(parameters, dict):
                return {"ok": False, "reason": "invalid_parameters"}

            try:
                return self.query_service.execute(
                    self.observatory,
                    query_type,
                    parameters,
                )
            except (TypeError, ValueError) as error:
                return {"ok": False, "reason": str(error)}

    def get_tree_characteristics(self):
        """Return height, depth, priority, and costly-access status by tree."""
        with self.lock:
            if self.observatory is None:
                return {"ok": False, "reason": "no_scenario"}
            return self.query_service.tree_characteristics(self.observatory)

    def prepare_archive_tree(self, threshold_hours=None, client_id=None):
        """Select and preview an archivable branch without changing the AVL."""
        with self.lock:
            if self.observatory is None:
                return {"ok": False, "reason": "no_scenario"}
            if self.recovering:
                return {"ok": False, "reason": "busy"}
            threshold = self.getT() if threshold_hours is None else threshold_hours
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
            self._complete_operation(
                self.observatory,
                "mass_archive",
                before_version,
                before_indicators,
                {"root_id": result["subtree"]["root_id"],
                 "affected_ids": result["subtree"]["affected_ids"]},
            )
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
            self._complete_operation(
                self.observatory,
                "advance_clock",
                before_version,
                before_indicators,
                {"hours": float(hours)},
            )
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
            self._complete_operation(
                self.observatory,
                "advance_clock_to",
                before_version,
                before_indicators,
                {"target": self.observatory.getClock().getCurrentTimeText()},
            )
            payload = {
                "scenarioId": self.scenario_id,
                "currentTime": self.observatory.getClock().getCurrentTimeText(),
            }

        self.socketio.emit("clock:updated", payload)
        return {"ok": True, "clock": payload, "currentTime": current_time.isoformat()}

    def load_scenario_from_text(self, content):
        """Validate and build before persisting or activating a new scenario."""
        previous = self.observatory
        previous_snapshot = self._snapshot_for_load(previous)
        with self.lock:
            observatory = self.scenario_load_service.load_text(content)
            self._save_observatory(observatory)

        if self.scenario_manager is not None:
            self.scenario_manager.load_scenario(observatory)
        else:
            self.set_observatory(observatory)
        self._announce_scenario_loaded(observatory)
        self._record_loaded_scenario(observatory, previous_snapshot)
        return observatory

    def pending_count(self):
        """Return the number of reports currently waiting in the FIFO queue."""
        with self.lock:
            if self.observatory is None:
                return 0
            return len(self.observatory.getReportQueue().items)

    def generate_reports_from_ai(self, payload):
        """Generate, validate and enqueue one AI batch through the normal report flow."""
        with self.lock:
            if self.observatory is None:
                return {"ok": False, "reports": [], "issues": ["no_scenario"]}
            scenario_id = self.scenario_id
            context = self.ai_report_service.build_context(self.observatory)

        generation = self.ai_report_service.generate(context, payload)
        if not generation["ok"]:
            return generation

        with self.lock:
            if self.observatory is None or self.scenario_id != scenario_id:
                return {
                    "ok": False,
                    "reports": [],
                    "issues": ["El escenario cambió durante la generación"],
                }

            queue_reports = [self.ai_report_service.normalize(report) for report in generation["reports"]]

        enqueue_result = self.prepare_reports(queue_reports)
        if not enqueue_result.get("ok", False):
            return {
                "ok": False,
                "reports": [],
                "issues": enqueue_result.get("issues", []) + generation["issues"],
            }

        return {
            "ok": True,
            "reports": generation["reports"],
            "issues": generation["issues"],
            "fallback_count": generation["fallback_count"],
            "snapshot": enqueue_result.get("snapshot"),
        }

    def start_ai_report_generation(self, payload=None, minimum_interval=2):
        """Validate AI generation settings and start the report worker."""
        if self.ai_generation_loop is None:
            return {"ok": False, "running": False, "reason": "ai_unavailable"}

        payload = payload if isinstance(payload, dict) else {}
        interval = max(
            minimum_interval,
            float(payload.get("intervalSeconds", 10)),
        )

        with self.lock:
            if self.observatory is None:
                return {
                    "ok": False,
                    "running": self.ai_generation_loop.is_running(),
                    "reason": "no_scenario",
                }

            known_ids = [station.getId() for station in self.observatory.getStations()]
            requested_ids = payload.get("stationIds")
            station_ids = (
                [station_id for station_id in requested_ids if station_id in known_ids]
                if requested_ids
                else known_ids
            )

            if not station_ids:
                return {
                    "ok": False,
                    "running": self.ai_generation_loop.is_running(),
                    "reason": "no_valid_stations",
                }

        started = self.ai_generation_loop.start({
            "interval": interval,
            "station_ids": station_ids,
            "scenario": payload.get("scenario"),
            "seed": int(payload.get("seed", 42)),
        })

        self.socketio.emit("reports:ai_status", {"running": True})
        return {
            "ok": True,
            "running": True,
            "alreadyRunning": not started,
        }

    def stop_ai_report_generation(self):
        """Stop the continuous AI report worker."""
        if self.ai_generation_loop is None:
            return {"ok": False, "running": False, "reason": "ai_unavailable"}

        self.ai_generation_loop.stop()
        self.socketio.emit("reports:ai_status", {"running": False})
        return {"ok": True, "running": False}

    def ai_report_generation_status(self):
        """Return the current state of the continuous AI report worker."""
        if self.ai_generation_loop is None:
            return {"ok": False, "running": False, "reason": "ai_unavailable"}
        return {"ok": True, "running": self.ai_generation_loop.is_running()}

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
            self._load_parameters_from_observatory(restored)
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
            self._save_observatory(restored)
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
            result, snapshot = self.report_processing_service.prepare(
                self.observatory,
                raw_reports,
            )
            if result["ok"]:
                self._save_observatory(self.observatory)
        self.socketio.emit("queue:updated", snapshot)
        return {**result, "snapshot": snapshot}

    def create_manual_report(self, raw_report):
        """Validate and enqueue one report submitted by the manual form."""
        with self.lock:
            if self.observatory is None:
                return {"ok": False, "reason": "no_scenario", "enqueued": 0, "issues": []}

            # Use the same report service as JSON batches so both entry points
            # have identical validation and FIFO behavior.
            result, snapshot = self.report_processing_service.prepare(
                self.observatory,
                [raw_report],
            )
            if result["ok"]:
                self._save_observatory(self.observatory)

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

            step_payload, tree_payload, snapshot = self.report_processing_service.process_one(
                self.observatory,
                self.scenario_id,
                self._complete_operation,
                self._next_sequence,
                self.service.metrics_service,
            )

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

    def _next_sequence(self):
        """Return the next visual operation sequence number."""
        self.sequence += 1
        return self.sequence

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

    # ===================== Tree CRUD operations (with undo options) =====================
    def create_manual_event(self, data):
        """Create one manual event atomically and publish its tree patch."""
        with self.lock:
            if self.observatory is None:
                raise ValueError("No hay un escenario cargado")
            if self.recovering:
                raise ValueError("La estructura se está recuperando; inténtalo de nuevo")

            operation = self.event_lifecycle_service.create_manual_event(
                self.observatory,
                data,
            )
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
        with self.lock:
            if self.observatory is None:
                return {"ok": False, "reason": "no_scenario"}
            if self.recovering:
                return {"ok": False, "reason": "busy"}

            result = self.event_lifecycle_service.update_manual_event(
                self.observatory,
                data,
                self._complete_operation,
                self._save_observatory,
                self.scenario_id,
            )
            response = result["response"]
            if not response.get("ok"):
                return response

            event_id = data["event_id"]
            snapshot = response["snapshot"]
            tree_operation = result["tree_operation"]
            if tree_operation is not None:
                self.sequence += 1
                tree_operation["sequence"] = self.sequence

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

            return self.event_lifecycle_service.mark_reviewed(
                self.observatory,
                event_id,
                self._complete_operation,
            )

    def delete_event_by_id(self, eventId):
        with self.lock:
            if self.observatory is None:
                return {"ok": False, "reason": "no_scenario"}
            if self.recovering:
                return {"ok": False, "reason": "recovering"}
            return self.event_lifecycle_service.delete_event(
                self.observatory,
                eventId,
                self._complete_operation,
            )
      
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
                report = self.execution_mode_service.activate_stress(
                    self.observatory
                )
                self._save_observatory(self.observatory)
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
                report = self.execution_mode_service.recover_normal(
                    self.observatory,
                    self._recovery_before_version,
                    self._recovery_before_indicators,
                )
                self._save_observatory(self.observatory)
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
            return snapshot

        snapshot = observatory.toVersion()
        snapshot["scenario_id"] = observatory.getScenarioId()
        snapshot["action_stack"] = observatory.getActionStack().toDict()
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
            self._save_observatory(observatory)

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
        """Delegate automatic clock startup to the clock service."""
        self.clock_service.start(self._run_realtime_clock)

    def _stop_realtime_clock_locked(self):
        """Delegate automatic clock shutdown to the clock service."""
        self.clock_service.stop()

    def _reset_realtime_anchor_locked(self, current_time):
        """Restart automatic progression from a manually selected instant."""
        self.clock_service.reset_anchor(current_time)

    def _run_realtime_clock(self):
        """Keep the old engine entry point while the service owns the loop."""
        self.clock_service.run()

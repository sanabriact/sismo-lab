import queue
import threading

class EventEngine:
    """
    Motor de eventos en tiempo real.

    Toma los eventos generados, los inserta en el observatorio activo y
    avisa al frontend por WebSocket. No conoce la persistencia: todo lo que
    toca el dominio o el disco pasa por SeismicObservatoryService.
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

    def set_observatory(self, observatory):
        with self.lock:
            self.observatory = observatory
            self.sequence = 0
            self.scenario_id = observatory.scenario_id

    def get_observatory(self):
        return self.observatory

    def enqueue(self, station, data):
        if self.observatory is None:
            return
            
        self.events.put({
            "scenario_id": self.scenario_id,
            "station": station,
            "data": data,
        })

    def start(self):
        self.socketio.start_background_task(self.run)

    def run(self):
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
        self.socketio.emit("tree:generation-error", {
            "scenarioId": self.scenario_id,
            "stationId": station.id,
            "message": message,
        })

    def create_manual_event(self, data):
        """Crea un evento manual de forma atómica y publica sus parches."""
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

    # ===================== Modo de ejecución (normal / estrés) =====================

    def announce_mode(self):
        """Avisa al frontend del modo y el equilibrio actuales (p. ej. tras cargar un escenario)."""
        with self.lock:
            if self.observatory is None:
                return
            report = self.service.auditBalance(self.observatory)
            mode = self.observatory.getExecutionMode()
        self._notify_mode(report, mode, "changed")

    def request_mode(self, mode):
        """
        Atiende la solicitud "mode:set" del frontend. Devuelve la respuesta
        del acknowledgement: {"ok": bool, "reason"?: str, "mode"?: str}.

        - Pasar a estrés es inmediato.
        - Volver a normal exige recuperar el equilibrio del AVL; eso se hace
          en segundo plano y el resultado llega por "mode:changed".
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

            # stress -> normal: se pausa el motor y se recupera en segundo plano.
            self.recovering = True
            self.paused = True
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
                    before_version=before_version,
                    before_indicators=before_indicators,
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

            # El árbol pudo cambiar aunque la auditoría falle: se envía igual.
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

    def _notify_mode(self, report, mode, status):
        self.mode_changed.notify({
            "mode": mode,
            "status": status,
            "balanced": report["balanced"],
            "maxImbalance": report["maxImbalance"],
            "rotations": report.get("rotations", 0),
            "issues": report["issues"],
        })

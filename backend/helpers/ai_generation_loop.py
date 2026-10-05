MAX_PENDING_REPORTS = 50  # backpressure threshold

class AiGenerationLoop:
    """Periodically asks the engine for a batch of reports until it is stopped."""

    def __init__(self, socketio, engine):
        self._socketio = socketio
        self._engine = engine
        self._running = False
        self._config = {}

    def is_running(self):
        """Return whether the generation loop is currently active."""
        return self._running

    def start(self, config):
        """Start the loop. Returns False if it was already running."""
        if self._running:
            return False
        self._running = True
        self._config = config
        self._socketio.start_background_task(self._run)
        return True

    def stop(self):
        """Request the loop to stop; it exits at the next check."""
        self._running = False

    def _run(self):
        """Main loop: one batch per tick (one report per station), then wait."""
        tick = 0
        while self._running:
            try:
                self._run_tick(tick)
            except Exception as error:
                self._socketio.emit("reports:generation_error", {"tick": tick, "message": str(error)})
            tick += 1
            self._wait(self._config["interval"])

    def _run_tick(self, tick):
        """Generate one batch and enqueue it only if the user has not stopped the loop meanwhile."""
        if self._engine.pending_count() > MAX_PENDING_REPORTS:  # ASSUMPTION: queue length helper
            return  # backpressure: the user is not consuming the queue

        result = self._engine.generate_reports_from_ai({
            "count": len(self._config["station_ids"]),
            "station_ids": self._config["station_ids"],
            "scenario": self._config.get("scenario"),
            "seed": self._config["seed"] + tick,  # reproducible but different each tick
            "enqueue": False,
        })
        if not result["ok"] or not self._running:
            return

        queued = self._engine.prepare_reports({"reports": result["reports"]})  # ASSUMPTION
        if queued.get("ok", False):
            self._socketio.emit("reports:generated", {
                "tick": tick,
                "reports": result["reports"],
                "fallbackCount": result["fallback_count"],
            })

    def _wait(self, seconds):
        """Sleep in short steps so a stop request takes effect almost immediately."""
        waited = 0.0
        while self._running and waited < seconds:
            self._socketio.sleep(0.25)
            waited += 0.25
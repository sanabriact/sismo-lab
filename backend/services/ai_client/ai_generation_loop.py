MAX_PENDING_REPORTS = 50  # backpressure threshold

class AiGenerationLoop:

    # Initialize the loop with the socket server, the engine and an empty config
    def __init__(self, socketio, engine):
        self._socketio = socketio
        self._engine = engine
        self._running = False
        self._config = {}

    # -------------------------------------------------------------------------
    # Controlling the loop
    # -------------------------------------------------------------------------

    # Get whether the generation loop is currently active
    def is_running(self):
        return self._running

    # Start the loop and return False if it was already running
    def start(self, config):
        if self._running:
            return False
        self._running = True
        self._config = config
        self._socketio.start_background_task(self._run)
        return True

    # Request the loop to stop; it exits at the next check
    def stop(self):
        self._running = False

    # -------------------------------------------------------------------------
    # Running the loop
    # -------------------------------------------------------------------------

    # Run the main loop: one batch per tick (one report per station), then wait
    def _run(self):
        tick = 0
        while self._running:
            try:
                self._run_tick(tick)
            except Exception as error:
                self._socketio.emit("reports:generation_error", {"tick": tick, "message": str(error)})
            tick += 1
            self._wait(self._config["interval"])

    # Generate one batch and enqueue it only if the user has not stopped the loop meanwhile
    def _run_tick(self, tick):
        if self._engine.pending_count() > MAX_PENDING_REPORTS:  # ASSUMPTION: queue length helper
            return  # backpressure: the user is not consuming the queue

        result = self._engine.generate_reports_from_ai({
            "count": len(self._config["station_ids"]),
            "station_ids": self._config["station_ids"],
            "scenario": self._config.get("scenario"),
            "seed": self._config["seed"] + tick,
        })
        if not result["ok"] or not self._running:
            return

        self._socketio.emit("reports:generated", {
            "tick": tick,
            "reports": result["reports"],
            "fallbackCount": result.get("fallback_count", 0),
        })

    # -------------------------------------------------------------------------
    # Waiting between ticks
    # -------------------------------------------------------------------------

    # Sleep in short steps so a stop request takes effect almost immediately
    def _wait(self, seconds):
        waited = 0.0
        while self._running and waited < seconds:
            self._socketio.sleep(0.25)
            waited += 0.25
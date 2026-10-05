import time
from datetime import timedelta


class RealtimeClockService:

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    # Store the collaborators and start with the clock loop stopped
    def __init__(
        self,
        socketio,
        lock,
        get_observatory,
        get_scenario_id,
        save_observatory,
        refresh_metrics,
        interval=1.0,
        persistence_interval=10.0,
    ):
        self.socketio = socketio
        self.lock = lock
        self.get_observatory = get_observatory
        self.get_scenario_id = get_scenario_id
        self.save_observatory = save_observatory
        self.refresh_metrics = refresh_metrics
        self.interval = interval
        self.persistence_interval = persistence_interval
        self.running = False
        self.anchor_monotonic = None
        self.anchor_time = None
        self.last_persist_monotonic = None

    # -------------------------------------------------------------------------
    # Lifecycle control
    # -------------------------------------------------------------------------

    # Start one background loop when a scenario is available
    def start(self, background_target):
        observatory = self.get_observatory()
        if observatory is None or self.running:
            return False

        self.running = True
        now = time.monotonic()
        self.anchor_monotonic = now
        self.anchor_time = observatory.getClock().getCurrentTime()
        self.last_persist_monotonic = now
        self.socketio.start_background_task(background_target)
        return True

    # Stop the loop before replacing or undoing a scenario
    def stop(self):
        self.running = False
        self.anchor_monotonic = None
        self.anchor_time = None
        self.last_persist_monotonic = None

    # Continue real-time progression from a manually advanced instant
    def reset_anchor(self, current_time):
        now = time.monotonic()
        self.anchor_monotonic = now
        self.anchor_time = current_time
        self.last_persist_monotonic = now

    # -------------------------------------------------------------------------
    # Clock loop
    # -------------------------------------------------------------------------

    # Advance and publish the clock once per real-time interval
    def run(self):
        while True:
            self.socketio.sleep(self.interval)

            # Mutate state under the lock, but emit outside of it
            with self.lock:
                if not self.running:
                    return

                observatory = self.get_observatory()
                if observatory is None:
                    return

                now = time.monotonic()
                elapsed_seconds = int(now - self.anchor_monotonic)
                target_time = self.anchor_time + timedelta(seconds=elapsed_seconds)
                clock = observatory.getClock()

                if target_time <= clock.getCurrentTime():
                    continue

                clock.advanceTo(target_time)
                self.refresh_metrics(observatory)
                if now - self.last_persist_monotonic >= self.persistence_interval:
                    self.save_observatory(observatory)
                    self.last_persist_monotonic = now

                payload = {
                    "scenarioId": self.get_scenario_id(),
                    "currentTime": clock.getCurrentTimeText(),
                }

            self.socketio.emit("clock:updated", payload)
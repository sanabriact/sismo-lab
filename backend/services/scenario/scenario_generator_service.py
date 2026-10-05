import threading
import time
from backend.services.ai_client.event_generator_client import validate_ai_response


# Generate events automatically with the AI client, one station at a time
class ScenarioGeneratorService:

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    # Create the service with its AI client, engine and default generation settings
    def __init__(self, ai_client, engine):
        self.ai_client = ai_client
        self.engine = engine
        self.stations = []
        self.current_index = 0

        self.interval = 3
        self.max_events = 900
        self.event_count = 0

        self.stop_event = threading.Event()
        self.thread = None

    # -------------------------------------------------------------------------
    # Scenario loading
    # -------------------------------------------------------------------------

    # Load a scenario into the engine and reset the generation state
    def load_scenario(self, observatory):
        self.stop()
        self.engine.set_observatory(observatory)
        self.stations = observatory.getStations()
        self.current_index = 0
        self.event_count = 0

        # Generation is started explicitly from the interface.
        # Loading a scenario must not consume the AI by itself.
        self.thread = None

    # -------------------------------------------------------------------------
    # Generation control
    # -------------------------------------------------------------------------

    # Start a single automatic generation for the active scenario
    def start(self):
        if len(self.stations) == 0:
            return False, "no_stations"

        if self.thread is not None and self.thread.is_alive():
            return True, "already_running"

        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        return True, "started"

    # Signal the generation thread to stop
    def stop(self):
        if self.stop_event:
            self.stop_event.set()

    # -------------------------------------------------------------------------
    # Station rotation
    # -------------------------------------------------------------------------

    # Return the next station in round-robin order
    def next_station(self):
        station = self.stations[self.current_index]
        self.current_index += 1

        if self.current_index == len(self.stations):
            self.current_index = 0

        return station

    # -------------------------------------------------------------------------
    # Generation loop
    # -------------------------------------------------------------------------

    # Generate, validate and enqueue events until stopped or the limit is reached
    def run(self):
        while not self.stop_event.is_set():
            # Stop when the session event limit is reached
            if self.event_count >= self.max_events:
                self.engine.emit_error(
                    self.stations[0],
                    "Se alcanzó el límite de eventos de la sesión",
                )
                return

            start_time = time.time()
            station = self.next_station()

            # Ask the AI for an event, validate it and enqueue it
            try:
                observatory = self.engine.get_observatory()

                raw_data = self.ai_client.generate(
                    station,
                    observatory.getClock(),
                )

                event_data = validate_ai_response(
                    raw_data,
                    observatory.getClock(),
                )

                self.engine.enqueue(station, event_data)
                self.event_count += 1

            except Exception as error:
                message = str(error)

                self.engine.emit_error(station, message)

                # If Groq rate-limits temporarily, wait one minute
                if "429" in message:
                    self.stop_event.wait(60)
                    continue

            # Wait the rest of the interval before the next generation
            elapsed = time.time() - start_time
            wait_time = self.interval - elapsed

            if wait_time > 0:
                self.stop_event.wait(wait_time)
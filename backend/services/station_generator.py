import threading
import random
from backend.services.ai_event_client import validate_ai_response

class StationGenerator:
    def __init__(self, station, ai_client, engine):
        self.station = station
        self.ai_client = ai_client
        self.engine = engine
        self.stop_event = threading.Event()

    def start(self):
        threading.Thread(target=self.run, daemon=True).start()

    def stop(self):
        self.stop_event.set()

    def run(self):
        while not self.stop_event.is_set():
            self.stop_event.wait(random.randint(8, 20))

            if self.stop_event.is_set():
                return

            try:
                observatory = self.engine.get_observatory()

                data = self.ai_client.generate(
                    station=self.station,
                    clock=observatory.getClock(),
                    zones=observatory.getZones(),
                )

                event_data = validate_ai_response(
                    data,
                    observatory.getClock(),
                )

                self.engine.enqueue(self.station, event_data)

            except Exception as error:
                self.engine.emit_error(self.station, str(error))
import threading
import time
from backend.services.ai_event_client import validate_ai_response

class ScenarioGeneratorManager:
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

    def load_scenario(self, observatory):
        self.stop()
        self.engine.set_observatory(observatory)
        self.stations = observatory.getStations()
        self.current_index = 0
        self.event_count = 0
        
        if len(self.stations) == 0:
            return
        
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
    
    def stop(self):
        if self.stop_event:
            self.stop_event.set()
    
    def next_station(self):
        station = self.stations[self.current_index]
        self.current_index += 1
        
        if self.current_index == len(self.stations):
            self.current_index = 0
        
        return station
    
    def run(self):
        while not self.stop_event.is_set():
            if self.event_count >= self.max_events:
                self.engine.emit_error(
                    self.stations[0],
                    "Se alcanzó el límite de eventos de la sesión",
                )
                return

            start_time = time.time()
            station = self.next_station()

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

                # Si Groq limita temporalmente, espera un minuto.
                if "429" in message:
                    self.stop_event.wait(60)
                    continue

            elapsed = time.time() - start_time
            wait_time = self.interval - elapsed

            if wait_time > 0:
                self.stop_event.wait(wait_time)
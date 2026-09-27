import threading
import random
import time
from backend.services.realtime_service import emit_event

class AIEventGenerator:
    def __init__(self, observatory_service, min_interval=5, max_interval=20):
        self.observatory_service = observatory_service
        self.min_interval = min_interval
        self.max_interval = max_interval
        self._stop_event = threading.Event()
    
    def start_for_station(self, station):
        thread = threading.Thread(target=self._loop, args=(station,), daemon=True)
        thread.start()
    
    def stop_all(self):
        self._stop_event.set()
    
    def _loop(self, station):
        while not self._stop_event.set():
            time.sleep(random.uniform(self.min_interval, self.max_interval))
            try:
                report = self._generate_report_via_ai(station)
                result = self.observatory_service.processReport(report)
                emit_event("report_processed", {
                    "station": station.toDict(),
                    "result": result
                })
            except Exception as error:
                emit_event("report_error", {
                    "station": station.toDict(),
                    "result": str(error)
                })
    
    def _generate_report_via_ai(self, station):
        """ Pendiente """
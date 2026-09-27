import queue
import threading

class EventEngine:
    def __init__(self, socketio, repository):
        self.socketio = socketio
        self.repository = repository
        self.observatory = None
        self.events = queue.Queue()
        self.lock = threading.Lock()
        self.paused = False
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
            "station": station,
            "data": data,
        })

    def start(self):
        self.socketio.start_background_task(self.run)

    def run(self):
        while True:
            candidate = self.events.get()

            while self.paused:
                self.socketio.sleep(0.2)

            try:
                with self.lock:
                    operation = self._apply_generated_event(candidate)
                    self.repository.save(self.observatory)

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
    
    def _apply_generated_event(self, candidate):
        station = candidate["station"]
        data = candidate["data"]

        event_id = next_available_event_id(self.observatory)
        mode = self.observatory.getExecutionMode()
        balance = mode == "normal"

        self.observatory.begin_visual_operation()

        self.observatory.createEvent(
            id=event_id,
            magnitude=data["magnitude"],
            depth=data["depth"],
            epicenter_x=data["epicenter_x"],
            epicenter_y=data["epicenter_y"],
            datetime=data["datetime"],
            revision=1,
            station=station,
            balance=balance,
        )

        event = self.observatory.searchEventById(event_id)

        return {
            "mode": mode,
            "stationId": station.id,
            "event": event.toDict(),
            "steps": self.observatory.finish_visual_operation(),
        }
        
    def recover_from_stress(self):
        self.paused = True

        try:
            with self.lock:
                self.observatory.begin_visual_operation()

                avl = self.observatory.getAVLTree()
                avl.recover_balance()

                self.observatory.setExecutionMode("normal")
                self.repository.save(self.observatory)

                self.sequence += 1

                payload = {
                    "scenarioId": self.scenario_id,
                    "sequence": self.sequence,
                    "mode": "normal",
                    "stationId": None,
                    "event": None,
                    "steps": self.observatory.finish_visual_operation(),
                }

            self.socketio.emit("tree:operation", payload)

        finally:
            self.paused = False
        
def next_available_event_id(observatory):
    used_ids = set(observatory.getAVLTree().index.keys())
    used_ids.update(observatory.getHistory().getArchived().keys())
    used_ids.update(observatory.getHistory().getDeletedIds())
    
    for eventId in range(1, 1000000):
        if eventId not in used_ids:
            return eventId
    
    raise RuntimeError("No hay ids disponibles.")
# ------------------------------------------------------------------
# s oc ke t b ro ad ca st er
# ------------------------------------------------------------------

from backend.services.socket.realtime_service import emit_event

class SocketBroadcaster:
    def __init__(self, mode_changed, scenario_loaded, emit=emit_event):
        self._unsubscribers = [
            mode_changed.subscribe(lambda payload: emit("mode:changed", payload)),
            scenario_loaded.subscribe(lambda payload: emit("scenario:loaded", payload))
        ]
    
    def close(self):
        for unsubscribe in self._unsubscribers:
            unsubscribe()
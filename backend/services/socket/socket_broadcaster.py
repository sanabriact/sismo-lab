# ------------------------------------------------------------------
# Socket broadcaster
# ------------------------------------------------------------------

from backend.services.socket.realtime_service import emit_event


# Forward domain events to socket clients
class SocketBroadcaster:

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    # Subscribe to domain events and emit them through the socket
    def __init__(self, mode_changed, scenario_loaded, emit=emit_event):
        self._unsubscribers = [
            mode_changed.subscribe(lambda payload: emit("mode:changed", payload)),
            scenario_loaded.subscribe(lambda payload: emit("scenario:loaded", payload)),
        ]

    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------

    # Unsubscribe from all registered events
    def close(self):
        for unsubscribe in self._unsubscribers:
            unsubscribe()
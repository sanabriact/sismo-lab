# ------------------------------------------------------------------
# Realtime service
# ------------------------------------------------------------------

# Socket.IO instance shared by the module
_socketio = None


# ------------------------------------------------------------------
# Initialization
# ------------------------------------------------------------------

# Register the Socket.IO instance used to emit events
def init_realtime(socketio_instance):
    global _socketio
    _socketio = socketio_instance


# ------------------------------------------------------------------
# Event emission
# ------------------------------------------------------------------

# Emit an event to connected clients if the service is initialized
def emit_event(event_name, payload):
    if _socketio is not None:
        _socketio.emit(event_name, payload)
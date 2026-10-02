_socketio = None

def init_realtime(socketio_instance):
    global _socketio
    _socketio = socketio_instance
    
def emit_event(event_name, payload):
    if _socketio is not None:
        _socketio.emit(event_name, payload)
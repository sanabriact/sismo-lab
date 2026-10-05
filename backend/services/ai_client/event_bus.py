from backend.services.ai_client.subject import Subject

# Subject notified when the execution mode changes
mode_changed = Subject()

# Subject notified when a scenario is loaded
scenario_loaded = Subject()
import os
from backend.services.load_scenario_manager import LoadScenarioManager

ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "escenario_insercion.json")

manager = LoadScenarioManager()
result = manager.loadFromFile(ruta, False)

print(result)
print(manager.errors)
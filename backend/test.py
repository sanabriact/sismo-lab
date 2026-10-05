# ------------------------------------------------------------------
# t es t
# ------------------------------------------------------------------

from backend.models.station import Station
from backend.services.tree_service import TreeService
from backend.models.seismic_observatory import SeismicObservatory
from backend.models.report import Report
from backend.repositories.json_repository import JSONRepository
from datetime import datetime

observatory = SeismicObservatory()
n = 7
for i in range(1,7):
    date = datetime(2024, 6, 1, 12, 0, 0)
    magnitude = 4.0 + i * 0.5
    observatory.createEvent(n-i,magnitude,10.0,20.0,30.0, date,1,"ST-001")
     
print("================================= DIBUJO ÁRBOLES ========================================")
observatory.getAVLTree().draw()
observatory.getBSTTree().draw()
print("=========================================================================")
print(f"Busqueda (id = 100): {observatory.searchEventById(100)}")
print(F"Eliminación (id = 2): {observatory.deleteEventById(2)}") 
observatory.getAVLTree().draw()
observatory.getBSTTree().draw()
print("=========================================================================")
station = Station(1,"ST-001", 20, 40)
report = Report(3,2,station, 3.2,23,105,105,datetime(2025, 6, 1, 12, 0, 0))
observatory.editEvent(report)
observatory.getBSTTree().draw()
persistence = JSONRepository("seismic_observatory.json")
observatory.getAVLTree().draw()

persistence._write(observatory.toDict())
print("=========================================================================")


tree_service = TreeService("tree.json")
tree_service.postTree(observatory.getAVLTree())

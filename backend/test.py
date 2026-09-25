from backend.structures.avl import AVL
from backend.structures.bst import BST
from backend.models.event import Event
from backend.models.seismic_observatory import SeismicObservatory
from backend.models.report import Report
from backend.repositories.json_repository import JSONRepository

from datetime import datetime

observatory = SeismicObservatory()

list = []
n = 7
for i in range(1,7):
    date = datetime(2024, 6, 1, 12, 0, 0)
    magnitude = 4.0 + i * 0.5
    observatory.createEvent(n-i,magnitude,10.0,20.0,30.0, date,1,"ST-001")
     

observatory.getAVLTree().draw()
observatory.getBSTTree().draw()
print("=========================================================================") 
print(observatory.searchEventById(100))
print(observatory.deleteEventById(2))
observatory.getAVLTree().draw()

report = Report(3,2,"ST-001", 3.2,23,105,105,datetime(2025, 6, 1, 12, 0, 0))
observatory.editEvent(report)
observatory.getAVLTree().draw()
observatory.getBSTTree().draw()
persistence = JSONRepository("seismic_observatory.json")

persistence._write(observatory.toDict())




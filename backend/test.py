""" from backend.services.seismic_observatory_service import SeismicObservatoryService
from backend.services.tree_service import TreeService
from backend.structures.avl import AVL
from backend.structures.bst import BST
from backend.models.event import Event
from backend.models.seismic_observatory import SeismicObservatory
from backend.models.report import Report
from backend.repositories.seismic_observatory_repository import SeismicObservatoryRepository
from backend.repositories.json_repository import JSONRepository
from datetime import datetime

observatory = SeismicObservatory()
obs_service = SeismicObservatoryService()

list = []
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
report = Report(3,2,"ST-001", 3.2,23,105,105,datetime(2025, 6, 1, 12, 0, 0))
observatory.editEvent(report)
observatory.getBSTTree().draw()
persistence = JSONRepository("seismic_observatory.json")
observatory.getAVLTree().draw()

persistence._write(observatory.toDict())
print("=========================================================================")


tree_service = TreeService("tree.json")
tree_service.postTree(observatory.getAVLTree()) """

from datetime import datetime, timezone
from backend.models.event import Event
from backend.structures.avl import AVL
from backend.structures.bst import BST

def ev(i, m=3.0):
    return Event(i, m, 10.0, 20.0, 30.0, datetime(2026, 9, 7, 10, 0, tzinfo=timezone.utc), 1, 1)

# BST: delete root, two-children node and leaf; the index must stay consistent
bst = BST()
for i in [5, 3, 8, 2, 4, 7, 9]:
    bst.insert(ev(i, 3.0 + i / 10))
for i in [5, 3, 9]:
    assert bst.delete(i) is True
    assert bst.delete(i) is False
ids = [e.getKey()[2] for e in bst.inorder()]
assert ids == sorted(ids) == [2, 4, 7, 8]
assert set(bst.index) == set(ids)

# AVL: ascending insertions must produce exactly ONE recorded RR rotation
avl = AVL()
avl.begin_visual_operation()
for i in [1, 2, 3]:
    avl.insert(ev(i))
steps = avl.finish_visual_operation()
rotations = [s["rotation"]["type"] for s in steps if s["kind"] == "rotation"]
assert rotations == ["RR"], rotations
assert avl.audit()["ok"]

# Report: naive and aware datetimes must compare without errors
from backend.utils.quantities import normalizeDatetime, toTenths
assert normalizeDatetime(datetime(2026, 9, 7, 10, 0)) == datetime(2026, 9, 7, 10, 0, tzinfo=timezone.utc)
assert toTenths(4.5) == toTenths(4.50) == 45
print("point 0 OK")
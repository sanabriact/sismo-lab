from backend.models.event import Event
class History:
    
    def __init__(self):
        self.archived = {}
        self.archivedTrees = []
        self.deleted = {}
        self.listHistoricIds = []

    def addDeleted(self, key, event):
        self.deleted[key] = event

    def getDeleted(self):
        return self.deleted

    def getDeletedEvents(self):
        return [e.toDict() for e in self.deleted.values()]

    def addArchivedTree(self, root_id, ids, tree):
        self.archivedTrees.append({
            "root_id": root_id,
            "affected_ids": ids,
            "number_nodes": len(ids),
            "tree": tree,
        })

    def getArchivedTrees(self):
        return self.archivedTrees
    
    def getArchived(self):
        return self.archived
    def getArchivedEvent(self,key):
        return self.archived[key]
    def addArchived(self,key,event):
        self.archived[key] = event
    def deleteArchived(self, key):
        del self.archived[key]

    def addIdEvent(self, id):
        if self.binarySearch(id, self.listHistoricIds):
            return False
        self.listHistoricIds.append(id)
        self.merge_sort(self.listHistoricIds)
        return True
        
    def merge_sort(self, list):
        if len(list) <= 1:
            return
        half = len(list) // 2
        left = list[:half]
        right = list[half:]

        self.merge_sort(left)
        self.merge_sort(right)
        self.merge(list, left, right)
        
    def merge(self, list, left, right):
        i = j = k = 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                list[k] = left[i]
                i += 1
            else:
                list[k] = right[j]
                j += 1
            k += 1
        while i < len(left):
            list[k] = left[i]
            i += 1
            k += 1
        while j < len(right):
            list[k] = right[j]
            j += 1
            k += 1
            
    def binarySearch(self, id, list):
        start = 0
        end = len(list) - 1

        while(start <= end):
            half = (start + end) // 2
            
            if list[half] == id:
                return True
            elif list[half] > id:
                end = half - 1
            else:
                start = half + 1
        return False
    
    def toDict(self):
        return {
            "archived": {k: e.toDict() for k, e in self.archived.items()},
            "archivedTrees": self.archivedTrees,
            "deleted": {k: e.toDict() for k, e in self.deleted.items()},
            "listHistoricIds": self.listHistoricIds,
    }

    @classmethod
    def fromDict(cls, data):
        history = cls()
        history.archived = {int(k): Event.fromDict(e) for k, e in data["archived"].items()}
        history.archivedTrees = data.get("archivedTrees", [])
        history.deleted = {int(k): Event.fromDict(e) for k, e in data.get("deleted", {}).items()}
        history.listHistoricIds = data.get("listHistoricIds", [])
        return history
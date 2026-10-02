from backend.models.event import Event
class History:
    def __init__(self):
        self.archived = {} #dict int:event
        self.deleted_ids = set() #set de enteros
        self.listHistoricIds = []

    def getArchived(self):
        return self.archived
    def getArchivedEvent(self,key):
        return self.archived[key]
    def addArchived(self,key,event):
        self.archived[key] = event
    def deleteArchived(self, key):
        del self.archived[key]

    def getDeletedIds(self):
        return self.deleted_ids
    def addDeletedId(self,id):
        self.deleted_ids.add(id)
    def deleteId(self, id):
        self.deleted_ids.remove(id)

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
            "archived": {key: event.toDict() for key,event in self.archived.items()},
            "deleted_ids":[event_id for event_id in self.deleted_ids]
            }
        
    @classmethod
    def fromDict(cls, data):
        history = cls()
        history.archived = {int(key):Event.fromDict(event) for key,event in data["archived"].items()}
        history.deleted_ids = set(data["deleted_ids"])
        return history
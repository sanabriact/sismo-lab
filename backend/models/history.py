class History:
    def __init__(self):
        self.archived = {} #dict int:event
        self.deleted_ids = set() #set de enteros

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

    def toDict(self):
        return {
            "archived": {key: event.toDict() for key,event in self.archived.items()},
            "deleted_ids":[event_id for event_id in self.deleted_ids]
            }
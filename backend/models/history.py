from backend.models.event import Event


class History:

    # Initialize the empty history structures
    def __init__(self):
        self.archived = {}
        self.archivedTrees = []
        self.deleted = {}
        # Keep deleted identities even when a test or a loaded file stores only
        # the tombstone ID and not the full deleted event object.
        self.deletedIds = set()
        self.listHistoricIds = []

    # -------------------------------------------------------------------------
    # Deleted events
    # -------------------------------------------------------------------------

    # Store a deleted event and preserve its identity permanently
    def addDeleted(self, key, event):
        self.deleted[key] = event
        self.addDeletedId(key)

    # Register a deleted identity without requiring an event snapshot
    def addDeletedId(self, key):
        self.deletedIds.add(key)
        self.addIdEvent(key)

    # Get the dictionary of deleted events
    def getDeleted(self):
        return self.deleted

    # Return every deleted identity, including ID-only tombstones
    def getDeletedIds(self):
        return set(self.deletedIds).union(self.deleted.keys())

    # Get the deleted events as a list of dictionaries
    def getDeletedEvents(self):
        return [e.toDict() for e in self.deleted.values()]

    # ------------------------------------------------------------------
    # Archived events
    # ------------------------------------------------------------------

    # Get the dictionary of archived events
    def getArchived(self):
        return self.archived

    # Get one archived event by its key
    def getArchivedEvent(self, key):
        return self.archived[key]

    # Index one archived event for direct identity-based lookup
    def addArchived(self, key, event):
        self.archived[key] = event
        self.addIdEvent(key)

    # Remove one archived event by its key
    def deleteArchived(self, key):
        del self.archived[key]

    # ------------------------------------------------------------------
    # Archived trees
    # ------------------------------------------------------------------

    # Store the tree removed when an event was archived
    def addArchivedTree(self, root_id, ids, tree):
        self.archivedTrees.append({
            "root_id": root_id,
            "affected_ids": ids,
            "number_nodes": len(ids),
            "tree": tree,
        })

    # Get the list of archived trees
    def getArchivedTrees(self):
        return self.archivedTrees

    # ------------------------------------------------------------------
    # Historic identity index (sorted list of ids)
    # ------------------------------------------------------------------

    # Add an id to the sorted index, returns False if it already exists
    def addIdEvent(self, id):
        if self.binarySearch(id, self.listHistoricIds):
            return False
        self.listHistoricIds.append(id)
        self.merge_sort(self.listHistoricIds)
        return True

    # Remove the last id added to the index
    def deleteLastAddedId(self):
        self.listHistoricIds.pop()

    # ------------------------------------------------------------------

    # Sort a list in place using merge sort
    def merge_sort(self, list):
        if len(list) <= 1:
            return
        half = len(list) // 2
        left = list[:half]
        right = list[half:]

        self.merge_sort(left)
        self.merge_sort(right)
        self.merge(list, left, right)

    # Merge two sorted lists into the original list
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

    # Check if an id is in a sorted list using binary search
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

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    # Convert object to dictionary
    def toDict(self):
        return {
            "archived": {k: e.toDict() for k, e in self.archived.items()},
            "archivedTrees": self.archivedTrees,
            "deleted": {k: e.toDict() for k, e in self.deleted.items()},
            "deletedIds": sorted(self.getDeletedIds()),
            "listHistoricIds": self.listHistoricIds,
        }

    # Convert dictionary to object
    @classmethod
    def fromDict(cls, data):
        history = cls()
        history.archived = {
            int(k): Event.fromDict(e)
            for k, e in data.get("archived", {}).items()
        }
        history.archivedTrees = data.get("archivedTrees", [])
        history.deleted = {
            int(k): Event.fromDict(e)
            for k, e in data.get("deleted", {}).items()
        }
        history.deletedIds = {
            int(value) for value in data.get("deletedIds", [])
        }
        history.deletedIds.update(history.deleted.keys())
        history.listHistoricIds = [
            int(value) for value in data.get("listHistoricIds", [])
        ]

        # Older files may not have included every archived/deleted identity.
        # Rebuild the identity index without changing the stored event data.
        for event_id in history.archived:
            history.addIdEvent(event_id)
        for event_id in history.deletedIds:
            history.addIdEvent(event_id)
        return history
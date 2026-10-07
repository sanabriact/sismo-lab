# ------------------------------------------------------------------
# Queue
# ------------------------------------------------------------------

from backend.utils.json_utils import objectToDict
from backend.models.report import Report


# FIFO queue of reports
class Queue:

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    # Create an empty queue
    def __init__(self):
        self.items = []

    # -------------------------------------------------------------------------
    # Queue operations
    # -------------------------------------------------------------------------

    # Return true if the queue has no items
    def is_empty(self):
        return len(self.items) == 0

    # Add an item at the end of the queue
    def enqueue(self, item):
        self.items.append(item)

    # Remove and return the first item, failing if the queue is empty
    def dequeue(self):
        if not self.is_empty():
            return self.items.pop(0)
        else:
            raise IndexError("dequeue from empty queue")

    # Return the first item without removing it, failing if the queue is empty
    def peek(self):
        if not self.is_empty():
            return self.items[0]
        else:
            raise IndexError("peek from empty queue")

    # Return the number of items in the queue
    def size(self):
        return len(self.items)

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    # Convert the queue into a dictionary
    def toDict(self):
        return {
            "items": [objectToDict(item) for item in self.items]
        }

    # Rebuild a queue from a dictionary
    @classmethod
    def fromDict(cls, data, stations_by_id):
        queue = cls()
        queue.items = [Report.fromDict(report, stations_by_id) for report in data["items"]]
        return queue
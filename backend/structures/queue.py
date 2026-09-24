from backend.repositories.json_utils import objectToDict
from backend.models.report import Report
class Queue:
    def __init__(self):
        self.items = []

    def is_empty(self):
        return len(self.items) == 0

    def enqueue(self, item):
        self.items.append(item)

    def dequeue(self):
        if not self.is_empty():
            return self.items.pop(0)
        else:
            raise IndexError("dequeue from empty queue")

    def peek(self):
        if not self.is_empty():
            return self.items[0]
        else:
            raise IndexError("peek from empty queue")

    def size(self):
        return len(self.items)

    def toDict(self):
        return {
            "items":[objectToDict(item) for item in self.items]
        }

    @classmethod
    def fromDict(cls,data):
        queue = cls()
        queue.items = [Report.fromDict(report) for report in data["items"]]
        return queue
# ------------------------------------------------------------------
# Stack
# ------------------------------------------------------------------

from backend.utils.json_utils import objectToDict
from backend.models.action import Action


# LIFO stack of actions
class Stack:

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    # Create an empty stack
    def __init__(self):
        self.items = []

    # -------------------------------------------------------------------------
    # Stack operations
    # -------------------------------------------------------------------------

    # Return true if the stack has no items
    def is_empty(self):
        return len(self.items) == 0

    # Add an item on top of the stack
    def push(self, item):
        self.items.append(item)

    # Remove and return the top item, failing if the stack is empty
    def pop(self):
        if not self.is_empty():
            return self.items.pop()
        else:
            raise IndexError("pop from empty stack")

    # Return the top item without removing it, failing if the stack is empty
    def peek(self):
        if not self.is_empty():
            return self.items[-1]
        else:
            raise IndexError("peek from empty stack")

    # Return the number of items in the stack
    def size(self):
        return len(self.items)

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    # Convert the stack into a dictionary
    def toDict(self):
        return {
            "items": [objectToDict(item) for item in self.items]
        }

    # Rebuild a stack from a dictionary
    @classmethod
    def fromDict(cls, data):
        stack = cls()
        stack.items = [Action.fromDict(action) for action in data["items"]]
        return stack
# ------------------------------------------------------------------
# Tree node
# ------------------------------------------------------------------

from backend.utils.json_utils import objectToDict
from backend.utils.quantities import normalizeDatetime, parseDatetime


# Node shared by the tree structures, holding a value and its links
class Node:

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    # Create a node with the given value and no links
    def __init__(self, value):
        self.value = value
        self.height = 0
        self.leftChild = None
        self.rightChild = None
        self.parent = None
        self.nodeCreationTime = None

    # -------------------------------------------------------------------------
    # Value
    # -------------------------------------------------------------------------

    # Get the node value
    def getValue(self):
        return self.value

    # Set the node value
    def setValue(self, newValue):
        self.value = newValue

    # -------------------------------------------------------------------------
    # Children
    # -------------------------------------------------------------------------

    # Get the left child
    def getLeftChild(self):
        return self.leftChild

    # Set the left child
    def setLeftChild(self, node):
        self.leftChild = node

    # Return true if it has a left child
    def hasLeftChild(self):
        return not (self.leftChild is None)

    # Get the right child
    def getRightChild(self):
        return self.rightChild

    # Set the right child
    def setRightChild(self, node):
        self.rightChild = node

    # Return true if it has a right child
    def hasRightChild(self):
        return not (self.rightChild is None)

    # -------------------------------------------------------------------------
    # Parent
    # -------------------------------------------------------------------------

    # Get the parent
    def getParent(self):
        return self.parent

    # Set the parent
    def setParent(self, node):
        self.parent = node

    # Return true if it has a parent
    def hasParent(self):
        return not (self.parent is None)

    # -------------------------------------------------------------------------
    # Height and creation time
    # -------------------------------------------------------------------------

    # Return the node height
    def getHeight(self):
        return self.height

    # Set the node height
    def setHeight(self, newHeight):
        self.height = newHeight

    # Set the creation time
    def setNodeCreationTime(self, time):
        self.nodeCreationTime = normalizeDatetime(time)

    # -------------------------------------------------------------------------
    # Position checks
    # -------------------------------------------------------------------------

    # Return true if it is a leaf node
    def isLeaf(self):
        return self.getLeftChild() is None and self.getRightChild() is None

    # Return true if the node is a left child
    def isLeftChild(self):
        return self.hasParent() and self.parent.getLeftChild() is self

    # Return true if the node is a right child
    def isRightChild(self):
        return self.hasParent() and self.parent.getRightChild() is self

    # -------------------------------------------------------------------------
    # Archiving
    # -------------------------------------------------------------------------

    # Check whether the node can be archived
    def isArchivable(self, actualTime, time):
        key = self.value.getKey()
        return key[0] == 1 and self.calculateTime(actualTime) > time

    # Calculate how long ago the node event was created
    def calculateTime(self, actualTime):
        return actualTime - self.value.getDateTime()

    # -------------------------------------------------------------------------
    # Tree metrics
    # -------------------------------------------------------------------------

    # Calculate the depth of the node
    def getDepth(self, counter):
        if self.getParent() is not None:
            counter += 1
            return self.getParent().getDepth(counter)
        else:
            return counter

    # Count the nodes of the subtree
    def countNodes(self, counter):
        counter += 1
        if self.hasLeftChild():
            counter = self.getLeftChild().countNodes(counter)
        if self.hasRightChild():
            counter = self.getRightChild().countNodes(counter)
        return counter

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    # Convert the node and its subtree into a dictionary
    def toDict(self):

        return {
            "value": objectToDict(self.value),
            "height": self.height,
            "left_child": objectToDict(self.leftChild),
            "right_child": objectToDict(self.rightChild),
            "node_creation_time": (
                self.nodeCreationTime.isoformat()
                if self.nodeCreationTime is not None
                else None)

        }

    # Rebuild a node and its subtree from a dictionary
    @classmethod
    def fromDict(cls, data, event_cls):

        node = cls(
            event_cls.fromDict(data["value"])
        )

        node.height = data["height"]

        if data["left_child"] is not None:
            node.leftChild = cls.fromDict(
                data["left_child"],
                event_cls
            )
            node.leftChild.parent = node

        if data["right_child"] is not None:
            node.rightChild = cls.fromDict(
                data["right_child"],
                event_cls
            )
            node.rightChild.parent = node

        if data["node_creation_time"] is not None:
            node.nodeCreationTime = parseDatetime(data["node_creation_time"])
        else:
            node.nodeCreationTime = None

        return node
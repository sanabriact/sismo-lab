# ------------------------------------------------------------------
# BST tree
# ------------------------------------------------------------------

from backend.structures.node import Node
from backend.utils.json_utils import objectToDict


# Binary search tree of events with an id index and visual operation recording
class BST:

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    # Create an empty tree
    def __init__(self):
        self.root = None
        self.index = {}
        self._dirty_ids = set()
        self._removed_ids = set()
        self._visual_steps = []

    # -------------------------------------------------------------------------
    # Visual operation recording
    # -------------------------------------------------------------------------

    # Mark a node as changed so it is included in the next patch
    def _touch(self, node):
        if node is not None:
            event_id = node.getValue().getKey()[2]
            self._dirty_ids.add(event_id)

    # Reset the change tracking before a new visual operation
    def begin_visual_operation(self):
        self._dirty_ids.clear()
        self._removed_ids.clear()

    # Build the patch with the changed and removed nodes and reset the tracking
    def finish_visual_operation(self):
        # Collect the changed nodes
        upserted = []

        for event_id in self._dirty_ids:
            node = self.index.get(event_id)
            if node is None:
                continue

            upserted.append({
                "id": event_id,
                "key": list(node.getValue().getKey()),
                "height": node.getHeight(),
                "leftChildId": (
                    node.getLeftChild().getValue().getKey()[2]
                    if node.hasLeftChild()
                    else None
                ),
                "rightChildId": (
                    node.getRightChild().getValue().getKey()[2]
                    if node.hasRightChild()
                    else None
                ),
                "parentId": (
                    node.getParent().getValue().getKey()[2]
                    if node.hasParent()
                    else None
                ),
            })

        # Find the root id
        root_id = None

        if self.root is not None:
            root_id = self.root.getValue().getKey()[2]

        # Reset the tracking and return the patch
        removed_ids = list(self._removed_ids)
        self._dirty_ids.clear()
        self._removed_ids.clear()

        return {
            "operation": "delete" if removed_ids else "insert",
            "upserted": upserted,
            "removedIds": removed_ids,
            "rootId": root_id,
        }

    # -------------------------------------------------------------------------
    # Insertion
    # -------------------------------------------------------------------------

    # Try to insert the node as the left child
    def _tryInsertLeftChild(self, currentRoot, node):
        leftChild = currentRoot.getLeftChild()
        if leftChild is None:
            currentRoot.setLeftChild(node)
            node.setParent(currentRoot)
            self.index[node.getValue().getKey()[2]] = node
            self._touch(node)
            self._touch(currentRoot)
            return True, leftChild
        else:
            return False, leftChild

    # Try to insert the node as the right child
    def _tryInsertRightChild(self, currentRoot, node):
        rightChild = currentRoot.getRightChild()
        if rightChild is None:
            currentRoot.setRightChild(node)
            node.setParent(currentRoot)
            self.index[node.getValue().getKey()[2]] = node
            self._touch(node)
            self._touch(currentRoot)
            return True, rightChild
        else:
            return False, rightChild

    # Public method of inserting
    def insert(self, data):
        event_id = data.getKey()[2]
        # Event identity is unique independently from the ordering key.
        if event_id in self.index:
            return False

        node = Node(data)
        if self.root is None:
            self.root = node
            self.index[event_id] = node
            self._touch(node)
            return True
        else:
            return self._insert(node, self.root)

    # Private method of inserting
    def _insert(self, node, currentRoot):
        # Validate equality
        if currentRoot.getValue().getKey() == node.getValue().getKey():
            return False
        if node.getValue().getKey() < currentRoot.getValue().getKey():
            inserted, child = self._tryInsertLeftChild(currentRoot, node)
        if node.getValue().getKey() > currentRoot.getValue().getKey():
            inserted, child = self._tryInsertRightChild(currentRoot, node)

        if inserted:
            self._refresh_heights(self.root)
            return True
        return self._insert(node, child)

    # Update the tree when a report changes an event key.
    def _updateTree(self, event):
        self.delete(event.getKey()[2])
        self.insert(event)

    # -------------------------------------------------------------------------
    # Search
    # -------------------------------------------------------------------------

    # Search an element by its key
    def search(self, data):
        if self.root is None:
            return None
        else:
            return self._search(data, self.root)

    # Private method of searching
    def _search(self, data, currentRoot):
        if currentRoot is None:
            return None
        else:
            if data == currentRoot.getValue().getKey()[2]:
                return currentRoot

            left = self._search(data, currentRoot.getLeftChild())
            if left is not None:
                return left

        return self._search(data, currentRoot.getRightChild())

    # Search an element by its id
    def searchById(self, id):
        if self.root is None:
            return None
        else:
            return self._searchById(id)

    # Private method of searching an element by id
    def _searchById(self, id):
        if id in self.index:
            return self.index[id]
        else:
            return None

    # -------------------------------------------------------------------------
    # Traversals
    # -------------------------------------------------------------------------

    # Public method for preorder transversal
    def preorder(self):
        if self.root is None:
            return None
        else:
            list_ = []
            return self._preorder(self.root, list_)

    # Private method for preorder transversal
    def _preorder(self, currentRoot, list_):
        if currentRoot is not None:
            list_.append(currentRoot.getValue())
            self._preorder(currentRoot.getLeftChild(), list_)
            self._preorder(currentRoot.getRightChild(), list_)
            return list_

        return None

    # Public method for inorder transversal
    def inorder(self):
        if self.root is None:
            return None
        else:
            list_ = []
            return self._inorder(self.root, list_)

    # Private method for inorder transversal
    def _inorder(self, currentRoot, list_):
        if currentRoot is not None:
            self._inorder(currentRoot.getLeftChild(), list_)
            list_.append(currentRoot.getValue())
            self._inorder(currentRoot.getRightChild(), list_)
            return list_

        return None

    # Public method for postorder transversal
    def postorder(self):
        if self.root is None:
            return None
        else:
            list_ = []
            return self._postorder(self.root, list_)

    # Private method for postorder transversal
    def _postorder(self, currentRoot, list_):
        if currentRoot is not None:
            self._postorder(currentRoot.getLeftChild(), list_)
            self._postorder(currentRoot.getRightChild(), list_)
            list_.append(currentRoot.getValue())
            return list_

        return None

    # -------------------------------------------------------------------------
    # Deletion
    # -------------------------------------------------------------------------

    # Public method for eliminating a node
    def delete(self, data):
        # We check the tree has root
        if self.root is None:
            return False
        else:
            # We check that the node exists in the tree
            targetNode = self.searchById(data)
            if targetNode is None:
                return False
            else:
                self._delete(targetNode)
                return True

    # Private method for eliminating a node
    def _delete(self, node):
        removed_id = node.getValue().getKey()[2]          # CHANGE 1: remember the id

        # We ask if the node doesn´t has children
        if node.isLeaf():
            nodeParent = node.getParent()

            if nodeParent is None:                        # CHANGE 2: the root was the only node
                self.root = None
            elif node.isLeftChild():
                nodeParent.setLeftChild(None)
            else:
                nodeParent.setRightChild(None)

            node.setParent(None)
        else:
            if node.hasLeftChild() and node.hasRightChild():
                predecessor = self._getPredecessor(node.getLeftChild())
                predecessor_id = predecessor.getValue().getKey()[2]
                self._updateNodeValue(node, predecessor)
                self.index[predecessor_id] = node         # CHANGE 1: the value now lives in `node`

                # CHANGE 3: the predecessor has at most a left child, so one branch is enough
                predecessorParent = predecessor.getParent()
                replacement = predecessor.getLeftChild()  # may be None (leaf case)
                if predecessorParent is node:
                    node.setLeftChild(replacement)
                else:
                    predecessorParent.setRightChild(replacement)
                if replacement is not None:
                    replacement.setParent(predecessorParent)

                predecessor.setLeftChild(None)
                predecessor.setParent(None)

            else:
                # CHANGE 2: one child; it also works when the node is the root
                child = node.getLeftChild() if node.hasLeftChild() else node.getRightChild()
                nodeParent = node.getParent()

                if nodeParent is None:
                    self.root = child
                elif node.isLeftChild():
                    nodeParent.setLeftChild(child)
                else:
                    nodeParent.setRightChild(child)

                child.setParent(nodeParent)
                node.setLeftChild(None)
                node.setRightChild(None)
                node.setParent(None)

        # Remove the original identity from the auxiliary index.  In the
        # two-child case the predecessor identity now points to the old node.
        self.index.pop(removed_id, None)
        self._dirty_ids.discard(removed_id)
        self._removed_ids.add(removed_id)
        self._touch(node.getParent())
        self._refresh_heights(self.root)

    # Private method for getting a predeccesor of a root.
    def _getPredecessor(self, node):
        rightChild = node.getRightChild()
        # Base case
        if rightChild is None:
            return node

        # Recursive call
        else:
            return self._getPredecessor(rightChild)

    # Private method for exchanging values (used in delete method.)
    def _updateNodeValue(self, oldNode, newNode):
        oldNode.setValue(newNode.getValue())

    # -------------------------------------------------------------------------
    # Heights
    # -------------------------------------------------------------------------

    # Keep node heights accurate without applying AVL rotations
    def _refresh_heights(self, node):
        if node is None:
            return -1

        left_height = self._refresh_heights(node.getLeftChild())
        right_height = self._refresh_heights(node.getRightChild())
        height = max(left_height, right_height) + 1
        if node.getHeight() != height:
            node.setHeight(height)
            self._touch(node)
        return height

    # -------------------------------------------------------------------------
    # Drawing
    # -------------------------------------------------------------------------

    # Public method for drawing a tree (For test instances)
    def draw(self):
        if self.root is None:
            return

        lines = []
        self._draw(self.root.getRightChild(), "", False, lines)
        lines.append(self._label(self.root))
        self._draw(self.root.getLeftChild(), "", True, lines)
        print("\n".join(lines))

    # Private method of drawing a tree
    def _draw(self, node, prefix, isLeft, lines):
        if node is None:
            return

        self._draw(node.getRightChild(),
                   prefix + ("│   " if isLeft else "    "),
                   False, lines)

        lines.append(prefix + ("└── " if isLeft else "┌── ")
                     + self._label(node))

        self._draw(node.getLeftChild(),
                   prefix + ("    " if isLeft else "│   "),
                   True, lines)

    # Text that is shown for each node
    def _label(self, node):
        value = node.getValue().getKey()
        if isinstance(value, (tuple, list)):
            return "(" + ", ".join(str(v) for v in value) + ")"
        return str(value)

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    # Convert a BST tree instance into a JSON or dictionary type.
    def toDict(self):
        # The index is not included in the dictionary representation because it can be reconstructed from the tree structure.
        return {
            "root": objectToDict(self.root),
        }

    # Convert a JSON answer into a BST object instance.
    @classmethod
    def fromDict(cls, data, event_cls):
        tree = cls()
        if data["root"] is not None:
            tree.root = Node.fromDict(data["root"], event_cls)
            tree._rebuildIndex(tree.root)
        return tree

    # Private method for rebuilding indexes.
    def _rebuildIndex(self, node):
        if node is not None:
            self.index[node.getValue().getKey()[2]] = node
            self._rebuildIndex(node.getLeftChild())
            self._rebuildIndex(node.getRightChild())
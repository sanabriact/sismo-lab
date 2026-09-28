from backend.structures.node import Node
from backend.repositories.json_utils import objectToDict

class BST:
    def __init__(self):
        self.root = None
        self.index = {}
        self._dirty_ids = set()
        self._visual_steps = []
    
    def _touch(self, node):
        if node is not None:
            event_id = node.getValue().getKey()[2]
            self._dirty_ids.add(event_id)
    
    def begin_visual_operation(self):
        self._dirty_ids.clear()


    def finish_visual_operation(self):
        upserted = []

        for event_id in self._dirty_ids:
            node = self.index[event_id]

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

        root_id = None

        if self.root is not None:
            root_id = self.root.getValue().getKey()[2]

        self._dirty_ids.clear()

        return {
            "operation": "insert",
            "upserted": upserted,
            "removedIds": [],
            "rootId": root_id,
        }

    # Method for trying inserting left child
    def _tryInsertLeftChild(self, currentRoot, node):
        leftChild = currentRoot.getLeftChild()
        if leftChild is None:
            currentRoot.setLeftChild(node)
            node.setParent(currentRoot)
            self._touch(node)
            self._touch(currentRoot)
            return True, leftChild
        else:
            return False, leftChild
        
    # Method for trying inserting right child
    def _tryInsertRightChild(self, currentRoot, node):
        rightChild = currentRoot.getRightChild()
        if rightChild is None:
            currentRoot.setRightChild(node)
            node.setParent(currentRoot)
            self._touch(node)
            self._touch(currentRoot)
            return True, rightChild
        else:
            return False, rightChild

    # Public method of inserting
    def insert(self, data):
        node = Node(data)
        if self.root is None:
            self.root = node
            self.index[node.getValue().getKey()[2]]
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
            return True
        return self._insert(node, child)

    # Method for updating the tree when a report changes an event key.
    def _updateKey(self, event, oldKey):
        self.delete(oldKey)
        self.insert(event)
     
    # Search and element by its key
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

    # Public method for eliminating a node
    def delete(self, data):
        # We check the tree has root
        if self.root is None:
            return None
        else:
            # We check that the node exists in the tree
            targetNode = self.search(data[2])
            if targetNode is None:
                return None
            else:
                self._delete(targetNode)

    # Private method for eliminating a node
    def _delete(self, node):
        # We ask if the node doesn´t has children
        if node.isLeaf():
            nodeParent = node.getParent()

            if node.isLeftChild():
                nodeParent.setLeftChild(None)
            else:
                nodeParent.setRightChild(None)

            node.setParent(None)
        else:
            # If the node is not leaf, then we check the 2 restant cases.
            # We first ask if the node has both children.
            if node.hasLeftChild() and node.hasRightChild():
                predecessor = self._getPredecessor(node.getLeftChild())
                self._updateNodeValue(node, predecessor)

                # We validate if the predeccesor is leaf
                if predecessor.isLeaf():
                    predecessorParent = predecessor.getParent()
                    predecessorParent.setRightChild(None)
                else:
                    # If the predeccesor isn't a leaf, it means that the node has a left child (Right child validation isn't neccesary thanks to the getPredeccesor method logic)
                    predecessor.getParent().setLeftChild(predecessor.getLeftChild())
                    predecessor.getLeftChild().setParent(predecessor.getParent())
                    predecessor.setLeftChild(None)

                predecessor.setParent(None)

            # If the node doesn't have both children, then we validate if has a left or a right child.
            # For both cases, we validate that child has again left or right child.
            # For each case, they intercambiate and we eliminate the references of the parent to the old and new child and vice versa.
            else:
                if node.isLeftChild():
                    if node.hasLeftChild():
                        node.getParent().setLeftChild(node.getLeftChild())
                        node.getLeftChild().setParent(node.getParent())
                        node.setLeftChild(None)
                    else:
                        node.getParent().setLeftChild(node.getRightChild())
                        node.getRightChild().setParent(node.getParent())
                        node.setRightChild(None)
                else:
                    if node.hasLeftChild():
                        node.getParent().setRightChild(node.getLeftChild())
                        node.getLeftChild().setParent(node.getParent())
                        node.setLeftChild(None)
                    else:
                        node.getParent().setRightChild(node.getRightChild())
                        node.getRightChild().setParent(node.getParent())
                        node.setRightChild(None)

                node.setParent(None)

    # Private method for getting a predeccesor of a root.
    def _getPredecessor(self, node):
        rightChild = node.getRightChild()
        # Case base
        if rightChild is None:
            return node

        # Recursive call
        else:
            return self._getPredecessor(rightChild)

    # Private method for exchanging values (used in delete method.)
    def _updateNodeValue(self, oldNode, newNode):
        oldNode.setValue(newNode.getValue())
    
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

    # Method to converting a BST tree instance into a JSON or dictionary type.
    def toDict(self):
        #The index is not included in the dictionary representation because it can be reconstructed from the tree structure.
            return {
                "root": objectToDict(self.root),
            }

    # Method for converting a JSON answer into a BST object instance.
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

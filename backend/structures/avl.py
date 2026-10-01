from backend.structures.node import Node
from backend.utils.json_utils import objectToDict
from backend.services.structure_audit_service import StructureAuditService

class AVL:
    def __init__(self):
        self.root = None
        self.index = {} # Search nodes by id; more efficient.
        self._dirty_ids = set()
        self._removed_ids = set()
        self._visual_steps = []
        self.balance = True

    def getBalance(self):
        return self.balance
    def setBalance(self, balance):
        self.balance = balance
    
    def _touch(self, node):
        if node is not None:
            self._dirty_ids.add(node.getValue().getKey()[2])
            
    def begin_visual_operation(self):
        self._dirty_ids.clear()
        self._removed_ids.clear()
        self._visual_steps = []


    def finish_visual_operation(self):
        steps = self._visual_steps
        self._visual_steps = []
        return steps


    def _record_insert(self):
        patch = self._build_patch("insert")

        self._visual_steps.append({
            "kind": "insert",
            "avlPatch": patch,
        })


    def _record_rotation(self, rotation_type, pivot):
        new_root = pivot.getParent()
        patch = self._build_patch("rotation")

        affected_ids = []

        for node in patch["upserted"]:
            affected_ids.append(node["id"])

        self._visual_steps.append({
            "kind": "rotation",
            "rotation": {
                "type": rotation_type,
                "pivotId": pivot.getValue().getKey()[2],
                "newRootId": new_root.getValue().getKey()[2],
                "affectedIds": affected_ids,
            },
            "avlPatch": patch,
        })
    
    def _record_heights(self):
        self._visual_steps.append({
            "kind": "heights",
            "avlPatch": self._build_patch("heights")
        })
    
    def _record_delete(self):
        self._visual_steps.append({
            "kind": "delete",
            "avlPatch": self._build_patch("delete")
        })

    # Method for trying inserting left child
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

    # Method for trying inserting right child
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
        node = Node(data)
        if self.root is None:
            self.root = node
            self.index[node.getValue().getKey()[2]] = node
            self._touch(node)
            self._record_insert()
            
            return True
        else:
            return self._insert(node, self.root, self.balance)

    # Private method of inserting
    def _insert(self, node, currentRoot, balance):
        # We validate equality
        if currentRoot.getValue().getKey() == node.getValue().getKey():
            print("Already existing node with this value ", node.getValue())
            return False
        if node.getValue().getKey() < currentRoot.getValue().getKey():
            inserted, child = self._tryInsertLeftChild(currentRoot, node)
        if node.getValue().getKey() > currentRoot.getValue().getKey():
            inserted, child = self._tryInsertRightChild(currentRoot, node)
        #Check balance
        if inserted:
            self._update_heights_to_root(node.getParent())
            self._record_insert()
            if balance:
                self._checkBalance(node.getParent(), 0)
            self.index[node.getValue().getKey()[2]] = node
            return True
        return self._insert(node, child, balance)
    
    def _updateTree(self, event):
        self.delete(event.getKey()[2])
        self.insert(event)
        
    # Public method for searching a node
    def search(self, data):
        if self.root is None:
            print("The tree is empty.")
            return None
        else:
            return self._search(data, self.root)

    # Private method of searching
    def _search(self, data, currentRoot):
        if currentRoot is not None:
            if data == currentRoot.getValue().getKey()[2]:
                return currentRoot
            else:
                left = self._search(data, currentRoot.getLeftChild())
                if left is None:
                    right = self._search(data, currentRoot.getRightChild())
                    if right is None:
                        return None
                    else:
                        return right
                else:
                    return left

    # Search an element by its id
    def searchById(self, id):
        if self.root is None:
            print("The tree is empty.")
            return None
        else:
            return self._searchById(id)

    # Private method of searching an element by id
    def _searchById(self, id):
        if id in self.index:
            return self.index[id]
        else:
            return None

    # Public method for preorder transversal
    def preorder(self):
        if self.root is None:
            print("The tree is empty so can not be traversed.")
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
            print("The tree is empty so can not be traversed.")
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
            print("The tree is empty so can not be traversed.")
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

    # Public method for deleting a node
    def delete(self, data):
        # First we check the tree has a root
        if self.root is None:
            return None
        else:
            # We check the node exists in the tree
            targetNode = self.index.get(data)

            if targetNode is None:
                return False
            else:
                return self._delete(targetNode, self.balance)

    # Private method for deleting a node
    def _delete(self, node, balance):
        nodeParent = node.getParent()
        start = nodeParent
        removed_id = node.getValue().getKey()[2]
        # We ask if the node doesn't has children
        if node.isLeaf():
            if nodeParent is None:
                self.root = None
            elif node.isLeftChild():
                nodeParent.setLeftChild(None)
            else:
                nodeParent.setRightChild(None)
            
            # We add the node id to the list for managing tree changes easily
            self._removed_ids.add(node.getValue().getKey()[2])
            self._touch(nodeParent)
            node.setParent(None)
            del self.index[removed_id]
            
        elif node.hasLeftChild() and node.hasRightChild():
            # If the node isn't leaf, then we validate the 2 cases left.
            # First we ask if the node has both children
            predecessor = self._getPredecessor(node.getLeftChild())
            predecessorParent = predecessor.getParent()
            predecessor_id = predecessor.getValue().getKey()[2]
            start = predecessorParent
            self._updateNodeValue(node, predecessor)
            # We add the node id to the removed ids
            self._removed_ids.add(removed_id)
            self.index.pop(removed_id, None)
            self.index[predecessor_id] = node
            self._touch(node)
            self._touch(nodeParent)
            self._touch(node.getLeftChild())
            self._touch(node.getRightChild())
            
            replacement = predecessor.getLeftChild()
            if predecessorParent is node:
                predecessorParent.setLeftChild(replacement)
            else:
                predecessorParent.setRightChild(replacement)
            if replacement is not None:
                replacement.setParent(predecessorParent)
                self._touch(replacement)
            self._touch(predecessorParent)
            predecessor.setLeftChild(None)
            predecessor.setParent(None)                

            # If the node doesn't has both children, then we validate if has left or right child.
            # Then for both them, we ask again if the node has left or right child.
        else:
            child = node.getLeftChild() if node.hasLeftChild() else node.getRightChild()
            if nodeParent is None:
                self.root = child
            elif node.isLeftChild():
                nodeParent.setLeftChild(child)
            else:
                nodeParent.setRightChild(child)
            child.setParent(nodeParent)
            self._removed_ids.add(removed_id)
            self._touch(nodeParent)
            self._touch(child)
            node.setLeftChild(None)
            node.setRightChild(None)
            node.setParent(None)
            del self.index[removed_id]

        self._update_heights_to_root(start)
        self._record_delete()
        if balance:
            self._checkBalance(start, 0)
        return True

    # Private method for getting a predeccesor of a root.
    def _getPredecessor(self, node):
        rightChild = node.getRightChild()
        # Caso base (Condición de salida)
        if rightChild is None:
            return node

        # Llamada recursiva
        else:
            return self._getPredecessor(rightChild)

    # Private method for exchanging values (used in delete method.)
    def _updateNodeValue(self, oldNode, newNode):
        oldNode.setValue(newNode.getValue())

    # Private method for getting a node height.
    def _height(self, node):
        if node is None:
            return -1
        else:
            return node.getHeight()

    # Private method for updating a node height
    def _updateHeight(self, node):
        leftHeight = self._height(node.getLeftChild())
        rightHeight = self._height(node.getRightChild())
        maxHeight = max(leftHeight, rightHeight)
        node.setHeight(1 + maxHeight)
        self._touch(node)
    
    def _update_heights_to_root(self, node):
        while node is not None:
            self._updateHeight(node)
            node = node.getParent()

    # Simple right turn balancing
    def _simpleRightTurn(self, top):
        grandparent = top.getParent()
        middle = top.getLeftChild()
        # Hacemos el giro
        aux = middle.getRightChild()
        if aux is not None:
            aux.setParent(top)
            self._touch(aux)
        middle.setRightChild(top)
        top.setLeftChild(aux)
        middle.setParent(top.getParent())
        top.setParent(middle)
        # We reasignate grandparent reference
        if grandparent is not None:
            if grandparent.getLeftChild() == top:
                grandparent.setLeftChild(middle)
            else:
                grandparent.setRightChild(middle)
            self._touch(grandparent)
        else:
            self.root = middle
        self._updateHeight(top)
        self._updateHeight(middle)
        self._touch(top)
        self._touch(middle)

    # Simple left turn for balancing
    def _simpleLeftTurn(self, top):
        grandparent = top.getParent()
        middle = top.getRightChild()
        # Hacemos el giro
        aux = middle.getLeftChild()
        if aux is not None:
            aux.setParent(top)
            self._touch(aux)
        middle.setLeftChild(top)
        top.setRightChild(aux)
        middle.setParent(top.getParent())
        top.setParent(middle)
        # We asignate grandparent reference
        if grandparent is not None:
            if grandparent.getLeftChild() == top:
                grandparent.setLeftChild(middle)
            else:
                grandparent.setRightChild(middle)
            self._touch(grandparent)
        else:
            self.root = middle
        self._updateHeight(top)
        self._updateHeight(middle)
        self._touch(top)
        self._touch(middle)

    # Private method for checking balance
    def _checkBalance(self, node, childBalanceFactor):
        if node is not None:
            if node.getLeftChild() is not None:
                self._updateHeight(node.getLeftChild())
            if node.getRightChild() is not None:
                self._updateHeight(node.getRightChild())
            leftHeight = self._height(node.getLeftChild())
            rightHeight = self._height(node.getRightChild())
            balanceFactor = leftHeight - rightHeight
            self._updateHeight(node)
            if balanceFactor in [-1, 0, 1]:
                self._checkBalance(node.getParent(), balanceFactor)
            else:
                self._rebalance(node, balanceFactor, childBalanceFactor)

    # Private method for getting balancing case
    def _getCaseOfBalance(self, superiorBalanceFactor, childBalanceFactor):
        case = ""
        if superiorBalanceFactor < 0 and childBalanceFactor < 0:
            case = "RR"
        elif superiorBalanceFactor > 0 and childBalanceFactor > 0:
            case = "LL"
        elif superiorBalanceFactor < 0 and childBalanceFactor > 0:
            case = "RL"
        elif superiorBalanceFactor > 0 and childBalanceFactor < 0:
            case = "LR"

        return case

    # Private method for rebalancing
    def _rebalance(self, superior, superiorBalanceFactor, childBalanceFactor=0):
        if superiorBalanceFactor > 0:
            child = superior.getLeftChild()
            child_bf = self._height(child.getLeftChild()) - self._height(child.getRightChild())
            balanceCase = "LL" if child_bf >= 0 else "LR"
        else:
            child = superior.getRightChild()
            child_bf = self._height(child.getLeftChild()) - self._height(child.getRightChild())
            balanceCase = "RR" if child_bf <= 0 else "RL"

        match balanceCase:
            case "LL":
                self._simpleRightTurn(superior)
            case "RR":
                self._simpleLeftTurn(superior)
            case "LR":
                self._simpleLeftTurn(superior.getLeftChild())
                self._simpleRightTurn(superior)
            case "RL":
                self._simpleRightTurn(superior.getRightChild())
                self._simpleLeftTurn(superior)
            case _:
                return None

        self._record_rotation(balanceCase, superior)
        self._checkBalance(superior.getParent().getParent(), 0)
        if self._dirty_ids:
            self._record_heights()
    
    def recover_balance(self):
        while True:
            self._refresh_heights(self.root)
            if not self._recover_one_node(self.root):
                break
        if self._dirty_ids or self._removed_ids:
            self._record_heights()

    def _refresh_heights(self, node):
        if node is None:
            return -1

        left_height = self._refresh_heights(node.getLeftChild())
        right_height = self._refresh_heights(node.getRightChild())

        new_height = max(left_height, right_height) + 1

        if node.getHeight() != new_height:
            node.setHeight(new_height)
            self._touch(node)

        return new_height


    def _recover_one_node(self, node):
        if node is None:
            return False

        # Primero corrige los subárboles inferiores.
        if self._recover_one_node(node.getLeftChild()):
            return True

        if self._recover_one_node(node.getRightChild()):
            return True

        left_height = self._height(node.getLeftChild())
        right_height = self._height(node.getRightChild())
        balance_factor = left_height - right_height

        # Caso izquierdo: LL o LR.
        if balance_factor > 1:
            left_node = node.getLeftChild()

            if self._height(left_node.getLeftChild()) >= self._height(left_node.getRightChild()):
                self._simpleRightTurn(node)
                self._record_rotation("LL", node)
            else:
                self._simpleLeftTurn(left_node)
                self._simpleRightTurn(node)
                self._record_rotation("LR", node)

            return True

        # Caso derecho: RR o RL.
        if balance_factor < -1:
            right_node = node.getRightChild()

            if self._height(right_node.getRightChild()) >= self._height(right_node.getLeftChild()):
                self._simpleLeftTurn(node)
                self._record_rotation("RR", node)
            else:
                self._simpleRightTurn(right_node)
                self._simpleLeftTurn(node)
                self._record_rotation("RL", node)

            return True
        return False

    # Public method for archiving a sub-tree
    def archiveSubTree(self, actualTime, time):
        if self.root is None:
            print("The tree is empty")
        else:
            listToArchivate = []
            archivateRoot = self._archiveSubTree(self.root, actualTime, time ,listToArchivate)
            if archivateRoot:
                self.root = None
                return archivateRoot
            else:
                rootToArchivate = self.findArchiveSubTree(listToArchivate, 1, listToArchivate[0])
                self.removeSubTree(rootToArchivate)
                return rootToArchivate

    # Private method for archivating a sub-tree
    def _archiveSubTree(self, node, actualTime, time, listToArchivate):
        if node is not None:
            leftEligible = self._archiveSubTree(node.getLeftChild(), actualTime, time, listToArchivate)
            rightEligible= self._archiveSubTree(node.getRightChild(), actualTime, time, listToArchivate)
            Eligible = node.isArchivable(actualTime, time) and leftEligible and rightEligible
            if not Eligible:
                if leftEligible and node.getLeftChild() is not None:
                    listToArchivate.append(node.getLeftChild())
                if rightEligible and node.getRightChild() is not None:
                    listToArchivate.append(node.getRightChild())
                return False
        return True
    
    # Public method for finding a archivable sub-tree
    def findArchiveSubTree(self, listToArchivate, index, best):
        if index == len(listToArchivate):
            return best
        node = listToArchivate[index]
        nodeSize = node.countNodes(0)
        bestSize = best.countNodes(0)
        if nodeSize > bestSize:
            best = node
        elif nodeSize == bestSize:
            nodeDepth = node.getDepth(0)
            bestDepth = best.getDepth(0)
            if nodeDepth > bestDepth:
                best = node
            elif nodeDepth == bestDepth:
                if node.getValue()[2] > best.getValue()[2]:
                    best = node
        
        return self.findArchiveSubTree(listToArchivate, index+1, best)
    
    def audit(self, mode="normal"):
        audit_service = StructureAuditService()
        return audit_service.audit_avl(self, mode)
    
    # Public method for drawing a tree
    def draw(self):
        if self.root is None:
            print("(El árbol está vacío)")
            return

        lines = []
        self._draw(self.root.getRightChild(), "", False, lines)
        lines.append(self._label(self.root))
        self._draw(self.root.getLeftChild(), "", True, lines)
        print("\n".join(lines))

    # Private method for drawing a tree
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

    # Text shown for each node
    def _label(self, node):
        value = node.getValue().getKey()
        if isinstance(value, (tuple, list)):
            return "(" + ", ".join(str(v) for v in value) + ")"
        return str(value)


    # Private method for rebuilding an index.
    def _rebuildIndex(self, node):
        if node is not None:
            self.index[node.getValue().getKey()[2]] = node
            self._rebuildIndex(node.getLeftChild())
            self._rebuildIndex(node.getRightChild())
    
    # Private method for building a patch (For front and backend connections)
    def _build_patch(self, operation):
        upserted = []
        for node_id in self._dirty_ids:
            node = self.index.get(node_id)
            if node is not None:
                upserted.append({
                    "id": node_id,
                    "key": list(node.getValue().getKey()),
                    "height": node.getHeight(),
                    "leftChildId": node.getLeftChild().getValue().getKey()[2] if node.hasLeftChild() else None,
                    "rightChildId": node.getRightChild().getValue().getKey()[2] if node.hasRightChild() else None,
                    "parentId": node.getParent().getValue().getKey()[2] if node.hasParent() else None,
                })
        patch = {
            "operation": operation,
            "upserted": upserted,
            "removedIds": list(self._removed_ids),
            "rootId": self.root.getValue().getKey()[2] if self.root is not None else None,
        }
        self._dirty_ids.clear()
        self._removed_ids.clear()
        return patch
    
    
    # Converting a AVL tree instance into a dictionary or JSON type
    def toDict(self):
        return {
            "root": objectToDict(self.root),
            #The index is not included in the dictionary representation because it can be reconstructed from the tree structure.
        }

    # Class method for converting a JSON or dictionary type to a instance of AVL.
    @classmethod
    def fromDict(cls, data, event_cls):
        tree = cls()
        if data["root"] is not None:
            tree.root = Node.fromDict(data["root"], event_cls)
            tree._rebuildIndex(tree.root)  # reconstruye self.index recorriendo el árbol
        return tree
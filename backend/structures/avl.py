from backend.structures.node import Node


class AVL:
    def __init__(self):
        self.root = None
        self.index = {} #Buscador de nodos por id, para acceder a ellos de manera más rápida

    """ # Método para insertar evento
    def insertEvent(self, data, time):
        if self.comprobatorNode(data):
            self.updateNodeValues(data)
        else:
            self.insert(data)
            self.insertTime(time, self.search(data[2]))

    # Método para comprobar la existencia del nodo
    def comprobatorNode(self, data):
        if self.search(data.getValue()[2]) is None:
            return False
        else:
            return True

    # Método para actualizar valores del nodo
    def updateNodeValues(self, data):
        node = self.search(data.getValue()[2])
        node.setValue()[0] = data[0]
        node.setValue()[1] = data[1]
        print("This event already existing in the tree, the data has been updated")

    def insertTime(self, time, node):
        node.setNodeCreationTime(time)"""

    # Método para intentar insertar hijo izquierdo
    def _tryInsertLeftChild(self, currentRoot, node):
        leftChild = currentRoot.getLeftChild()
        if leftChild is None:
            currentRoot.setLeftChild(node)
            node.setParent(currentRoot)
            self.index[node.getValue().getKey()[2]] = node
            print(node.getValue(), " has been inserted as left child of ", currentRoot.getValue())
            return True, leftChild
        else:
            return False, leftChild

    # Método para intentar insertar hijo derecho
    def _tryInsertRightChild(self, currentRoot, node):
        rightChild = currentRoot.getRightChild()
        if rightChild is None:
            currentRoot.setRightChild(node)
            node.setParent(currentRoot)
            self.index[node.getValue().getKey()[2]] = node
            print(node.getValue(), " has been inserted as right child of ",currentRoot.getValue())
            return True, rightChild
        else:
            return False, rightChild

    # Método público de insertar
    def insert(self, data):
        node = Node(data)
        if self.root is None:
            self.root = node
            print("Value ", data, " has been inserted as tree root.")
            return True
        else:
            return self._insert(node, self.root)

        # Método privado de insertar
    def _insert(self, node, currentRoot):
        # Se valida igualdad
        if currentRoot.getValue().getKey() == node.getValue().getKey():
            print("Already existing node with this value ", node.getValue())
            return False
        if node.getValue().getKey() < currentRoot.getValue().getKey():
            inserted, child = self._tryInsertLeftChild(currentRoot, node)
        if node.getValue().getKey() > currentRoot.getValue().getKey():
            inserted, child = self._tryInsertRightChild(currentRoot, node)

        if inserted:
            self._checkBalance(node.getParent(), 0)
            return True
        return self._insert(node, child)
        
    # Buscar un elemento por su key
    def search(self, data):
        if self.root is None:
            print("The tree is empty.")
            return None
        else:
            return self._search(data, self.root)

    # Método privado de buscar
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

    #Buscar elemento por Id
    def searchById(self, id):
        if self.root is None:
            print("The tree is empty.")
            return None
        else:
            return self._searchById(id)

    def _searchById(self, id):
        if id in self.index:
            return self.index[id]
        else:
            return None


    # Método público para recorrer en preorden
    def preorder(self):
        if self.root is None:
            print("The tree is empty so can not be traversed.")
        else:
            list_ = []
            return self._preorder(self.root, list_)

    # Método privado de preorden
    def _preorder(self, currentRoot, list_):
        if currentRoot is not None:
            list_.append(currentRoot.getValue())
            self._preorder(currentRoot.getLeftChild(), list_)
            self._preorder(currentRoot.getRightChild(), list_)
            return list_

        return None

    # Método público para recorrer en inorden
    def inorder(self):
        if self.root is None:
            print("The tree is empty so can not be traversed.")
        else:
            list_ = []
            return self._inorder(self.root, list_)

    # Método privado de inorden
    def _inorder(self, currentRoot, list_):
        if currentRoot is not None:
            self._inorder(currentRoot.getLeftChild(), list_)
            list_.append(currentRoot.getValue())
            self._inorder(currentRoot.getRightChild(), list_)
            return list_

        return None

    # Método público para recorrer en postorden
    def postorder(self):
        if self.root is None:
            print("The tree is empty so can not be traversed.")
        else:
            list_ = []
            return self._postorder(self.root, list_)

    # Método público para recorrer en postorden
    def _postorder(self, currentRoot, list_):
        if currentRoot is not None:
            self._postorder(currentRoot.getLeftChild(), list_)
            self._postorder(currentRoot.getRightChild(), list_)
            list_.append(currentRoot.getValue())
            return list_

        return None

    # Método público para eliminar un nodo
    def delete(self, data):
        # Se verifica que el árbol tenga raíz
        if self.root is None:
            print("Cannot eliminate data. The tree is empty.")
        else:
            # Se verifica que el nodo exista en el árbol
            targetNode = self.search(data)

            if targetNode is None:
                print("Cannot eliminate. Data doesn´t exists.")
                return False
            else:
                return self._delete(targetNode)

    # Método privado de eliminación de nodo
    def _delete(self, node):
        fatherNode = node.getParent()
        # Se pregunta si el nodo es hoja (No tiene hijos)
        if node.isLeaf():
            nodeParent = node.getParent()

            if node.isLeftChild():
                nodeParent.setLeftChild(None)
            else:
                nodeParent.setRightChild(None)

            node.setParent(None)
            
        else:
            # Si el nodo no es hoja, se validan los 2 casos restantes.
            # Primero se pregunta si tiene hijo izquierdo y derecho.
            if node.hasLeftChild() and node.hasRightChild():
                predecessor = self._getPredecessor(node.getLeftChild())
                self._updateNodeValue(node, predecessor)

                # Se valida si el predecesor es hoja
                if predecessor.isLeaf():
                    predecessorParent = predecessor.getParent()
                    predecessorParent.setRightChild(None)
                else:
                    # Si el predecesor no es hoja, significa que el nodo tiene hijo izquierdo (No es necesaria la validación sobre si es hijo derecho, gracias a la lógica del método getPredecessor.)
                    predecessor.getParent().setLeftChild(predecessor.getLeftChild())
                    predecessor.getLeftChild().setParent(predecessor.getParent())
                    predecessor.setLeftChild(None)

                predecessor.setParent(None)
                

            # Si el nodo no tiene dos hijos, se verifica si tiene hijo izquierdo o hijo derecho.
            # Para cada uno de los casos, se verifica nuevamente si este hijo posee hijo izquierdo o derecho.
            # Para cada caso, se cambian y eliminan referencias del padre hacia el nuevo hijo y viceversa.
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
                
        self._checkBalance(fatherNode, 0)
        return True

    # Método privado para obtener el predecesor del subárbol de un nodo.
    # Se pregunta si el nodo que entra a la función tiene hijo derecho.
    # Si tiene hijo derecho, se llama recursivamente a la función con este hijo.
    # Sino, significa que ya se alcanzó el nodo más a la derecha del subárbol izquierdo, por lo que se retorna ese nodo.
    def _getPredecessor(self, node):
        rightChild = node.getRightChild()
        # Caso base (Condición de salida)
        if rightChild is None:
            return node

        # Llamada recursiva
        else:
            return self._getPredecessor(rightChild)

    # Método privado para actualizar el valor entre dos nodos (Para intercambiar el valor entre una raíz y su predecesor.)
    def _updateNodeValue(self, oldNode, newNode):
        oldNode.setValue(newNode.getValue())

    def _height(self, node):
        if node is None:
            return -1
        else:
            return node.getHeight()

    # Método para actualizar altura
    def _updateHeight(self, node):
        leftHeight = self._height(node.getLeftChild())
        rightHeight = self._height(node.getRightChild())
        maxHeight = max(leftHeight, rightHeight)
        node.setHeight(1 + maxHeight)

    # Giro simple a la derecha
    def _simpleRightTurn(self, top):
        grandparent = top.getParent()
        middle = top.getLeftChild()
        # Hacemos el giro
        aux = middle.getRightChild()
        if aux is not None:
            aux.setParent(top)
        middle.setRightChild(top)
        top.setLeftChild(aux)
        middle.setParent(top.getParent())
        top.setParent(middle)
        # reasignamos referencia al abuelo
        if grandparent is not None:
            if grandparent.getLeftChild() == top:
                grandparent.setLeftChild(middle)
            else:
                grandparent.setRightChild(middle)
        else:
            self.root = middle
        self._updateHeight(top)
        self._updateHeight(middle)

    # Giro simple a la izquierda
    def _simpleLeftTurn(self, top):
        grandparent = top.getParent()
        middle = top.getRightChild()
        # Hacemos el giro
        aux = middle.getLeftChild()
        if aux is not None:
            aux.setParent(top)
        middle.setLeftChild(top)
        top.setRightChild(aux)
        middle.setParent(top.getParent())
        top.setParent(middle)
        # Reasignamos referencia al abuelo
        if grandparent is not None:
            if grandparent.getLeftChild() == top:
                grandparent.setLeftChild(middle)
            else:
                grandparent.setRightChild(middle)
        else:
            self.root = middle
        self._updateHeight(top)
        self._updateHeight(middle)

    # Método para verificar el balance
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

    # Método para obtener el caso de balanceo
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

    # Método para balancear
    def _rebalance(self, superior, superiorBalanceFactor, childBalanceFactor):
        balanceCase = self._getCaseOfBalance(
            superiorBalanceFactor, childBalanceFactor)

        match(balanceCase):
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

    # Método publico para archivar un subarbol
    def archiveSubTree(self, time):
        if self.root is None:
            print("The tree is empty")
        else:
            listToArchivate = []
            archivateRoot = self._archiveSubTree(self.root, time, listToArchivate)
            if archivateRoot:
                self.root = None
                return archivateRoot
            else:
                rootToArchivate = self.findArchiveSubTree(listToArchivate, 1, listToArchivate[0])
                self.removeSubTree(rootToArchivate)
                return rootToArchivate

    # Método privado para archivar un arbol
    def _archiveSubTree(self, node, time, listToArchivate):
        if node is not None:
            leftEligible = self._archiveSubTree(node.getLeftChild(), time, listToArchivate)
            rightEligible= self._archiveSubTree(node.getRightChild(), time, listToArchivate)
            Eligible = node.isArchivable(time) and leftEligible and rightEligible
            if not Eligible:
                if leftEligible and node.getLeftChild() is not None:
                    listToArchivate.append(node.getLeftChild())
                if rightEligible and node.getRightChild() is not None:
                    listToArchivate.append(node.getRightChild())
                return False
        return True
    
    # Método para escoger la raiz del arbol a eliminar
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
        
    # Método para remover el arbol a archivar
    def removeSubTree(self, currentRoot):
        parent = currentRoot.getPadre()
        if currentRoot.isLeftChild():
            parent.setLeftChild(None)
        else:
            parent.setRigthChild(None)
        currentRoot.setPadre(None)
                    
    # Método para dibujar el arbol
    def draw(self):
        if self.root is None:
            print("(El árbol está vacío)")
            return

        lines = []
        self._draw(self.root.getRightChild(), "", False, lines)
        lines.append(self._label(self.root))
        self._draw(self.root.getLeftChild(), "", True, lines)
        print("\n".join(lines))

    # Método privado de dibujar
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

    # Texto que se muestra para cada nodo
    def _label(self, node):
        value = node.getValue().getKey()
        if isinstance(value, (tuple, list)):
            return "(" + ", ".join(str(v) for v in value) + ")"
        return str(value)
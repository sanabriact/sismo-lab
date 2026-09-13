class Node:
    def __init__(self, value):
        self.value = value
        self.leftChild = None
        self.rightChild = None
        self.parent = None

    # Se obtiene el valor del nodo
    def getValue(self):
        return self.value

    # Se asigna el valor.
    def setValue(self, newValue):
        self.value = newValue

    # Se obtiene el hijo izquierdo
    def getLeftChild(self):
        return self.leftChild

    # Se asigna el hijo izquierdo
    def setLeftChild(self, node):
        self.leftChild = node

    # Retorna true si tiene hijo izquierdo
    def hasLeftChild(self):
        return not (self.leftChild is None)

    # Se obtiene el hijo derecho
    def getRightChild(self):
        return self.rightChild

    # Se asigna el hijo derecho
    def setRightChild(self, node):
        self.rightChild = node

    # Retorna true si tiene hijo derecho
    def hasRightChild(self):
        return not (self.rightChild is None)

    # Se obtiene el padre
    def getParent(self):
        return self.parent

    # Se asigna el padre
    def setParent(self, node):
        self.parent = node

    # Retorna true si tiene padre
    def hasParent(self):
        return not (self.parent is None)

    # Retorna true si es nodo hoja
    def isLeaf(self):
        return self.getLeftChild() is None and self.getRightChild() is None

    # Retorna true si el nodo es hijo izquierdo
    def isLeftChild(self):
        return self.hasParent() and self.parent.hasLeftChild() and self.value == self.parent.leftChild.value

    # Retorna true si el nodo es hijo derecho
    def isRightChild(self):
        return self.hasParent() and self.parent.hasRightChild() and self.value == self.parent.rightChild.value


class BST:
    def __init__(self):
        self.root = None

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
        if currentRoot.getValue() == node.getValue():
            print("Already existing node with this value ", node.getValue())
            return None
        else:
            if node.getValue()[0] == currentRoot.getValue()[0]:
                if node.getValue()[1] == currentRoot.getValue()[1]:
                    if node.getValue()[2] < currentRoot.getValue()[2]:
                        leftChild = currentRoot.getLeftChild()
                        if leftChild is None:
                            currentRoot.setLeftChild(node)
                            node.setParent(currentRoot)
                            print(
                                node.getValue(), " has been inserted as left child of ", currentRoot.getValue())
                        else:
                            self._insert(node, leftChild)
                    else:
                        rightChild = currentRoot.getRightChild()
                        if rightChild is None:
                            currentRoot.setRightChild(node)
                            node.setParent(currentRoot)
                            print(
                                node.getValue(), " has been inserted as right child of ", currentRoot.getValue())
                        else:
                            self._insert(node, rightChild)
                elif node.getValue()[1] < currentRoot.getValue()[1]:
                    leftChild = currentRoot.getLeftChild()
                    if leftChild is None:
                        currentRoot.setLeftChild(node)
                        node.setParent(currentRoot)
                        print(
                            node.getValue(), " has been inserted as left child of ", currentRoot.getValue())
                    else:
                        self._insert(node, leftChild)
                else:
                    rightChild = currentRoot.getRightChild()
                    if rightChild is None:
                        currentRoot.setRightChild(node)
                        node.setParent(currentRoot)
                        print(node.getValue(), " has been inserted as right child of ", currentRoot.getValue())
                    else:
                        self._insert(node, rightChild)

            # Si es menor se va por la izquierda
            elif node.getValue()[0] < currentRoot.getValue()[0]:
                leftChild = currentRoot.getLeftChild()
                if leftChild is None:
                    currentRoot.setLeftChild(node)
                    node.setParent(currentRoot)
                    print(
                        node.getValue(), " has been inserted as left child of ", currentRoot.getValue())
                else:
                    self._insert(node, leftChild)
                    # Si es mayor se va por la derecha
            else:
                rightChild = currentRoot.getRightChild()
                if rightChild is None:
                    currentRoot.setRightChild(node)
                    node.setParent(currentRoot)
                    print(
                        node.getValue(), " has been inserted as right child of ", currentRoot.getValue())
                else:
                    self._insert(node, rightChild)

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
            if data == currentRoot.getValue()[2]: 
                return currentRoot
            else:
                left = self._search(data,currentRoot.getLeftChild())
                if left is None:
                    right = self._search(data,currentRoot.getRightChild())
                    if right is None: 
                        return None
                    else:
                        return right
                else:
                    return left
      
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
                return None
            else:
                self._delete(targetNode)

    # Método privado de eliminación de nodo
    def _delete(self, node):
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

    def dibujar(self):

        if self.root is None:

            print("El árbol está vacío")

        else:

            print("\nÁrbol BST:")
            print("-----------")

            self._dibujar(
                self.root,
                "",
                "R"
            )

    # método para dibujar conceptualmente el árbol binario

    def _dibujar(self, raizActual, espacio, posicion):

        if raizActual is not None:

            self._dibujar(
                raizActual.getRightChild(),
                espacio + "     ",
                "D"
            )

            print(
                espacio +
                posicion + "── " +
                str(raizActual.getValue())
            )

            self._dibujar(
                raizActual.getLeftChild(),
                espacio + "     ",
                "I"
            )



tree = BST()
list = [(3, 5.2, 10),(2, 5.8, 20),(3, 6.1, 30),(3, 5.2, 5),(3, 5.2, 25), (1,1,1)]
for i in list:
    tree.insert(i)

tree.dibujar()
if tree.search(3):
    print(tree.search(3).getValue())
else:
    print("No existe")

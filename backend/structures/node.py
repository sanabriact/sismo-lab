from backend.persistence.json_utils import objectToDict

class Node:
    def __init__(self, value):
        self.value = value
        self.height = 0
        self.leftChild = None
        self.rightChild = None
        self.parent = None
        self.nodeCreationTime = None

    # Se obtiene el valor del nodo
    def getValue(self):
        return self.value

    # Se asigna el valor
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

    # Retorna la altura del nodo
    def getHeight(self):
        return self.height
    
    # Se asigna la altura del nodo
    def setHeight(self, newHeight):
        self.height = newHeight

    # Se asigna un tiempo de creacion
    def setNodeCreationTime(self, time):
        self.nodeCreationTime = time

    # Se calcula el tiempo desde creacion
    def calculateTime(self, actualTime):
        return actualTime - self.nodeCreationTime
        
    # Retorna true si es nodo hoja
    def isLeaf(self):
        return self.getLeftChild() is None and self.getRightChild() is None

    # Retorna true si el nodo es hijo izquierdo
    def isLeftChild(self):
        return self.hasParent() and self.parent.hasLeftChild() and self.value == self.parent.leftChild.value

    # Retorna true si el nodo es hijo derecho
    def isRightChild(self):
        return self.hasParent() and self.parent.hasRightChild() and self.value == self.parent.rightChild.value
    
    # Método para comprobar si el nodo es archivable
    def isArchivable(self, time):
        return self.value[0] == 1 and self.nodeCreationTime > time 
    
    # Método para calcular la profundidad del nodo
    def getDepth(self, counter):
        if self.getParent() is not None:
            counter += 1
            return self.getParent().getDepth(counter)
        else:
            return counter
        
    # Método para contar nodos
    def countNodes(self, counter):
        counter += 1
        if self.hasLeftChild():
            counter = self.getLeftChild().countNodes(counter)
        if self.hasRightChild():
            counter = self.getRightChild().countNodes(counter)
        return counter

    def toDict(self):
        return {
            "value": objectToDict(self.value),
            "height": self.height,
            "leftChild": objectToDict(self.leftChild),
            "rightChild": objectToDict(self.rightChild),
            "nodeCreationTime": self.nodeCreationTime
            
        }
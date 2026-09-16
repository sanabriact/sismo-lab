from node import Node
from bst import BST
from avl import AVL

tree = AVL()  
bst = BST()      
list = [(3, 5.2, 10),(2, 5.8, 20),(3, 6.1, 30),(3, 5.2, 5),(3, 5.2, 25), (1,1,1), (1,1,2), (3,7,76),(3,9,1001),(3,10,8888)]
for i in list:
    tree.insert(i)
    bst.insert(i)

tree.draw()
print("=========================================================================") 
bst.draw()
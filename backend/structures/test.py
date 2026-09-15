from node import Node
from bst import BST
from avl import AVL

tree = AVL()        
list = [(3, 5.2, 10),(2, 5.8, 20),(3, 6.1, 30),(3, 5.2, 5),(3, 5.2, 25), (1,1,1)]
for i in list:
    tree.insert(i)

tree.draw_tree() 
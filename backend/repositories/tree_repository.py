
from backend.repositories.json_repository import JSONRepository


class TreeRepository(JSONRepository):
    def __init__(self, file_name):
        super().__init__(file_name)

    def save(self, tree):
        data = tree.toDict()
        return self._write(data)

    def load(self,tree_instance ):#AVL or BST
        data = self._read()
        if not data:
            return None
        tree = tree_instance.fromDict(data)
        return tree

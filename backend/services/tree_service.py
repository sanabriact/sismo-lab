from backend.repositories.tree_repository import TreeRepository


class TreeService:

    def __init__(self, file_name):
        self.repository = TreeRepository(file_name)

    def getTree(self, treeInstance):
        tree = self.repository.load(treeInstance)
        if tree is None:
            return None
        return tree

    def postTree(self, tree):
        return self.repository.save(tree)
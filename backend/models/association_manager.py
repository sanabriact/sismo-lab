from backend.models.event import Event

class AssociationManager:
    def __init__(self):
        self.W = 48.0 #horas
        self.R = 40.0 #km
        self.candidates ={} #dict int:list
        self.selected_references = {}#dict int:int

    def getW(self):
        return self.W
    def setW(self, w):
        self.W = w

    def getR(self):
        return self.R
    def setR(self, r):
        self.R = r

    def getCandidates(self):
        return self.candidates
    def getCandidate(self,key):
        return self.candidates[key]
    def addCandidate(self, key, candidate):
        if key not in self.candidates:
            self.candidates[key] = []
            self.candidates[key].append(candidate)
    def deleteCandidate(self,key):
        del self.candidates[key]
    
    def getSelectedReferences(self):
        return self.selected_references
    def getReference(self,key):
        return self.selected_references[key]
    def addReference(self, key, reference):
        self.selected_references[key] = reference
    def deleteCandidate(self,key):
        del self.selected_references[key]

    def toDict(self):
        return {
            "W": self.W,
            "R": self.R,
            "candidates": {
            key: [candidate.toDict() for candidate in candidates]
            for key, candidates in self.candidates.items()
        },
            "selected_references": self.selected_references
        }

    @classmethod
    def fromDict(cls,data):
        manager = cls()
        manager.W = data["W"]
        manager.R = data["R"]
        manager.candidates = {int(key): Event.fromDict(candidate) for key,candidate in data["candidates"].items()}
        manager.selected_references = {int(key): int(value) for key,value in data["selected_references"].items()}
        return manager
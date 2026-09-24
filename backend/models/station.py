class Station:
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def getId(self):
        return self.id
    def setId(self,id):
        self.id = id
    def getName(self):
        return self.name
    def setName(self,name):
        self.name = name

    def toDict(self):
        return {
            "id":self.id,
            "name":self.name
        }

    @classmethod
    def fromDict(cls, data):
        station = cls()
        station.id = data["id"]
        station.name = data["name"]
        return station 
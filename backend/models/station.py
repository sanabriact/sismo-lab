class Station:
    def __init__(self, id, name, x = 0, y = 0):
        self.id = id
        self.name = name
        self.x = x
        self.y = y

    def getId(self):
        return self.id
    def setId(self,id):
        self.id = id
    def getName(self):
        return self.name
    def setName(self,name):
        self.name = name
    def getX(self):
        return self.x
    def setX(self, x):
        self.x = x
    def getY(self):
        return self.y
    def setY(self, y):
        self.y = y
    

    def toDict(self):
        return {
            "id":self.id,
            "name":self.name,
            "x":self.x,
            "y":self.y

        }

    @classmethod
    def fromDict(cls, data):
        station = cls.__new__(cls)
        station.id = data["id"]
        station.name = data["name"]
        # Topology files may contain only the station identity.
        station.x = data.get("x", 0)
        station.y = data.get("y", 0)
        return station 

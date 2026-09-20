class Zone:
    def __init__(self,id,x_min,x_max,y_min,y_max,is_populated):
        self._validateData(x_min, x_max, y_min, y_max)
        self.id = id
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.is_populated = is_populated

    def getid(self):
        return self.id 
    def setid(self, id):
        self.id = id
    def getXMin(self):
        return self.x_min
    def setXMin(self, x_min):
        self.x_min = x_min
    def getXMax(self):
        return self.x_max
    def setXMax(self, x_max):
        self.x_max = x_max
    def getYMin(self):
        return self.y_min
    def setYMin(self, y_min):
        self.y_min = y_min
    def getYMax(self):
        return self.y_max
    def setYMax(self, y_max):
        self.y_max = y_max
    def getIsPopulated(self):
        return self.is_populated   
    def setIsPopulated(self, is_populated):
        self.is_populated = is_populated

    

    def _validateData(self, x_min, x_max, y_min, y_max):
        if not (0.0 <= x_min <= 1000.0) or not (0.0 <= x_max <= 1000.0):
            raise ValueError("x boundaries must be within 0 to 1000 km")
        if not (0.0 <= y_min <= 1000.0) or not (0.0 <= y_max <= 1000.0):
            raise ValueError("y boundaries must be within 0 to 1000 km")
        if x_min >= x_max or y_min >= y_max:
            raise ValueError("Zone boundaries are invalid: min must be less than max")

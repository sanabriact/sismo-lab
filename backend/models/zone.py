
class Zone:

    # Initialize the zone with its id, name, boundaries and population flag
    def __init__(self, id, name, x_min, x_max, y_min, y_max, is_populated):
        self._validateData(x_min, x_max, y_min, y_max)
        self.id = id
        self.name = name
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.is_populated = is_populated

    # -------------------------------------------------------------------------
    # Validates the boundaries of the zone
    # -------------------------------------------------------------------------

    # Validate that the boundaries are inside the plane and min is less than max
    def _validateData(self, x_min, x_max, y_min, y_max):
        if not (0.0 <= x_min <= 1000.0) or not (0.0 <= x_max <= 1000.0):
            raise ValueError("x boundaries must be within 0 to 1000 km")
        if not (0.0 <= y_min <= 1000.0) or not (0.0 <= y_max <= 1000.0):
            raise ValueError("y boundaries must be within 0 to 1000 km")
        if x_min >= x_max or y_min >= y_max:
            raise ValueError("Zone boundaries are invalid: min must be less than max")

    # ------------------------------------------------------------------
    # Reading and writing the zone attributes
    # ------------------------------------------------------------------

    # Get the id of the zone
    def getid(self):
        return self.id

    # Set the id of the zone
    def setid(self, id):
        self.id = id

    # Get the name of the zone
    def getName(self):
        return self.name

    # Set the name of the zone
    def setName(self, name):
        self.name = name

    # ------------------------------------------------------------------

    # Get the minimum x boundary
    def getXMin(self):
        return self.x_min

    # Set the minimum x boundary
    def setXMin(self, x_min):
        self.x_min = x_min

    # Get the maximum x boundary
    def getXMax(self):
        return self.x_max

    # Set the maximum x boundary
    def setXMax(self, x_max):
        self.x_max = x_max

    # Get the minimum y boundary
    def getYMin(self):
        return self.y_min

    # Set the minimum y boundary
    def setYMin(self, y_min):
        self.y_min = y_min

    # Get the maximum y boundary
    def getYMax(self):
        return self.y_max

    # Set the maximum y boundary
    def setYMax(self, y_max):
        self.y_max = y_max

    # ------------------------------------------------------------------

    # Get whether the zone is populated
    def getIsPopulated(self):
        return self.is_populated

    # Set whether the zone is populated
    def setIsPopulated(self, is_populated):
        self.is_populated = is_populated

    # ------------------------------------------------------------------
    # Queries about a point
    # ------------------------------------------------------------------

    # Check if a point is inside the zone, borders included
    def contains(self, x, y):
        return (self.x_min <= x <= self.x_max) and (self.y_min <= y <= self.y_max)

    # Check if a point is exactly on a corner of the zone
    def isInBorder(self, x, y):
        return (x == self.x_min or x == self.x_max) and (y == self.y_min or y == self.y_max)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    # Convert object to dictionary
    def toDict(self):
        return {
            "id": self.id,
            "name": self.name,
            "x_min": self.x_min,
            "x_max": self.x_max,
            "y_min": self.y_min,
            "y_max": self.y_max,
            "is_populated": self.is_populated
        }

    # Convert dictionary to object
    @classmethod
    def fromDict(cls, data):
        name = data.get("name", f"Zona {data['id']}")
        return cls(
            data["id"], name, data["x_min"], data["x_max"],
            data["y_min"], data["y_max"], data["is_populated"],
        )
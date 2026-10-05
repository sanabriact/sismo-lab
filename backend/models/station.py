
class Station:

    # Initialize the station with its id, name and coordinates
    def __init__(self, id, name, x, y):
        self._validate_coordinates(x, y)
        self.id = id
        self.name = name
        self.x = x
        self.y = y

    # -------------------------------------------------------------------------
    # Validates the coordinates of the station
    # -------------------------------------------------------------------------

    # Validate that the coordinates are numbers between 0 and 1000
    def _validate_coordinates(self, x, y):
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise ValueError("La coordenada x de la estación debe ser numérica")
        if isinstance(y, bool) or not isinstance(y, (int, float)):
            raise ValueError("La coordenada y de la estación debe ser numérica")
        if not 0 <= x <= 1000 or not 0 <= y <= 1000:
            raise ValueError("Las coordenadas de la estación deben estar entre 0 y 1000")

    # ------------------------------------------------------------------
    # Reading and writing the station attributes
    # ------------------------------------------------------------------

    # Get the id of the station
    def getId(self):
        return self.id

    # Set the id of the station
    def setId(self, id):
        self.id = id

    # Get the name of the station
    def getName(self):
        return self.name

    # Set the name of the station
    def setName(self, name):
        self.name = name

    # ------------------------------------------------------------------

    # Get the x coordinate of the station
    def getX(self):
        return self.x

    # Set the x coordinate of the station after validating it
    def setX(self, x):
        self._validate_coordinates(x, self.y)
        self.x = x

    # Get the y coordinate of the station
    def getY(self):
        return self.y

    # Set the y coordinate of the station after validating it
    def setY(self, y):
        self._validate_coordinates(self.x, y)
        self.y = y

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    # Convert object to dictionary
    def toDict(self):
        return {
            "id": self.id,
            "name": self.name,
            "x": self.x,
            "y": self.y
        }

    # Convert dictionary to object
    @classmethod
    def fromDict(cls, data):
        missing = [
            field for field in ("id", "name", "x", "y")
            if field not in data
        ]

        if missing:
            station_id = data.get("id")
            raise ValueError(f"Estación {station_id}: faltan campos {','.join(missing)}")

        return cls(data["id"], data["name"], data["x"], data["y"])
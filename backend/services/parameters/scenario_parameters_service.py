from math import isfinite


class ScenarioParametersService:

    def __init__(self):
        self.L = 3
        self.W = 48
        self.R = 40
        self.T = 72

    def getL(self):
        return self.L

    def setL(self, L):
        if not isinstance(L, int) or isinstance(L, bool) or L < 0:
            raise ValueError("L debe ser un número entero mayor o igual a 0")
        self.L = L

    def getW(self):
        return self.W

    def setW(self, W):
        if not isinstance(W, (int, float)) or isinstance(W, bool) or not isfinite(W) or W <= 0:
            raise ValueError("W debe ser un número mayor que 0")
        self.W = W

    def getR(self):
        return self.R

    def setR(self, R):
        if not isinstance(R, (int, float)) or isinstance(R, bool) or not isfinite(R) or R <= 0:
            raise ValueError("R debe ser un número mayor que 0")
        self.R = R

    def getT(self):
        return self.T

    def setT(self, T):
        if not isinstance(T, (int, float)) or isinstance(T, bool) or not isfinite(T) or T <= 0:
            raise ValueError("T debe ser un número mayor que 0")
        self.T = T

    def getAll(self):
        return {"L": self.getL(), "W": self.getW(), "R": self.getR(), "T": self.getT()}

    def update(self, values):
        """Validate all supplied values before applying any of them."""
        if not isinstance(values, dict) or not values:
            raise ValueError("Debe enviar al menos un parámetro")
        allowed = {"L", "W", "R", "T"}
        unknown = set(values) - allowed
        if unknown:
            raise ValueError(f"Parámetro(s) no válido(s): {', '.join(sorted(unknown))}")
        candidate = ScenarioParametersService()
        for name, value in self.getAll().items():
            getattr(candidate, f"set{name}")(value)
        for name, value in values.items():
            getattr(candidate, f"set{name}")(value)
        for name, value in candidate.getAll().items():
            setattr(self, name, value)
        return self.getAll()

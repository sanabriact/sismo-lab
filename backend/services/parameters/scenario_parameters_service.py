from math import isfinite

# Sentinel used to tell "no argument" apart from an explicit None
_UNSET = object()


class ScenarioParametersService:

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    # Create the service with the default scenario parameters
    def __init__(self):
        self.L = 3
        self.W = 48
        self.R = 40
        self.T = 72

    # -------------------------------------------------------------------------
    # Parameter L
    # -------------------------------------------------------------------------

    # Return the current value of L
    def getL(self):
        return self.L

    # Validate and set L as a non-negative integer
    def setL(self, L):
        if not isinstance(L, int) or isinstance(L, bool) or L < 0:
            raise ValueError("L debe ser un número entero mayor o igual a 0")
        self.L = L

    # -------------------------------------------------------------------------
    # Parameter W
    # -------------------------------------------------------------------------

    # Return the current value of W
    def getW(self):
        return self.W

    # Validate and set W as a finite number greater than 0
    def setW(self, W):
        if not isinstance(W, (int, float)) or isinstance(W, bool) or not isfinite(W) or W <= 0:
            raise ValueError("W debe ser un número mayor que 0")
        self.W = W

    # -------------------------------------------------------------------------
    # Parameter R
    # -------------------------------------------------------------------------

    # Return the current value of R
    def getR(self):
        return self.R

    # Validate and set R as a finite number greater than 0
    def setR(self, R):
        if not isinstance(R, (int, float)) or isinstance(R, bool) or not isfinite(R) or R <= 0:
            raise ValueError("R debe ser un número mayor que 0")
        self.R = R

    # -------------------------------------------------------------------------
    # Parameter T
    # -------------------------------------------------------------------------

    # Return the current value of T
    def getT(self):
        return self.T

    # Validate and set T as a finite number greater than 0
    def setT(self, T):
        if not isinstance(T, (int, float)) or isinstance(T, bool) or not isfinite(T) or T <= 0:
            raise ValueError("T debe ser un número mayor que 0")
        self.T = T

    # -------------------------------------------------------------------------
    # Reading all parameters
    # -------------------------------------------------------------------------

    # Return every parameter as a dictionary
    def getAll(self):
        return {"L": self.getL(), "W": self.getW(), "R": self.getR(), "T": self.getT()}

    # -------------------------------------------------------------------------
    # Scenario normalization
    # -------------------------------------------------------------------------

    # Validate scenario overrides and fill omitted fields with defaults
    def normalize_scenario_values(self, values=_UNSET):
        candidate = ScenarioParametersService()
        if values is not _UNSET:
            if not isinstance(values, dict):
                candidate.update(values)
            elif values:
                candidate.update(values)
        return candidate.getAll()

    # Read the optional parameters object from a scenario document
    def parameters_from_scenario(self, scenario):
        if not isinstance(scenario, dict):
            raise ValueError("El escenario debe ser un objeto")
        if "parameters" in scenario and "parametros" in scenario:
            raise ValueError("Use solo uno de 'parameters' o 'parametros'")
        if "parameters" in scenario:
            return self.normalize_scenario_values(scenario["parameters"])
        if "parametros" in scenario:
            return self.normalize_scenario_values(scenario["parametros"])
        return self.normalize_scenario_values()

    # -------------------------------------------------------------------------
    # Updating parameters
    # -------------------------------------------------------------------------

    # Validate all supplied values before applying any of them
    def update(self, values):
        if not isinstance(values, dict) or not values:
            raise ValueError("Debe enviar al menos un parámetro")
        allowed = {"L", "W", "R", "T"}
        unknown = set(values) - allowed
        if unknown:
            raise ValueError(f"Parámetro(s) no válido(s): {', '.join(sorted(unknown))}")
        # Work on a candidate so a failed validation never leaves a partial update
        candidate = ScenarioParametersService()
        for name, value in self.getAll().items():
            getattr(candidate, f"set{name}")(value)
        for name, value in values.items():
            getattr(candidate, f"set{name}")(value)
        for name, value in candidate.getAll().items():
            setattr(self, name, value)
        return self.getAll()
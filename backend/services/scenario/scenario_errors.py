# Raised when a scenario cannot be loaded safely
class ScenarioValidationError(Exception):

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    # Create the error from a list of issues and keep them for later access
    def __init__(self, issues):
        super().__init__("; ".join(issues))
        self.issues = issues
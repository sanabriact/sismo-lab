class ScenarioValidationError(Exception):
    """Raised when a scenario cannot be loaded safely."""

    def __init__(self, issues):
        super().__init__("; ".join(issues))
        self.issues = issues

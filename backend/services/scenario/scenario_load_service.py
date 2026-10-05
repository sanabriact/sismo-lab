from backend.services.scenario.scenario_errors import ScenarioValidationError


class ScenarioLoadService:
    """Validate and build scenario data before the engine activates it."""

    def __init__(self, observatory_service, parameters_service):
        self.observatory_service = observatory_service
        self.parameters_service = parameters_service
        self.validator = None

    def set_validator(self, validator):
        """Set the validator responsible for uploaded scenario content."""
        self.validator = validator

    def load_text(self, content):
        """Return a fully built scenario or restore shared parameters on failure."""
        previous_parameters = self.parameters_service.getAll()
        try:
            validated = None
            if self.validator is not None:
                validated = self.validator.loadFromText(content, stress_mode=False)
                if validated is None:
                    raise ScenarioValidationError(self.validator.errors)

            observatory = self.observatory_service.loadScenarioFromText(content)
            self._load_optional_sections(observatory, validated)

            metrics_service = getattr(self.observatory_service, "metrics_service", None)
            if metrics_service is not None:
                metrics_service.refresh_derived_metrics(observatory)
            return observatory
        except Exception:
            self.parameters_service.update(previous_parameters)
            raise

    def _load_optional_sections(self, observatory, validated):
        """Restore optional export sections when the validator supports them."""
        if self.validator is None:
            return

        loader = getattr(self.validator, "loadOptionalSections", None)
        if not callable(loader):
            return

        try:
            loader(observatory, validated)
        except (AttributeError, IndexError, KeyError, TypeError, ValueError) as error:
            raise ScenarioValidationError([
                f"Secciones opcionales inválidas: {error}"
            ]) from error

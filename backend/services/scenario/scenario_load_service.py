from backend.services.scenario.scenario_errors import ScenarioValidationError


# Validate and build scenario data before the engine activates it
class ScenarioLoadService:

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    # Create the service with its observatory and parameters services
    def __init__(self, observatory_service, parameters_service):
        self.observatory_service = observatory_service
        self.parameters_service = parameters_service
        self.validator = None

    # -------------------------------------------------------------------------
    # Validator
    # -------------------------------------------------------------------------

    # Set the validator responsible for uploaded scenario content
    def set_validator(self, validator):
        self.validator = validator

    # -------------------------------------------------------------------------
    # Scenario loading
    # -------------------------------------------------------------------------

    # Return a fully built scenario or restore shared parameters on failure
    def load_text(self, content):
        previous_parameters = self.parameters_service.getAll()
        try:
            # Validate the content when a validator is available
            validated = None
            if self.validator is not None:
                validated = self.validator.loadFromText(content, stress_mode=False)
                if validated is None:
                    raise ScenarioValidationError(self.validator.errors)

            # Build the scenario and restore its optional sections
            observatory = self.observatory_service.loadScenarioFromText(content)
            self._load_optional_sections(observatory, validated)

            # Refresh the derived metrics when a metrics service is available
            metrics_service = getattr(self.observatory_service, "metrics_service", None)
            if metrics_service is not None:
                metrics_service.refresh_derived_metrics(observatory)
            return observatory
        except Exception:
            self.parameters_service.update(previous_parameters)
            raise

    # -------------------------------------------------------------------------
    # Optional sections
    # -------------------------------------------------------------------------

    # Restore optional export sections when the validator supports them
    def _load_optional_sections(self, observatory, validated):
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
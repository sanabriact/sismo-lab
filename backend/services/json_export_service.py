from backend.repositories.json_export_repository import JSONExportRepository


class JSONExportService:
    """Prepare a consistent JSON export for the active scenario."""

    def __init__(self, repository=None, parameters_service=None):
        self.repository = repository or JSONExportRepository()
        self.parameters_service = parameters_service

    def export(self, observatory):
        if observatory is None:
            return None
        if self.parameters_service is not None:
            parameters = self.parameters_service.getAll()
        else:
            parameters = {
                "W": observatory.getAssociationManager().getW(),
                "R": observatory.getAssociationManager().getR(),
                "L": observatory.getL(),
                "T": observatory.getT(),
            }
        return self.repository.export(observatory, parameters)

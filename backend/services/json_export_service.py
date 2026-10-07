# ------------------------------------------------------------------
# j so n e xp or t s er vi ce
# ------------------------------------------------------------------

from copy import deepcopy
from datetime import datetime, timezone

from backend.repositories.json_export_repository import JSONExportRepository


class JSONExportService:
    """Prepare a consistent JSON export for the active scenario."""

    def __init__(self, repository=None, parameters_service=None):
        self.repository = repository or JSONExportRepository()
        self.parameters_service = parameters_service

    def export(self, observatory):
        if observatory is None:
            return None
        snapshot = self.snapshot(observatory)
        versions = deepcopy(getattr(observatory, "scenario_versions", []))
        if not isinstance(versions, list):
            versions = []
        next_version = max(
            (item.get("version", 0) for item in versions
             if isinstance(item, dict) and isinstance(item.get("version"), int)),
            default=0,
        ) + 1
        versions.append({
            "version": next_version,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "snapshot": snapshot,
        })
        observatory.scenario_versions = versions
        return {**snapshot, "versions": versions}

    def snapshot(self, observatory):
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

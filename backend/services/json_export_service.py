# ------------------------------------------------------------------
# JSON export service
# ------------------------------------------------------------------

from copy import deepcopy
from datetime import datetime, timezone

from backend.repositories.json_export_repository import JSONExportRepository


# Prepare a consistent JSON export for the active scenario
class JSONExportService:

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    # Create the service with its export repository and parameters service
    def __init__(self, repository=None, parameters_service=None):
        self.repository = repository or JSONExportRepository()
        self.parameters_service = parameters_service

    # -------------------------------------------------------------------------
    # Export
    # -------------------------------------------------------------------------

    # Build the export and register a new scenario version
    def export(self, observatory):
        if observatory is None:
            return None

        # Take the current snapshot of the scenario
        snapshot = self.snapshot(observatory)

        # Compute the next version number from the saved versions
        versions = deepcopy(getattr(observatory, "scenario_versions", []))
        if not isinstance(versions, list):
            versions = []
        next_version = max(
            (item.get("version", 0) for item in versions if isinstance(item, dict)
             and isinstance(item.get("version"), int)),
            default=0,
        ) + 1

        # Register the new version and return the export
        versions.append({
            "version": next_version,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "snapshot": snapshot,
        })
        observatory.scenario_versions = versions
        return {**snapshot, "versions": versions}

    # -------------------------------------------------------------------------
    # Snapshot
    # -------------------------------------------------------------------------

    # Build the exportable snapshot with the current scenario parameters
    def snapshot(self, observatory):
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
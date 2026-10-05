from dataclasses import dataclass, field

from backend.utils.quantities import hasAtMostOneDecimal, normalizeDatetime, toTenths


@dataclass
class StepResult:
    """Describe the decision and observable changes from one report."""

    decision: str
    reason: str
    event_id: int
    revision: int
    station_id: object
    key_before: list | None = None
    key_after: list | None = None
    steps: list = field(default_factory=list)
    rotations: list = field(default_factory=list)
    tree_changed: bool = False

    def to_dict(self):
        """Serialize the processing result for logs or transport payloads."""
        return {
            "decision": self.decision,
            "reason": self.reason,
            "event_id": self.event_id,
            "revision": self.revision,
            "station_id": self.station_id,
            "key_before": self.key_before,
            "key_after": self.key_after,
            "steps": self.steps,
            "rotations": self.rotations,
            "tree_changed": self.tree_changed,
        }


class ReportProcessor:
    """Applies one already prepared report to the observatory domain."""

    def __init__(self, on_event_changed=None):
        self.on_event_changed = on_event_changed or (lambda observatory, event_id: None)

    def apply(self, observatory, report, metrics_service=None):
        """Apply one validated report and classify its domain outcome."""
        station_id = report.getStation().getId()
        event_id = report.getEventId()
        revision = report.getRevision()
        invalid_reason = self._validate(observatory, report)
        if invalid_reason is not None:
            observatory.getMetrics().incrementDiscardedReports()
            return StepResult("rejected_invalid", invalid_reason, event_id, revision, station_id)

        history = observatory.getHistory()
        if event_id in history.getDeletedIds():
            observatory.getMetrics().incrementDiscardedReports()
            return StepResult("rejected_deleted", "El evento fue eliminado y no puede reanudarse", event_id, revision, station_id)

        event = observatory.searchEventById(event_id)
        if event is not None:
            return self._apply_active(observatory, event, report)

        archived = history.getArchived().get(event_id)
        if archived is not None:
            return self._apply_archived(observatory, archived, report)

        # An unknown identity is a creation only for its first revision.
        # A higher revision without an active/archived event has no base event
        # to correct, so it must not silently create one.
        if revision != 1:
            observatory.getMetrics().incrementDiscardedReports()
            return StepResult(
                "rejected_invalid",
                "Un evento inexistente solo puede crearse con revision 1",
                event_id,
                revision,
                station_id,
            )

        result = observatory.createEvent(
            id=event_id, magnitude=report.getMagnitude(), depth=report.getDepth(),
            epicenter_x=report.getEpicenterX(), epicenter_y=report.getEpicenterY(),
            datetime=report.getDatetime(), revision=revision, station=station_id,
        )
        if result is False or not all(result):
            observatory.getMetrics().incrementDiscardedReports()
            return StepResult("rejected_invalid", "No se pudo crear el evento nuevo", event_id, revision, station_id)

        event = observatory.searchEventById(event_id)
        self.on_event_changed(observatory, event_id)
        return StepResult("created", "Evento creado correctamente", event_id, revision, station_id, key_after=list(event.getKey()), tree_changed=True)

    def _apply_active(self, observatory, event, report):
        """Handle a report whose event is currently present in both trees."""
        event_id = report.getEventId()
        station_id = report.getStation().getId()
        current_revision = event.getCurrentRevision()
        key_before = list(event.getKey())

        if report.getRevision() > current_revision:
            if not self._valid_report_values(report):
                observatory.getMetrics().incrementDiscardedReports()
                return StepResult("rejected_invalid", "Los valores del reporte están fuera de rango", event_id, report.getRevision(), station_id, key_before, key_before)
            observatory.editEvent(report)
            observatory.getMetrics().incrementAcceptedCorrections()
            self.on_event_changed(observatory, event_id)
            return StepResult("updated", "Corrección aceptada", event_id, report.getRevision(), station_id, key_before, list(event.getKey()), tree_changed=key_before != list(event.getKey()))
        if report.getRevision() < current_revision:
            observatory.getMetrics().incrementDiscardedReports()
            return StepResult("stale", "El reporte tiene una revisión antigua", event_id, report.getRevision(), station_id, key_before, key_before)
        if self._same_data(event, report):
            event.addReportingStation(station_id)
            return StepResult("confirmed", "Confirmación recibida", event_id, report.getRevision(), station_id, key_before, key_before)

        observatory.getMetrics().incrementConflicts()
        return StepResult("conflict", "El reporte entra en conflicto con los datos vigentes", event_id, report.getRevision(), station_id, key_before, key_before)

    def _apply_archived(self, observatory, event, report):
        """Handle a report that may reactivate an archived event."""
        event_id = report.getEventId()
        station_id = report.getStation().getId()
        key_before = list(event.getKey())
        current_revision = event.getCurrentRevision()

        if report.getRevision() < current_revision:
            observatory.getMetrics().incrementDiscardedReports()
            return StepResult("stale", "El reporte archivado tiene una revisión antigua", event_id, report.getRevision(), station_id, key_before, key_before)
        if report.getRevision() == current_revision:
            if self._same_data(event, report):
                event.addReportingStation(station_id)
                return StepResult("confirmed", "Confirmación del evento archivado", event_id, report.getRevision(), station_id, key_before, key_before)
            observatory.getMetrics().incrementDiscardedReports()
            return StepResult("stale", "El evento archivado no coincide con el reporte", event_id, report.getRevision(), station_id, key_before, key_before)

        history = observatory.getHistory()
        history.deleteArchived(event_id)
        event.updateEventData(report, observatory.getZones())
        event.setEventStatus("active")
        if not observatory.getAVLTree().insert(event) or not observatory.getBSTTree().insert(event):
            history.addArchived(event_id, event)
            raise ValueError("No se pudo reactivar el evento archivado")
        observatory.recalculateAssociations()
        observatory.getMetrics().incrementAcceptedCorrections()
        self.on_event_changed(observatory, event_id)
        return StepResult("reactivated", "Evento archivado reactivado correctamente", event_id, report.getRevision(), station_id, key_before, list(event.getKey()), tree_changed=True)

    def _validate(self, observatory, report):
        """Check station, clock, precision, and domain ranges before mutation."""
        station_ids = {station.getId() for station in observatory.getStations()}
        if report.getStation().getId() not in station_ids:
            return "La estación no pertenece al escenario"
        try:
            if not observatory.getClock().canOccurAt(report.getDatetime()):
                return "La fecha del reporte supera el reloj del escenario"
        except (TypeError, ValueError):
            return "La fecha del reporte no es válida"
        for value, label in ((report.getMagnitude(), "magnitud"), (report.getDepth(), "profundidad"), (report.getEpicenterX(), "epicentro x"), (report.getEpicenterY(), "epicentro y")):
            if not hasAtMostOneDecimal(value):
                return f"La {label} admite máximo un decimal"
        if not self._valid_report_values(report):
            return "Los valores del reporte están fuera de rango"
        return None

    def _valid_report_values(self, report):
        """Return whether all numeric report values fit domain limits."""
        return (
            -2 <= report.getMagnitude() <= 10
            and 0 <= report.getDepth() <= 700
            and 0 <= report.getEpicenterX() <= 1000
            and 0 <= report.getEpicenterY() <= 1000
        )

    def _same_data(self, event, report):
        """Compare normalized values to identify an idempotent confirmation."""
        return (
            toTenths(event.getKey()[1]) == toTenths(report.getMagnitude())
            and toTenths(event.getDepth()) == toTenths(report.getDepth())
            and toTenths(event.getEpicenterX()) == toTenths(report.getEpicenterX())
            and toTenths(event.getEpicenterY()) == toTenths(report.getEpicenterY())
            and normalizeDatetime(event.getDateTime()) == normalizeDatetime(report.getDatetime())
        )

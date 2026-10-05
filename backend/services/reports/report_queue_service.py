from backend.models.report import Report
from backend.utils.quantities import hasAtMostOneDecimal, parseDatetime


# Prepare reports and expose the FIFO queue without applying them
class ReportQueueService:

    # -------------------------------------------------------------------------
    # Batch preparation
    # -------------------------------------------------------------------------

    # Validate the whole batch before enqueuing any report
    def prepare(self, observatory, raw_reports):
        if not isinstance(raw_reports, list) or not raw_reports:
            return {"ok": False, "enqueued": 0, "issues": ["Se requiere al menos un reporte"]}

        # Build every report and collect the issues found
        stations = {station.getId(): station for station in observatory.getStations()}
        prepared = []
        issues = []
        for position, raw in enumerate(raw_reports, start=1):
            try:
                prepared.append(self._build_report(raw, stations))
            except (KeyError, TypeError, ValueError) as error:
                issues.append({"report": position, "reason": str(error)})

        if issues:
            return {"ok": False, "enqueued": 0, "issues": issues}

        # Enqueue the batch only when every report is valid
        for report in prepared:
            observatory.enqueueReport(report)
        return {"ok": True, "enqueued": len(prepared), "issues": []}

    # -------------------------------------------------------------------------
    # Queue serialization
    # -------------------------------------------------------------------------

    # Return a read-only snapshot of the queue in the received order
    def snapshot(self, observatory):
        # Queue.dequeue is O(n) because it removes the first list element with
        # pop(0); this read-only snapshot preserves the received order.
        items = []
        for position, report in enumerate(observatory.getReportQueue().items, start=1):
            items.append({
                "position": position,
                "event_id": report.getEventId(),
                "revision": report.getRevision(),
                "station_id": report.getStation().getId(),
                "magnitude": report.getMagnitude(),
                "depth": report.getDepth(),
                "epicenter_x": report.getEpicenterX(),
                "epicenter_y": report.getEpicenterY(),
                "datetime": report.getDatetime().isoformat(),
            })
        return {"size": len(items), "items": items}

    # -------------------------------------------------------------------------
    # Report construction
    # -------------------------------------------------------------------------

    # Convert one raw payload into a domain Report instance
    def _build_report(self, raw, stations):
        # Check the payload shape and required fields
        if not isinstance(raw, dict):
            raise TypeError("El reporte debe ser un objeto")
        required = ("event_id", "revision", "station", "magnitude", "depth", "epicenter_x", "epicenter_y", "datetime")
        missing = [field for field in required if field not in raw]
        if missing:
            raise ValueError(f"Faltan campos: {', '.join(missing)}")

        # Check that the station belongs to the scenario
        station_id = raw["station"]
        if station_id not in stations:
            raise ValueError(f"La estación {station_id} no pertenece al escenario")

        # Check that numeric fields are numbers with at most one decimal
        for field in ("magnitude", "depth", "epicenter_x", "epicenter_y"):
            value = raw[field]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{field} debe ser numérico")
            if not hasAtMostOneDecimal(value):
                raise ValueError(f"{field} admite máximo un decimal")

        return Report(
            event_id=raw["event_id"],
            revision=raw["revision"],
            station=stations[station_id],
            magnitude=raw["magnitude"],
            depth=raw["depth"],
            epicenter_x=raw["epicenter_x"],
            epicenter_y=raw["epicenter_y"],
            datetime_=parseDatetime(raw["datetime"]),
        )
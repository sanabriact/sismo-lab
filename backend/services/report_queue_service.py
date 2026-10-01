from backend.models.report import Report
from backend.utils.quantities import hasAtMostOneDecimal, parseDatetime


class ReportQueueService:
    """Prepares reports and exposes the FIFO queue without applying them."""

    def prepare(self, observatory, raw_reports):
        """Validate the whole batch before enqueuing any report."""
        if not isinstance(raw_reports, list) or not raw_reports:
            return {"ok": False, "enqueued": 0, "issues": ["Se requiere al menos un reporte"]}

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

        for report in prepared:
            observatory.enqueueReport(report)
        return {"ok": True, "enqueued": len(prepared), "issues": []}

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

    def _build_report(self, raw, stations):
        """Convert one raw payload into a domain Report instance."""
        if not isinstance(raw, dict):
            raise TypeError("El reporte debe ser un objeto")
        required = ("event_id", "revision", "station", "magnitude", "depth", "epicenter_x", "epicenter_y", "datetime")
        missing = [field for field in required if field not in raw]
        if missing:
            raise ValueError(f"Faltan campos: {', '.join(missing)}")

        station_id = raw["station"]
        if station_id not in stations:
            raise ValueError(f"La estación {station_id} no pertenece al escenario")

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

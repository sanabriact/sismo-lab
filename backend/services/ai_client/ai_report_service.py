from backend.services.ai_client.ai_report_client import (
    generate_deterministic_reports,
    request_reports_from_llm,
    validate_generated_report_shape,
)


class AIReportService:
    """Generate and validate report candidates without changing observatory state."""

    REPORTS_PER_REQUEST = 7

    def build_context(self, observatory):
        """Build a detached context that can safely be used outside the lock."""
        active = []
        for node in observatory.getAVLTree().index.values():
            event = node.getValue()
            data = event.toDict()
            data["event_id"] = event.getKey()[2]
            # Event.toDict stores the AVL key instead of duplicating magnitude.
            # The AI report context needs magnitude as a direct field because
            # fallback reports copy existing event data.
            data["magnitude"] = event.getKey()[1]
            # Event.toDict stores the reporting stations as a collection.
            # A generated report needs one concrete station id.
            data["station"] = self._first_station_id(event)
            data.pop("key", None)
            active.append(data)

        archived = []
        for event_id, event in observatory.getHistory().getArchived().items():
            data = event.toDict()
            data["event_id"] = event_id
            data["magnitude"] = event.getKey()[1]
            data["station"] = self._first_station_id(event)
            data.pop("key", None)
            archived.append(data)

        deleted_ids = observatory.getHistory().getDeletedIds()
        existing_ids = {item["event_id"] for item in active + archived}

        return {
            "clock": observatory.getClock().getCurrentTime(),
            "station_ids": [station.getId() for station in observatory.getStations()],
            "events": active + archived,
            "deleted_ids": sorted(deleted_ids),
            "used_ids": existing_ids.union(deleted_ids),
        }

    def _first_station_id(self, event):
        """Return a stable station id for fallback report generation."""
        stations = event.getReportingStations()
        if not stations:
            return None
        return sorted(stations)[0]

    def generate(self, context, payload):
        """Generate candidates, validate them, and return only detached data."""
        payload = payload if isinstance(payload, dict) else {}
        # Every AI request represents one fixed batch for the report queue.
        # Other payload options remain available, but the batch size is fixed.
        count = self.REPORTS_PER_REQUEST
        seed = int(payload.get("seed", 42))

        try:
            candidates = request_reports_from_llm(
                context,
                count,
                payload.get("scenario"),
            )
        except Exception as error:
            candidates = []
            llm_issue = str(error)
        else:
            llm_issue = None

        valid = []
        issues = []
        if llm_issue:
            issues.append({"source": "ai", "reason": llm_issue})

        for report in candidates:
            problem = self.validate(report, context)
            if problem:
                issues.append({"source": "ai", "reason": problem, "report": report})
            else:
                valid.append(report)

        fallback_count = 0
        missing = count - len(valid)
        if missing > 0:
            fallback = generate_deterministic_reports(context, missing, seed)
            for report in fallback:
                problem = self.validate(report, context)
                if problem:
                    issues.append({"source": "fallback", "reason": problem, "report": report})
                else:
                    valid.append(report)
                    fallback_count += 1
                if len(valid) >= count:
                    break

        valid = valid[:count]

        # Ensure every batch includes at least one creation with a new id.
        # If the model returned only existing identities, replace the last
        # candidate with a deterministic new report.
        known_ids = {event["event_id"] for event in context["events"]}
        has_new_event = any(report["event_id"] not in known_ids for report in valid)
        if not has_new_event:
            new_reports = generate_deterministic_reports(
                context,
                1,
                seed + 1,
                include_new=True,
            )
            if new_reports and self.validate(new_reports[0], context) is None:
                if valid:
                    valid[-1] = new_reports[0]
                else:
                    valid.append(new_reports[0])
                fallback_count += 1

        if not valid:
            return {
                "ok": False,
                "reports": [],
                "issues": issues or ["No se pudieron generar reportes válidos"],
            }

        return {
            "ok": True,
            "reports": valid,
            "issues": issues,
            "fallback_count": fallback_count,
        }

    def validate(self, report, context):
        """Validate one candidate against the detached scenario context."""
        try:
            problem = validate_generated_report_shape(
                report,
                set(context["station_ids"]),
                context["clock"],
            )
        except (AttributeError, TypeError, ValueError) as error:
            return str(error)

        if problem:
            return problem

        known_ids = {event["event_id"] for event in context["events"]}
        deleted_ids = set(context["deleted_ids"])
        event_id = report["event_id"]
        revision = report["revision"]
        if event_id in deleted_ids:
            return "El event_id pertenece a un evento eliminado"
        # A new identity may arrive with any positive first revision.
        return None

    def normalize(self, report):
        """Convert one valid candidate to the queue input contract."""
        return {
            "event_id": int(report["event_id"]),
            "revision": int(report["revision"]),
            "station": int(report["station"]),
            "magnitude": report["magnitude"],
            "depth": report["depth"],
            "epicenter_x": report["epicenter_x"],
            "epicenter_y": report["epicenter_y"],
            "datetime": report["datetime"],
        }

class EventLifecycleService:
    """Handle event changes without owning locks or transport notifications."""

    def __init__(self, observatory_service, report_processor, report_queue_service):
        self.observatory_service = observatory_service
        self.report_processor = report_processor
        self.report_queue_service = report_queue_service

    def create_manual_event(self, observatory, data):
        """Create one validated manual event in the active observatory."""
        return self.observatory_service.createManualEvent(observatory, data)

    def update_manual_event(
        self,
        observatory,
        data,
        complete_operation,
        save_observatory,
        scenario_id,
    ):
        """Queue or apply one manual correction using the existing report flow."""
        event_id = data.get("event_id") if isinstance(data, dict) else None
        if isinstance(event_id, bool) or not isinstance(event_id, int):
            return {"response": {"ok": False, "reason": "invalid_event_id"}, "tree_operation": None}

        event = observatory.searchEventById(event_id)
        if event is None:
            event = observatory.getHistory().getArchived().get(event_id)
        if event is None:
            return {"response": {"ok": False, "reason": "event_not_found"}, "tree_operation": None}

        try:
            report = self.observatory_service.build_manual_update_report(
                observatory,
                event_id,
                data,
            )
        except ValueError as error:
            return {"response": {"ok": False, "reason": str(error)}, "tree_operation": None}

        metrics_service = self.observatory_service.metrics_service
        before_version = observatory.toVersion()
        before_indicators = metrics_service.capture_display(observatory)
        queue = observatory.getReportQueue()

        if not queue.is_empty():
            observatory.enqueueReport(report)
            metrics_service.record_operation(
                observatory=observatory,
                action_type="updated_event",
                before_version=before_version,
                before_indicators=before_indicators,
                details={"event_id": event_id, "revision": report.getRevision(), "queued": True},
            )
            save_observatory(observatory)
            snapshot = self.report_queue_service.snapshot(observatory)
            return {
                "response": {
                    "ok": True,
                    "queued": True,
                    "revision": report.getRevision(),
                    "snapshot": snapshot,
                },
                "tree_operation": None,
            }

        observatory.begin_visual_operation()
        try:
            result = self.report_processor.apply(observatory, report)
        finally:
            steps = observatory.finish_visual_operation()

        if result.decision not in ("updated", "reactivated"):
            return {
                "response": {
                    "ok": False,
                    "reason": result.reason,
                    "decision": result.decision,
                },
                "tree_operation": None,
            }

        complete_operation(
            observatory,
            "updated_event",
            before_version,
            before_indicators,
            {
                "event_id": event_id,
                "revision": report.getRevision(),
                "queued": False,
                "key_changed": result.tree_changed,
            },
            steps,
        )
        snapshot = self.report_queue_service.snapshot(observatory)
        event = observatory.searchEventById(event_id)
        response = {
            "ok": True,
            "queued": False,
            "revision": report.getRevision(),
            "event": event.toDict(),
            "snapshot": snapshot,
        }

        tree_operation = None
        if result.tree_changed:
            tree_operation = {
                "scenarioId": scenario_id,
                "mode": observatory.getExecutionMode(),
                "stationId": report.getStation().getId(),
                "event": event.toDict(),
                "steps": steps,
            }

        return {"response": response, "tree_operation": tree_operation}

    def mark_reviewed(self, observatory, event_id, complete_operation):
        """Mark an active event as reviewed and record the completed action."""
        event = observatory.searchEventById(event_id)
        if event is None:
            return {"ok": False, "reason": "event_not_found"}

        if event.getAttentionStatus() == "reviewed":
            return {"ok": True, "changed": False, "event": event.toDict()}

        metrics_service = self.observatory_service.metrics_service
        before_version = observatory.toVersion()
        before_indicators = metrics_service.capture_display(observatory)
        previous_status = event.getAttentionStatus()
        event.setAttentionStatus("reviewed")
        complete_operation(
            observatory,
            "mark_reviewed",
            before_version,
            before_indicators,
            {
                "event_id": event_id,
                "previous_attention_status": previous_status,
                "new_attention_status": "reviewed",
            },
        )
        return {"ok": True, "changed": True, "event": event.toDict()}

    def delete_event(self, observatory, event_id, complete_operation):
        """Delete one active event and record the reversible operation."""
        if isinstance(event_id, bool) or not isinstance(event_id, int):
            return {"ok": False, "reason": "invalid_id"}

        event = observatory.searchEventById(event_id)
        if event is None:
            return {"ok": False, "reason": "event_not_found"}

        metrics_service = self.observatory_service.metrics_service
        before_version = observatory.toVersion()
        before_indicators = metrics_service.capture_display(observatory)
        try:
            deleted = observatory.deleteEventById(event_id)
            if not deleted:
                return {"ok": False, "reason": "delete_failed"}

            complete_operation(
                observatory,
                "delete_event",
                before_version,
                before_indicators,
                {"event_id": event_id, "deleted_event": event.toDict()},
            )
            return {"ok": True, "event_id": event_id}
        except (ValueError, KeyError) as error:
            return {"ok": False, "reason": str(error)}

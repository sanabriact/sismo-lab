# Coordinate report queue operations without owning locks or sockets
class ReportProcessingService:

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    # Create the service with its queue service and report processor
    def __init__(self, queue_service, report_processor):
        self.queue_service = queue_service
        self.report_processor = report_processor

    # -------------------------------------------------------------------------
    # Batch preparation
    # -------------------------------------------------------------------------

    # Validate and enqueue a complete report batch
    def prepare(self, observatory, raw_reports):
        result = self.queue_service.prepare(observatory, raw_reports)
        return result, self.queue_service.snapshot(observatory)

    # -------------------------------------------------------------------------
    # Report processing
    # -------------------------------------------------------------------------

    # Process the first queued report and return transport-ready data
    def process_one(
        self,
        observatory,
        scenario_id,
        complete_operation,
        next_sequence,
        metrics_service,
    ):
        # Capture the state before the operation
        report_queue = observatory.getReportQueue()
        before_version = observatory.toVersion()
        before_indicators = metrics_service.capture_display(observatory)
        report = report_queue.dequeue()

        # Apply the report while recording the visual steps
        observatory.begin_visual_operation()
        try:
            result = self.report_processor.apply(
                observatory,
                report,
                metrics_service,
            )
        finally:
            result_steps = observatory.finish_visual_operation()

        result.steps = result_steps
        result.rotations = [
            step.get("rotation", {}).get("type")
            for step in result_steps
            if step.get("kind") == "rotation"
        ]

        # Register the completed operation
        complete_operation(
            observatory,
            "queue_step",
            before_version,
            before_indicators,
            {
                "event_id": result.event_id,
                "revision": result.revision,
                "station_id": result.station_id,
                "decision": result.decision,
                "reason": result.reason,
                "rotations": result.rotations,
                "report_position": 1,
            },
            result_steps,
        )

        # Build the tree payload only when the tree changed
        tree_payload = None
        if result.tree_changed:
            event = observatory.searchEventById(result.event_id)
            tree_payload = {
                "scenarioId": scenario_id,
                "sequence": next_sequence(),
                "mode": observatory.getExecutionMode(),
                "stationId": result.station_id,
                "event": event.toDict() if event is not None else None,
                "steps": result.steps,
            }

        # Build the step payload and return all transport-ready data
        step_payload = {
            "decision": result.decision,
            "reason": result.reason,
            "eventId": result.event_id,
            "revision": result.revision,
            "stationId": result.station_id,
            "rotations": result.rotations,
            "remaining": report_queue.size(),
        }
        return step_payload, tree_payload, self.queue_service.snapshot(observatory)
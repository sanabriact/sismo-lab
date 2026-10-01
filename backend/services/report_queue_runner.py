class ReportQueueRunner:
    """Compatibility facade that delegates queue orchestration to EventEngine."""

    def __init__(self, engine, queue_service=None, processor=None, interval=1.5):
        self.engine = engine
        if interval != 1.5:
            self.engine.report_queue_interval = interval
        if queue_service is not None:
            self.engine.report_queue_service = queue_service
        if processor is not None:
            self.engine.report_processor = processor

    @property
    def queue_service(self):
        """Expose the engine-owned service for compatibility with callers."""
        return self.engine.report_queue_service

    @property
    def processor(self):
        """Expose the engine-owned processor for compatibility with callers."""
        return self.engine.report_processor

    def prepare_reports(self, raw_reports):
        """Forward batch preparation to the engine owner."""
        return self.engine.prepare_reports(raw_reports)

    def process_next(self):
        """Forward one processing step to the engine owner."""
        return self.engine.process_report_step()

    def start_continuous(self):
        """Forward continuous processing startup to the engine owner."""
        return self.engine.start_report_processing()

    def pause(self):
        """Forward a user-requested pause to the engine owner."""
        return self.engine.pause_report_processing()

    def pause_for_recovery(self):
        """Forward the recovery pause used by execution-mode changes."""
        return self.engine.pause_report_processing("recovering")

    def resume(self):
        """Forward queue resumption to the engine owner."""
        return self.engine.resume_report_processing()

    def is_running(self):
        """Report the running state maintained by the engine."""
        return self.engine.report_queue_running

    def snapshot(self):
        """Forward queue serialization to the engine owner."""
        return self.engine.report_queue_snapshot()

# Compatibility facade that delegates queue orchestration to EventEngine
class ReportQueueRunner:

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    # Create the runner and forward any custom settings to the engine
    def __init__(self, engine, queue_service=None, processor=None, interval=1.5):
        self.engine = engine
        if interval != 1.5:
            self.engine.report_queue_interval = interval
        if queue_service is not None:
            self.engine.report_queue_service = queue_service
        if processor is not None:
            self.engine.report_processor = processor

    # -------------------------------------------------------------------------
    # Engine-owned components
    # -------------------------------------------------------------------------

    # Expose the engine-owned service for compatibility with callers
    @property
    def queue_service(self):
        return self.engine.report_queue_service

    # Expose the engine-owned processor for compatibility with callers
    @property
    def processor(self):
        return self.engine.report_processor

    # -------------------------------------------------------------------------

    # Batch preparation
    # -------------------------------------------------------------------------

    # Forward batch preparation to the engine owner
    def prepare_reports(self, raw_reports):
        return self.engine.prepare_reports(raw_reports)

    # -------------------------------------------------------------------------
    # Report processing
    # -------------------------------------------------------------------------

    # Forward one processing step to the engine owner
    def process_next(self):
        return self.engine.process_report_step()

    # Forward continuous processing startup to the engine owner
    def start_continuous(self):
        return self.engine.start_report_processing()

    # -------------------------------------------------------------------------
    # Pause and resume
    # -------------------------------------------------------------------------

    # Forward a user-requested pause to the engine owner
    def pause(self):
        return self.engine.pause_report_processing()

    # Forward the recovery pause used by execution-mode changes
    def pause_for_recovery(self):
        return self.engine.pause_report_processing("recovering")

    # Forward queue resumption to the engine owner

    def resume(self):
        return self.engine.resume_report_processing()

    # -------------------------------------------------------------------------
    # State and serialization
    # -------------------------------------------------------------------------

    # Report the running state maintained by the engine
    def is_running(self):
        return self.engine.report_queue_running

    # Forward queue serialization to the engine owner
    def snapshot(self):
        return self.engine.report_queue_snapshot()
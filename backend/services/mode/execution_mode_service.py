class ExecutionModeService:
    """Coordinate stress-mode changes and AVL recovery bookkeeping."""

    def __init__(self, stress_mode_service, metrics_service):
        self.stress_mode_service = stress_mode_service
        self.metrics_service = metrics_service

    def activate_stress(self, observatory):
        """Apply the domain transition to stress mode."""
        return self.stress_mode_service.activateStressMode(observatory)

    def recover_normal(
        self,
        observatory,
        before_version,
        before_indicators,
    ):
        """Recover AVL balance and record the operation as one action."""
        report = self.stress_mode_service.deactivateStressMode(observatory)
        if self.metrics_service is not None:
            self.metrics_service.refresh_derived_metrics(observatory)
            self.metrics_service.register_rotation_steps(
                observatory.getMetrics(),
                report["steps"],
            )
            self.metrics_service.record_operation(
                observatory=observatory,
                action_type="recover_avl_balance",
                before_version=before_version,
                before_indicators=before_indicators,
                details={
                    "mode_before": "stress",
                    "mode_after": observatory.getExecutionMode(),
                },
            )
        return report

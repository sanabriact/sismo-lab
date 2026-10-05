class ExecutionModeService:

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    # Store the services used to change the execution mode
    def __init__(self, stress_mode_service, metrics_service):
        self.stress_mode_service = stress_mode_service
        self.metrics_service = metrics_service

    # -------------------------------------------------------------------------
    # Stress mode
    # -------------------------------------------------------------------------

    # Apply the domain transition to stress mode
    def activate_stress(self, observatory):
        return self.stress_mode_service.activateStressMode(observatory)

    # -------------------------------------------------------------------------
    # Normal mode recovery
    # -------------------------------------------------------------------------

    # Recover AVL balance and record the operation as one action
    def recover_normal(
        self,
        observatory,
        before_version,
        before_indicators,
    ):
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
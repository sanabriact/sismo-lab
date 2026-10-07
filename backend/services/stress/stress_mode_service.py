# ------------------------------------------------------------------
# Stress mode service
# ------------------------------------------------------------------

from backend.services.audit.structure_audit_service import StructureAuditService


# Coordinate execution mode changes for the active observatory
class StressModeService:

    # -------------------------------------------------------------------------
    # Mode activation
    # -------------------------------------------------------------------------

    # Disable AVL balancing and switch the observatory to stress mode
    def activateStressMode(self, observatory):
        avl_tree = observatory.getAVLTree()
        avl_tree.setBalance(False)
        observatory.setExecutionMode("stress")

        return self._createReport(observatory)

    # -------------------------------------------------------------------------
    # Mode deactivation
    # -------------------------------------------------------------------------

    # Recover the AVL and switch to normal mode only when recovery succeeds
    def deactivateStressMode(self, observatory):
        avl_tree = observatory.getAVLTree()

        # Record the recovery as a visual operation so the engine only has to publish it
        observatory.begin_visual_operation()
        avl_tree.recover_balance()
        steps = observatory.finish_visual_operation()

        # Audit the recovered tree
        audit = StructureAuditService().audit_avl(avl_tree)

        # Return to normal mode only if the audit passed
        if audit["ok"]:
            avl_tree.setBalance(True)
            observatory.setExecutionMode("normal")
        else:
            avl_tree.setBalance(False)
            observatory.setExecutionMode("stress")

        # Build the report with the recorded steps
        report = self._createReport(observatory, audit)
        report["steps"] = steps
        report["rotations"] = self._countRotations(steps)
        return report

    # -------------------------------------------------------------------------
    # Report helpers
    # -------------------------------------------------------------------------

    # Build the mode report, auditing the AVL when no audit is given
    def _createReport(self, observatory, audit=None):
        if audit is None:
            audit = StructureAuditService().audit_avl(observatory.getAVLTree())

        return {
            "ok": audit["ok"],
            "mode": observatory.getExecutionMode(),
            "balanced": audit["balanced"],
            "maxImbalance": audit["max_imbalance"],
            "issues": audit["issues"],
            "steps": [],
            "rotations": 0,
        }

    # Count the rotation steps in a recorded operation
    def _countRotations(self, steps):
        rotations = 0

        for step in steps:
            if step.get("kind") == "rotation":
                rotations += 1

        return rotations

class StressModeManager:
    
    """Coordinates execution mode changes for the active observatory."""

    def activateStressMode(self, observatory):
        """Disable AVL balancing and switch the observatory to stress mode."""
        avl_tree = observatory.getAVLTree()
        avl_tree.setBalance(False)
        observatory.setExecutionMode("stress")

        return self._createReport(observatory)

    def deactivateStressMode(self, observatory):
        """Recover the AVL and switch to normal mode only when recovery succeeds."""
        avl_tree = observatory.getAVLTree()

        # Keep the visual operation here so the engine only has to publish it.
        observatory.begin_visual_operation()
        avl_tree.recover_balance()
        steps = observatory.finish_visual_operation()

        audit = avl_tree.audit()

        if audit["ok"]:
            avl_tree.setBalance(True)
            observatory.setExecutionMode("normal")
        else:
            avl_tree.setBalance(False)
            observatory.setExecutionMode("stress")

        report = self._createReport(observatory, audit)
        report["steps"] = steps
        report["rotations"] = self._countRotations(steps)
        return report

    def _createReport(self, observatory, audit=None):
        if audit is None:
            audit = observatory.getAVLTree().audit()

        return {
            "ok": audit["ok"],
            "mode": observatory.getExecutionMode(),
            "balanced": audit["balanced"],
            "maxImbalance": audit["max_imbalance"],
            "issues": audit["issues"],
            "steps": [],
            "rotations": 0,
        }

    def _countRotations(self, steps):
        rotations = 0

        for step in steps:
            if step.get("kind") == "rotation":
                rotations += 1

        return rotations

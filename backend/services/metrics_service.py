from backend.models.action import Action


class MetricsService:
    """
    Centraliza indicadores y trazabilidad de acciones.

    Las métricas derivables se recalculan desde el árbol.
    Los contadores acumulativos se conservan en Metrics.
    """

    def __init__(self):
        self._inorder = []
        self._preorder = []
        self._postorder = []
        self._leaves = 0

    def capture_display(self, observatory):
        self._reset_traversals()

        root = observatory.getAVLTree().root
        self._collect_preorder(root)
        self._collect_inorder(root)
        self._collect_postorder(root)
        levels = self._collect_levels(root)

        return {
            "tree": {
                "active_events": len(self._inorder),
                "height": self._height(root),
                "leaves": self._leaves,
                "inorder": list(self._inorder),
                "preorder": list(self._preorder),
                "postorder": list(self._postorder),
                "levels": levels,
            },
            "counters": observatory.getMetrics().toDict(),
        }

    def refresh_derived_metrics(self, observatory):
        metrics = observatory.getMetrics()
        root = observatory.getAVLTree().root

        self._reset_traversals()
        self._collect_inorder(root)

        metrics.setActiveEvents(len(self._inorder))
        metrics.setHistoricalEvents(
            len(observatory.getHistory().getArchived())
        )
        metrics.setPendingAttention(
            self._count_pending(observatory.getAVLTree().root)
        )
        metrics.setHighCostAccessEvents(
            self._count_expensive(observatory.getAVLTree().root)
        )

        metrics.setEventsByPriority(1, 0)
        metrics.setEventsByPriority(2, 0)
        metrics.setEventsByPriority(3, 0)
        self._count_priorities(observatory.getAVLTree().root, metrics)

    def register_rotation_steps(self, metrics, steps):
        for step in steps:
            if step.get("kind") != "rotation":
                continue

            rotation = step.get("rotation") or {}
            rotation_type = rotation.get("type")

            if rotation_type == "LL":
                metrics.incrementLLCases()
                metrics.incrementSimpleRightRotations()

            elif rotation_type == "RR":
                metrics.incrementRRCases()
                metrics.incrementSimpleLeftRotations()

            elif rotation_type == "LR":
                metrics.incrementLRCases()
                metrics.incrementSimpleLeftRotations()
                metrics.incrementSimpleRightRotations()

            elif rotation_type == "RL":
                metrics.incrementRLCases()
                metrics.incrementSimpleRightRotations()
                metrics.incrementSimpleLeftRotations()

    def record_operation(
        self,
        observatory,
        action_type,
        before_version,
        before_indicators,
        details=None,
    ):
        after_indicators = self.capture_display(observatory)

        metadata = {
            "metrics_before": before_indicators,
            "metrics_after": after_indicators,
            "metrics_delta": self.calculate_delta(
                before_indicators,
                after_indicators,
            ),
            "details": details or {},
        }

        action = Action(
            action_type=action_type,
            datetime_value=observatory.getClock().getCurrentTime(),
            before_snapshot=before_version,
            metadata=metadata,
        )

        observatory.getActionStack().push(action)

    def calculate_delta(self, before_indicators, after_indicators):
        return {
            "tree": self._calculate_numeric_delta(
                before_indicators["tree"],
                after_indicators["tree"],
            ),
            "counters": self._calculate_numeric_delta(
                before_indicators["counters"],
                after_indicators["counters"],
            ),
        }

    def _calculate_numeric_delta(self, before, after):
        result = {}

        for key, after_value in after.items():
            before_value = before.get(key)

            if isinstance(after_value, (int, float)) and isinstance(
                before_value,
                (int, float),
            ):
                result[key] = after_value - before_value

        return result

    def _reset_traversals(self):
        self._inorder = []
        self._preorder = []
        self._postorder = []
        self._leaves = 0

    def _collect_preorder(self, node):
        if node is None:
            return

        self._preorder.append(node.getValue().getKey())
        self._collect_preorder(node.getLeftChild())
        self._collect_preorder(node.getRightChild())

    def _collect_inorder(self, node):
        if node is None:
            return

        self._collect_inorder(node.getLeftChild())
        self._inorder.append(node.getValue().getKey())

        if node.isLeaf():
            self._leaves += 1

        self._collect_inorder(node.getRightChild())

    def _collect_postorder(self, node):
        if node is None:
            return

        self._collect_postorder(node.getLeftChild())
        self._collect_postorder(node.getRightChild())
        self._postorder.append(node.getValue().getKey())

    def _collect_levels(self, root):
        if root is None:
            return []

        result = []
        queue = [root]
        position = 0

        while position < len(queue):
            node = queue[position]
            position += 1
            result.append(node.getValue().getKey())

            if node.getLeftChild() is not None:
                queue.append(node.getLeftChild())

            if node.getRightChild() is not None:
                queue.append(node.getRightChild())

        return result

    def _height(self, node):
        if node is None:
            return -1
        return node.getHeight()

    def _count_pending(self, node):
        if node is None:
            return 0

        current = 1 if node.getValue().getAttentionStatus() == "pending" else 0

        return (
            current
            + self._count_pending(node.getLeftChild())
            + self._count_pending(node.getRightChild())
        )

    def _count_expensive(self, node):
        if node is None:
            return 0

        current = 1 if node.getValue().getExpensiveAccess() else 0

        return (
            current
            + self._count_expensive(node.getLeftChild())
            + self._count_expensive(node.getRightChild())
        )

    def _count_priorities(self, node, metrics):
        if node is None:
            return

        priority = node.getValue().getKey()[0]
        current = metrics.getEventsByPriority().get(priority, 0)
        metrics.setEventsByPriority(priority, current + 1)

        self._count_priorities(node.getLeftChild(), metrics)
        self._count_priorities(node.getRightChild(), metrics)
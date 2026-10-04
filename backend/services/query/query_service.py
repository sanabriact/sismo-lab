from datetime import datetime, time, timezone

from backend.utils.quantities import parseDatetime


class QueryService:
    """Read-only service for the queries required by the project specification.

    The service deliberately uses simple tree traversals.  This makes the
    number of inspected AVL nodes visible and keeps the academic cost of each
    query easy to explain.  It never changes the observatory.
    """

    def execute(self, observatory, query_type, parameters):
        """Dispatch one validated query to its small, focused method."""
        if query_type == "by_id":
            return self.find_by_id(observatory, parameters.get("event_id"))
        if query_type == "top_pending":
            return self.top_pending(observatory, parameters.get("k"))
        if query_type == "magnitude_range":
            return self.magnitude_range(
                observatory,
                parameters.get("minimum"),
                parameters.get("maximum"),
            )
        if query_type == "date_depth_range":
            return self.date_depth_range(
                observatory,
                parameters.get("start_date"),
                parameters.get("end_date"),
                parameters.get("maximum_depth"),
            )
        if query_type == "associations":
            return self.associations(observatory, parameters.get("event_id"))
        if query_type == "expensive_access":
            return self.expensive_access(observatory)
        raise ValueError("Tipo de consulta no válido")

    def find_by_id(self, observatory, event_id):
        """Find an event in the active tree or either historical collection."""
        event_id = self._positive_integer(event_id, "event_id")
        history = observatory.getHistory()
        active_node = observatory.getAVLTree().index.get(event_id)

        if active_node is not None:
            event = active_node.getValue()
            return self._success({
                "status": "active",
                "event": self._event_data(active_node, event),
            }, 0)

        archived = history.getArchived().get(event_id)
        if archived is not None:
            return self._success({
                "status": "archived",
                "event": self._event_data(None, archived),
            }, 0)

        deleted = history.getDeleted().get(event_id)
        if deleted is not None:
            return self._success({
                "status": "deleted",
                "event": self._event_data(None, deleted),
            }, 0)

        return self._success({"status": "not_found", "event": None}, 0)

    def top_pending(self, observatory, k):
        """Return up to k pending events from greatest K to smallest K.

        The reverse in-order traversal visits the largest AVL keys first.
        Traversal stops as soon as k pending events have been collected.
        """
        k = self._positive_integer(k, "k")
        results = []
        state = {"examined": 0, "finished": False}

        def visit(node):
            if node is None or state["finished"]:
                return

            visit(node.getRightChild())
            if state["finished"]:
                return

            state["examined"] += 1
            event = node.getValue()
            if event.getAttentionStatus() == "pending":
                results.append(self._event_data(node, event))
                if len(results) == k:
                    state["finished"] = True

            visit(node.getLeftChild())

        visit(observatory.getAVLTree().root)
        return self._success({"events": results, "requested": k}, state["examined"])

    def magnitude_range(self, observatory, minimum, maximum):
        """Filter active events by an inclusive magnitude interval.

        Magnitude is the second part of K, while priority is the first part.
        Therefore a magnitude interval is not one contiguous AVL interval.
        The simple and correct strategy is to inspect every active node.
        """
        minimum = self._number(minimum, "minimum")
        maximum = self._number(maximum, "maximum")
        if minimum > maximum:
            raise ValueError("minimum no puede ser mayor que maximum")

        events, examined = self._all_matching(
            observatory,
            lambda event: minimum <= event.getKey()[1] <= maximum,
        )
        return self._success({"events": events}, examined)

    def date_depth_range(self, observatory, start_date, end_date, maximum_depth):
        """Filter active events by inclusive UTC dates and maximum depth."""
        start = self._date_boundary(start_date, False)
        end = self._date_boundary(end_date, True)
        maximum_depth = self._number(maximum_depth, "maximum_depth")
        if start > end:
            raise ValueError("start_date no puede ser posterior a end_date")

        def matches(event):
            occurred = event.getDateTime()
            return start <= occurred <= end and event.getDepth() <= maximum_depth

        events, examined = self._all_matching(observatory, matches)
        return self._success({"events": events}, examined)

    def associations(self, observatory, event_id):
        """Return candidates and selected reference information for one event."""
        event_id = self._positive_integer(event_id, "event_id")
        manager = observatory.getAssociationManager()
        candidates = manager.getCandidates().get(event_id, [])
        selected = manager.getSelectedReferences().get(event_id)

        candidate_events = []
        for candidate_id in candidates:
            event = self._event_by_active_or_archived(observatory, candidate_id)
            if event is not None:
                candidate_events.append(self._event_data(None, event))

        selected_event = None
        if selected is not None:
            event = self._event_by_active_or_archived(observatory, selected)
            if event is not None:
                selected_event = self._event_data(None, event)

        used_by = []
        for dependent_id, reference_id in manager.getSelectedReferences().items():
            if reference_id == event_id:
                dependent = self._event_by_active_or_archived(observatory, dependent_id)
                if dependent is not None:
                    used_by.append(self._event_data(None, dependent))

        return self._success({
            "event_id": event_id,
            "candidates": candidate_events,
            "selected_reference": selected_event,
            "used_by": used_by,
            "window_hours": manager.getW(),
            "distance_limit_km": manager.getR(),
        }, 0)

    def expensive_access(self, observatory):
        """Find high-priority events whose depth is greater than the limit L.

        For every visited node, its depth plus one is the number of nodes that
        a normal BST search would inspect to reach that node.  We calculate it
        during one traversal instead of performing a second search per event.
        """
        limit = observatory.getL()
        results = []

        def visit(node, depth):
            if node is None:
                return

            event = node.getValue()
            if event.getKey()[0] == 3 and depth > limit:
                results.append({
                    "event": self._event_data(node, event),
                    "depth": depth,
                    "limit": limit,
                    "nodes_visited": depth + 1,
                })

            visit(node.getLeftChild(), depth + 1)
            visit(node.getRightChild(), depth + 1)

        visit(observatory.getAVLTree().root, 0)
        return self._success({"events": results, "limit": limit}, 0)

    def _all_matching(self, observatory, predicate):
        """Visit each active node and keep events accepted by predicate."""
        events = []
        examined = 0

        def visit(node):
            nonlocal examined
            if node is None:
                return
            visit(node.getLeftChild())
            examined += 1
            event = node.getValue()
            if predicate(event):
                events.append(self._event_data(node, event))
            visit(node.getRightChild())

        visit(observatory.getAVLTree().root)
        return events, examined

    def _event_by_active_or_archived(self, observatory, event_id):
        """Resolve an association without returning deleted events."""
        node = observatory.getAVLTree().index.get(event_id)
        if node is not None:
            return node.getValue()
        return observatory.getHistory().getArchived().get(event_id)

    def _event_data(self, node, event):
        """Serialize event data plus query-specific structural information."""
        data = event.toDict()
        data["priority"] = event.getKey()[0]
        data["magnitude"] = event.getKey()[1]
        data["event_id"] = event.getKey()[2]

        if node is None:
            data["node_depth"] = None
            data["balance_factor"] = None
        else:
            data["node_depth"] = node.getDepth(0)
            data["balance_factor"] = self._balance_factor(node)
        return data

    def _balance_factor(self, node):
        """Calculate a node balance factor using stored child heights."""
        left_height = node.getLeftChild().getHeight() if node.getLeftChild() else -1
        right_height = node.getRightChild().getHeight() if node.getRightChild() else -1
        return left_height - right_height

    def _positive_integer(self, value, name):
        """Validate a positive integer without accepting booleans."""
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{name} debe ser un entero positivo")
        return value

    def _number(self, value, name):
        """Validate a finite numeric query parameter."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} debe ser numérico")
        return float(value)

    def _date_boundary(self, value, is_end):
        """Parse an ISO date or datetime and normalize it to UTC."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Las fechas son obligatorias")
        try:
            if len(value) == 10:
                parsed_date = datetime.fromisoformat(value).date()
                boundary_time = time.max if is_end else time.min
                return datetime.combine(parsed_date, boundary_time, tzinfo=timezone.utc)
            return parseDatetime(value)
        except (TypeError, ValueError) as error:
            raise ValueError(f"Fecha inválida: {value}") from error

    def _success(self, data, examined_nodes):
        """Build the common response envelope used by every query."""
        return {
            "ok": True,
            **data,
            "examined_nodes": examined_nodes,
        }

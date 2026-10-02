from datetime import timedelta
from math import isfinite


class ArchiveTreeService:
    """Select, preview, and archive an eligible AVL subtree."""

    def __init__(self):
        # Pending selections are isolated by Socket.IO client id.
        self.pending = {}

    @staticmethod
    def _event(node):
        return node.getValue()

    def _collect_ids(self, node):
        if node is None:
            return []
        return (
            [self._event(node).getKey()[2]]
            + self._collect_ids(node.getLeftChild())
            + self._collect_ids(node.getRightChild())
        )

    def _tree_json(self, node):
        if node is None:
            return None
        event = self._event(node)
        return {
            "id": event.getKey()[2],
            "key": list(event.getKey()),
            "event": event.toDict(),
            "left": self._tree_json(node.getLeftChild()),
            "right": self._tree_json(node.getRightChild()),
        }

    def prepare(self, observatory, actual_time, threshold_hours, client_id):
        if isinstance(threshold_hours, bool):
            return {"ok": False, "reason": "invalid_threshold"}
        try:
            hours = float(threshold_hours)
        except (TypeError, ValueError):
            return {"ok": False, "reason": "invalid_threshold"}
        if not isfinite(hours) or hours <= 0:
            return {"ok": False, "reason": "invalid_threshold"}

        threshold = timedelta(hours=hours)
        avl = observatory.getAVLTree()
        selected = avl.archiveSubTree(actual_time, threshold)
        if selected is None:
            self.pending.pop(client_id, None)
            return {"ok": False, "reason": "nothing_to_archive"}
        if isinstance(selected, tuple):
            selected, tree_payload = selected
        else:
            tree_payload = avl.objectToSend(selected, [])
        ids = self._collect_ids(selected)
        tree = self._tree_json(selected)
        self.pending[client_id] = {
            "scenario_id": observatory.scenario_id,
            "ids": ids,
            "root_id": self._event(selected).getKey()[2],
            "tree": tree,
        }
        return {
            "ok": True,
            "tree": {
                "root_id": self._event(selected).getKey()[2],
                "affected_ids": ids,
                "number_nodes": len(ids),
                "message": tree_payload.get("message", "Rama elegible para archivo."),
                "selection": tree_payload,
                "subtree": tree,
            },
        }

    def decide(self, observatory, archive, client_id):
        pending = self.pending.get(client_id)
        if pending is None:
            return {"ok": False, "reason": "no_pending_archive"}
        if not isinstance(archive, bool):
            return {"ok": False, "reason": "invalid_decision"}
        if not archive:
            self.pending.pop(client_id, None)
            return {"ok": True, "archived": False}
        if pending["scenario_id"] != observatory.scenario_id:
            return {"ok": False, "reason": "scenario_changed"}

        avl = observatory.getAVLTree()
        bst = observatory.getBSTTree()
        events = []
        for event_id in pending["ids"]:
            node = avl.searchById(event_id)
            bst_node = bst.searchById(event_id)
            if node is None or bst_node is None:
                return {"ok": False, "reason": "tree_changed"}
            events.append(node.getValue())

        # All IDs were snapshotted before mutation, so AVL rotations cannot
        # alter the selected set while individual removals rebalance the tree.
        for event in events:
            event_id = event.getKey()[2]
            avl_removed = avl.delete(event_id)
            bst_removed = bst.delete(event_id)
            if not avl_removed or not bst_removed:
                return {"ok": False, "reason": "archive_failed", "eventId": event_id}
            event.setEventStatus("archived")
            observatory.getHistory().addArchived(event_id, event)
        observatory.getHistory().addArchivedTree(
        pending["root_id"], pending["ids"], pending["tree"]
        )
        self.pending.pop(client_id, None)

        return {
            "ok": True,
            "archived": True,
            "subtree": {
                "root_id": pending["root_id"],
                "affected_ids": pending["ids"],
                "number_nodes": len(events),
                "tree": pending["tree"],
                "events": [event.toDict() for event in events],
            },
        }

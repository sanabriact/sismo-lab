class JSONExportRepository:
    """Map the live observatory to the portable JSON export contract."""

    def export(self, observatory, parameters):
        tree = observatory.getAVLTree()
        history = observatory.getHistory()
        association_manager = observatory.getAssociationManager()
        events = [node.getValue() for node in tree.index.values()]

        return {
            "load_type": "topology",
            "execution_mode": observatory.getExecutionMode(),
            "datetime": observatory.getClock().getCurrentTimeText(),
            "parameters": dict(parameters),
            "zones": [zone.toDict() for zone in observatory.getZones()],
            "stations": [
                {
                    **station.toDict(),
                    "emmited_events": sorted(
                        event.getKey()[2]
                        for event in events
                        if station.getId() in event.getReportingStations()
                    ),
                }
                for station in observatory.getStations()
            ],
            "tree": {"root": self._node_to_export(tree.root, association_manager)},
            "history": {
                "archived": [
                    self._historical_event_to_export(event, "archived")
                    for event in history.getArchived().values()
                ],
                "eliminated": [
                    self._historical_event_to_export(event, "deleted")
                    for event in history.getDeleted().values()
                ],
                "deletedIds": sorted(history.getDeletedIds()),
                "archivedTrees": history.getArchivedTrees(),
            },
            "report_queue": {
                "items": [
                    self._report_to_export(report)
                    for report in observatory.getReportQueue().items
                ]
            },
            "association_manager": {
                "selection_policy": "highest_magnitude_then_earliest_time_then_lowest_id",
                "candidates": {
                    str(key): list(ids)
                    for key, ids in association_manager.getCandidates().items()
                },
                "selected_references": {
                    str(key): value
                    for key, value in association_manager.getSelectedReferences().items()
                },
            },
            "metrics": observatory.getMetrics().toDict(),
        }

    def _node_to_export(self, node, association_manager):
        if node is None:
            return None
        event = node.getValue()
        data = event.toDict()
        event_id = event.getKey()[2]
        data.update({
            "key": list(event.getKey()),
            "eliminated": event.getEventStatus() == "deleted",
            "archived": event.getEventStatus() == "archived",
            "reference_id": association_manager.getReference(event_id),
        })
        left = node.getLeftChild()
        right = node.getRightChild()
        left_height = left.getHeight() if left else -1
        right_height = right.getHeight() if right else -1
        return {
            "height": node.getHeight(),
            "balance_factor": left_height - right_height,
            "event": data,
            "left_child": self._node_to_export(left, association_manager),
            "right_child": self._node_to_export(right, association_manager),
        }

    @staticmethod
    def _historical_event_to_export(event, status):
        data = event.toDict()
        data["key"] = list(event.getKey())
        data["event_status"] = status
        data["eliminated"] = status == "eliminated"
        data["archived"] = status == "archived"
        return data

    @staticmethod
    def _report_to_export(report):
        return {
            "station_id": report.getStation().getId(),
            "event_id": report.getEventId(),
            "revision": report.getRevision(),
            "magnitude": report.getMagnitude(),
            "epicenter_x": report.getEpicenterX(),
            "epicenter_y": report.getEpicenterY(),
            "depth": report.getDepth(),
            "datetime": report.getDatetime().isoformat(),
        }

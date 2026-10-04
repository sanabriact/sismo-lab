class HistoryService:
    """Provide read-only access to events stored in the observatory history."""

    def get_summary(self, observatory):
        """Return the historical counters used by the history landing page."""
        history = observatory.getHistory()
        return {
            "archived_events": len(history.getArchived()),
            "deleted_events": len(history.getDeleted()),
            "historical_ids": len(history.listHistoricIds),
        }

    def get_archived_events(self, observatory):
        """Serialize archived events in a stable identifier order."""
        archived = observatory.getHistory().getArchived()
        events = []
        for event_id in sorted(archived.keys()):
            event = archived[event_id]
            data = event.toDict()
            data["event_id"] = event_id
            data["priority"] = event.getKey()[0]
            data["magnitude"] = event.getKey()[1]
            events.append(data)
        return events

    def get_deleted_events(self, observatory):
        """Serialize events marked as deleted in a stable identifier order."""
        deleted = observatory.getHistory().getDeleted()
        events = []
        for event_id in sorted(deleted.keys()):
            event = deleted[event_id]
            data = event.toDict()
            data["event_id"] = event_id
            data["priority"] = event.getKey()[0]
            data["magnitude"] = event.getKey()[1]
            events.append(data)
        return events

    def get_historical_ids(self, observatory):
        """Return every identifier registered by the historical index."""
        return sorted(observatory.getHistory().listHistoricIds)

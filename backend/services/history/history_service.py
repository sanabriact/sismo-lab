class HistoryService:

    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------

    # Return the historical counters used by the history landing page
    def get_summary(self, observatory):
        history = observatory.getHistory()
        return {
            "archived_events": len(history.getArchived()),
            "deleted_events": len(history.getDeleted()),
            "historical_ids": len(history.listHistoricIds),
        }

    # -------------------------------------------------------------------------
    # Event listings
    # -------------------------------------------------------------------------

    # Serialize archived events in a stable identifier order
    def get_archived_events(self, observatory):
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

    # Serialize events marked as deleted in a stable identifier order
    def get_deleted_events(self, observatory):
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

    # -------------------------------------------------------------------------
    # Historical ids
    # -------------------------------------------------------------------------

    # Return every identifier registered by the historical index
    def get_historical_ids(self, observatory):
        return sorted(observatory.getHistory().listHistoricIds)
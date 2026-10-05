"""Associations between seismic events, independent from AVL topology."""

from math import hypot, isfinite
from backend.utils.quantities import normalizeDatetime

class AssociationManager:
    def __init__(self, w=48.0, r=40.0):
        self.W = self._validate_limit(w, "W")  # hours
        self.R = self._validate_limit(r, "R")  # kilometres
        self.candidates = {}          # {replica_id: [reference_id, ...]}
        self.selected_references = {} # {replica_id: reference_id}

    @staticmethod
    def _validate_limit(value, name):
        if isinstance(value, bool):
            raise ValueError(f"{name} debe ser un número positivo")
        try:
            value = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{name} debe ser un número positivo") from error
        if not isfinite(value) or value <= 0:
            raise ValueError(f"{name} debe ser un número positivo")
        return value

    def getW(self):
        return self.W

    def setW(self, w):
        self.W = self._validate_limit(w, "W")

    def getR(self):
        return self.R

    def setR(self, r):
        self.R = self._validate_limit(r, "R")

    def setLimits(self, w=None, r=None):
        """Validate both new limits before changing either one."""
        new_w = self.W if w is None else self._validate_limit(w, "W")
        new_r = self.R if r is None else self._validate_limit(r, "R")
        self.W, self.R = new_w, new_r

    def getLimits(self):
        """Return the current association limits in one small object."""
        return {"W": self.W, "R": self.R}

    def getCandidates(self):
        return self.candidates

    def getCandidate(self, key):
        return self.candidates.get(key, [])

    def getSelectedReferences(self):
        return self.selected_references

    def getReference(self, key):
        return self.selected_references.get(key)

    def getDependents(self, reference_id):
        """Return event IDs that currently use reference_id."""
        dependents = []
        for event_id, selected_id in self.selected_references.items():
            if selected_id == reference_id:
                dependents.append(event_id)
        return dependents

    @staticmethod
    def _event_id(event):
        return event.getKey()[2]

    @staticmethod
    def _magnitude(event):
        return event.getKey()[1]

    @staticmethod
    def _time(event):
        return normalizeDatetime(event.getDateTime())

    def _is_candidate(self, reference, replica):
        """Apply every mandatory candidate condition from requirement §8."""
        if self._magnitude(reference) <= self._magnitude(replica):
            return False
        reference_time = self._time(reference)
        replica_time = self._time(replica)
        if reference_time >= replica_time:  # strictly earlier
            return False
        hours = (replica_time - reference_time).total_seconds() / 3600
        if hours > self.W:
            return False
        distance = hypot(
            reference.getEpicenterX() - replica.getEpicenterX(),
            reference.getEpicenterY() - replica.getEpicenterY(),
        )
        return distance <= self.R

    @classmethod
    def _selection_key(cls, event):
        """Highest M, then earliest occurrence, then lowest id wins.

        This declared policy uses only event data, never arrival order or AVL
        topology. Strict temporal ordering also makes cycles impossible.
        """
        return (-cls._magnitude(event), cls._time(event), cls._event_id(event))

    def recalculate(self, active_events, archived_events):
        """Rebuild all association maps from active and archived events.

        Rebuilding from the complete event set keeps the rules easy to read
        and prevents stale candidates after an event update or deletion.
        Deleted events are intentionally excluded from the input set.
        """
        events_by_id = {}
        for event in list(active_events) + list(archived_events):
            if event.getEventStatus() != "deleted":
                events_by_id[self._event_id(event)] = event

        candidates = {}
        references = {}
        events = list(events_by_id.values())
        for replica in events:
            replica_id = self._event_id(replica)
            eligible = [
                reference for reference in events
                if reference is not replica and self._is_candidate(reference, replica)
            ]
            eligible.sort(key=self._selection_key)
            candidates[replica_id] = [self._event_id(event) for event in eligible]
            if eligible:
                references[replica_id] = self._event_id(eligible[0])

        self.candidates = candidates
        self.selected_references = references
    def toDict(self):
        return {
            "W": self.W,
            "R": self.R,
            "candidates": {str(key): list(ids) for key, ids in self.candidates.items()},
            "selected_references": {str(key): value for key, value in self.selected_references.items()},
            "selection_policy": "highest_magnitude_then_earliest_time_then_lowest_id",
        }

    @classmethod
    def fromDict(cls, data):
        data = data or {}
        manager = cls(data.get("W", 48.0), data.get("R", 40.0))
        manager.candidates = {
            int(key): [int(item) for item in ids]
            for key, ids in data.get("candidates", {}).items()
        }
        manager.selected_references = {
            int(key): int(value)
            for key, value in data.get("selected_references", {}).items()
        }
        return manager

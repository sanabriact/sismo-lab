
class Metrics:

    # Initialize every counter in zero
    def __init__(self):
        self.active_events = 0
        self.historical_events = 0
        self.events_by_priority = {1: 0, 2: 0, 3: 0}   # priority -> count
        self.pending_attention = 0
        self.high_cost_access_events = 0

        self.accepted_corrections = 0
        self.discarded_reports = 0
        self.conflicts = 0
        self.mass_archives = 0
        self.archived_events = 0

        self.ll_cases = 0
        self.rr_cases = 0
        self.lr_cases = 0
        self.rl_cases = 0
        self.simple_left_rotations = 0
        self.simple_right_rotations = 0

    # -------------------------------------------------------------------------
    # Counters of the current state of the events
    # -------------------------------------------------------------------------

    # Get the number of active events
    def getActiveEvents(self):
        return self.active_events

    # Set the number of active events
    def setActiveEvents(self, count):
        self.active_events = count

    # Add one to the number of active events
    def incrementActiveEvents(self):
        self.active_events += 1

    # ------------------------------------------------------------------

    # Get the number of historical events
    def getHistoricalEvents(self):
        return self.historical_events

    # Set the number of historical events
    def setHistoricalEvents(self, count):
        self.historical_events = count

    # Add one to the number of historical events
    def incrementHistoricalEvents(self):
        self.historical_events += 1

    # ------------------------------------------------------------------

    # Get the number of events of each priority
    def getEventsByPriority(self):
        return self.events_by_priority

    # Set the number of events of one priority (1, 2 or 3)
    def setEventsByPriority(self, priority, count):
        if priority in self.events_by_priority:
            self.events_by_priority[priority] = count
        else:
            raise ValueError("Invalid priority level. Must be 1, 2, or 3.")

    # Add one to the number of events of one priority (1, 2 or 3)
    def incrementEventsByPriority(self, priority):
        if priority in self.events_by_priority:
            self.events_by_priority[priority] += 1
        else:
            raise ValueError("Invalid priority level. Must be 1, 2, or 3.")

    # ------------------------------------------------------------------

    # Get the number of events pending attention
    def getPendingAttention(self):
        return self.pending_attention

    # Set the number of events pending attention
    def setPendingAttention(self, count):
        self.pending_attention = count

    # Add one to the number of events pending attention
    def incrementPendingAttention(self):
        self.pending_attention += 1

    # ------------------------------------------------------------------

    # Get the number of events with expensive access
    def getHighCostAccessEvents(self):
        return self.high_cost_access_events

    # Set the number of events with expensive access
    def setHighCostAccessEvents(self, count):
        self.high_cost_access_events = count

    # Add one to the number of events with expensive access
    def incrementHighCostAccessEvents(self):
        self.high_cost_access_events += 1

    # ------------------------------------------------------------------
    # Counters of the processed reports
    # ------------------------------------------------------------------

    # Get the number of accepted corrections
    def getAcceptedCorrections(self):
        return self.accepted_corrections

    # Set the number of accepted corrections
    def setAcceptedCorrections(self, count):
        self.accepted_corrections = count

    # Add one to the number of accepted corrections
    def incrementAcceptedCorrections(self):
        self.accepted_corrections += 1

    # ------------------------------------------------------------------

    # Get the number of discarded reports
    def getDiscardedReports(self):
        return self.discarded_reports

    # Set the number of discarded reports
    def setDiscardedReports(self, count):
        self.discarded_reports = count

    # Add one to the number of discarded reports
    def incrementDiscardedReports(self):
        self.discarded_reports += 1

    # ------------------------------------------------------------------

    # Get the number of conflicts
    def getConflicts(self):
        return self.conflicts

    # Set the number of conflicts
    def setConflicts(self, count):
        self.conflicts = count

    # Add one to the number of conflicts
    def incrementConflicts(self):
        self.conflicts += 1

    # ------------------------------------------------------------------
    # Counters of the archiving
    # ------------------------------------------------------------------

    # Get the number of mass archives
    def getMassArchives(self):
        return self.mass_archives

    # Set the number of mass archives
    def setMassArchives(self, count):
        self.mass_archives = count

    # Add one to the number of mass archives
    def incrementMassArchives(self):
        self.mass_archives += 1

    # ------------------------------------------------------------------

    # Get the number of archived events
    def getArchivedEvents(self):
        return self.archived_events

    # Set the number of archived events
    def setArchivedEvents(self, count):
        self.archived_events = count

    # Add one to the number of archived events
    def incrementArchivedEvents(self):
        self.archived_events += 1

    # ------------------------------------------------------------------
    # Counters of the AVL balancing
    # ------------------------------------------------------------------

    # Get the number of left-left cases
    def getLLCases(self):
        return self.ll_cases

    # Set the number of left-left cases
    def setLLCases(self, count):
        self.ll_cases = count

    # Add one to the number of left-left cases
    def incrementLLCases(self):
        self.ll_cases += 1

    # ------------------------------------------------------------------

    # Get the number of right-right cases
    def getRRCases(self):
        return self.rr_cases

    # Set the number of right-right cases
    def setRRCases(self, count):
        self.rr_cases = count

    # Add one to the number of right-right cases
    def incrementRRCases(self):
        self.rr_cases += 1

    # ------------------------------------------------------------------

    # Get the number of left-right cases
    def getLRCases(self):
        return self.lr_cases

    # Set the number of left-right cases
    def setLRCases(self, count):
        self.lr_cases = count

    # Add one to the number of left-right cases
    def incrementLRCases(self):
        self.lr_cases += 1

    # ------------------------------------------------------------------

    # Get the number of right-left cases
    def getRLCases(self):
        return self.rl_cases

    # Set the number of right-left cases
    def setRLCases(self, count):
        self.rl_cases = count

    # Add one to the number of right-left cases
    def incrementRLCases(self):
        self.rl_cases += 1

    # ------------------------------------------------------------------

    # Get the number of simple left rotations
    def getSimpleLeftRotations(self):
        return self.simple_left_rotations

    # Set the number of simple left rotations
    def setSimpleLeftRotations(self, count):
        self.simple_left_rotations = count

    # Add one to the number of simple left rotations
    def incrementSimpleLeftRotations(self):
        self.simple_left_rotations += 1

    # ------------------------------------------------------------------

    # Get the number of simple right rotations
    def getSimpleRightRotations(self):
        return self.simple_right_rotations

    # Set the number of simple right rotations
    def setSimpleRightRotations(self, count):
        self.simple_right_rotations = count

    # Add one to the number of simple right rotations
    def incrementSimpleRightRotations(self):
        self.simple_right_rotations += 1

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    # Convert object to dictionary
    def toDict(self):
        return {
            "active_events": self.active_events,
            "historical_events": self.historical_events,
            "events_by_priority": dict(self.events_by_priority),
            "pending_attention": self.pending_attention,
            "high_cost_access_events": self.high_cost_access_events,
            "accepted_corrections": self.accepted_corrections,
            "discarded_reports": self.discarded_reports,
            "conflicts": self.conflicts,
            "mass_archives": self.mass_archives,
            "archived_events": self.archived_events,
            "ll_cases": self.ll_cases,
            "rr_cases": self.rr_cases,
            "rl_cases": self.rl_cases,
            "lr_cases": self.lr_cases,
            "simple_left_rotations": self.simple_left_rotations,
            "simple_right_rotations": self.simple_right_rotations
        }

    # Convert dictionary to object
    @classmethod
    def fromDict(cls, data):
        metrics = cls()
        metrics.active_events = data["active_events"]
        metrics.historical_events = data["historical_events"]
        metrics.events_by_priority = {
            int(key): value
            for key, value in data["events_by_priority"].items()
        }
        metrics.pending_attention = data["pending_attention"]
        metrics.high_cost_access_events = data["high_cost_access_events"]
        metrics.accepted_corrections = data["accepted_corrections"]
        metrics.discarded_reports = data["discarded_reports"]
        metrics.conflicts = data["conflicts"]
        metrics.mass_archives = data["mass_archives"]
        metrics.archived_events = data["archived_events"]
        metrics.ll_cases = data["ll_cases"]
        metrics.rr_cases = data["rr_cases"]
        metrics.rl_cases = data["rl_cases"]
        metrics.lr_cases = data["lr_cases"]
        metrics.simple_left_rotations = data["simple_left_rotations"]
        metrics.simple_right_rotations = data["simple_right_rotations"]

        return metrics
class Metrics:
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


    def getActiveEvents(self):
        return self.active_events
    def setActiveEvents(self, count):
        self.active_events = count
    def incrementActiveEvents(self):
        self.active_events += 1

    def getHistoricalEvents(self):
        return self.historical_events
    def setHistoricalEvents(self, count):
        self.historical_events = count
    def incrementHistoricalEvents(self):
        self.historical_events += 1

    def getEventsByPriority(self):
        return self.events_by_priority
    def setEventsByPriority(self, priority, count):
        if priority in self.events_by_priority:
            self.events_by_priority[priority] = count
        else:
            raise ValueError("Invalid priority level. Must be 1, 2, or 3.")
    def incrementEventsByPriority(self, priority):
        if priority in self.events_by_priority:
            self.events_by_priority[priority] += 1
        else:
            raise ValueError("Invalid priority level. Must be 1, 2, or 3.")

    def getPendingAttention(self):
        return self.pending_attention
    def setPendingAttention(self, count):
        self.pending_attention = count
    def incrementPendingAttention(self):
        self.pending_attention += 1

    def getHighCostAccessEvents(self):
        return self.high_cost_access_events    
    def setHighCostAccessEvents(self, count):
        self.high_cost_access_events = count   
    def incrementHighCostAccessEvents(self):
        self.high_cost_access_events += 1

    def getAcceptedCorrections(self):
        return self.accepted_corrections
    def setAcceptedCorrections(self, count):
        self.accepted_corrections = count
    def incrementAcceptedCorrections(self):
        self.accepted_corrections += 1

    def getDiscardedReports(self):
        return self.discarded_reports   
    def setDiscardedReports(self, count):
        self.discarded_reports = count   
    def incrementDiscardedReports(self):
        self.discarded_reports += 1

    def getConflicts(self):
        return self.conflicts   
    def setConflicts(self, count):
        self.conflicts = count
    def incrementConflicts(self):
        self.conflicts += 1

    def getMassArchives(self):
        return self.mass_archives   
    def setMassArchives(self, count):
        self.mass_archives = count   
    def incrementMassArchives(self):
        self.mass_archives += 1

    def getArchivedEvents(self):
        return self.archived_events
    def setArchivedEvents(self, count):
        self.archived_events = count
    def incrementArchivedEvents(self):
        self.archived_events += 1

    def getLLCases(self):
        return self.ll_cases
    def setLLCases(self, count):
        self.ll_cases = count
    def incrementLLCases(self):
        self.ll_cases += 1

    def getRRCases(self):
        return self.rr_cases 
    def setRRCases(self, count):
        self.rr_cases = count
    def incrementRRCases(self):
            self.rr_cases += 1

    def getLRCases(self):
        return self.lr_cases
    def setLRCases(self, count):
        self.lr_cases = count
    def incrementLRCases(self):
            self.lr_cases += 1

    def getRLCases(self):
        return self.rl_cases
    def setRLCases(self, count):
        self.rl_cases = count
    def incrementRLCases(self):
            self.rl_cases += 1

    def getSimpleLeftRotations(self):
        return self.simple_left_rotations   
    def setSimpleLeftRotations(self, count):
        self.simple_left_rotations = count 
    def incrementSimpleLeftRotations(self):
        self.simple_left_rotations += 1

    def getSimpleRightRotations(self):
        return self.simple_right_rotations
    def setSimpleRightRotations(self, count):
        self.simple_right_rotations = count
    def incrementSimpleRightRotations(self):
        self.simple_right_rotations += 1
        
    def toDict(self):
        return {
            "active_events": self.active_events,
            "historical_events": self.historical_events,
            "events_by_priority":self.events_by_priority,
            "pending_attention":self.pending_attention,
            "high_cost_access_events":self.high_cost_access_events,
            "accepted_corrections":self.accepted_corrections,
            "discarded_reports":self.discarded_reports,
            "conflicts":self.conflicts,
            "mass_archives":self.mass_archives,
            "archived_events":self.archived_events,
            "ll_cases":self.ll_cases,
            "rr_cases":self.rr_cases,
            "rl_cases":self.rl_cases,
            "lr_cases":self.lr_cases,
            "simple_left_rotations":self.simple_left_rotations,
            "simple_right_rotations":self.simple_right_rotations
        }
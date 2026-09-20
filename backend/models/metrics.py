class Metrics:
    def __init__(self):
        self.activeEvents = 0
        self.historicalEvents = 0
        self.eventsByPriority = {1: 0, 2: 0, 3: 0}   # priority -> count
        self.pendingAttention = 0
        self.highCostAccessEvents = 0

        self.acceptedCorrections = 0
        self.discardedReports = 0
        self.conflicts = 0
        self.massArchives = 0
        self.archivedEvents = 0

        self.llCases = 0
        self.rrCases = 0
        self.lrCases = 0
        self.rlCases = 0
        self.simpleLeftRotations = 0
        self.simpleRightRotations = 0

    def getActiveEvents(self):
        return self.activeEvents
    def setActiveEvents(self, count):
        self.activeEvents = count
    def incrementActiveEvents(self):
        self.activeEvents += 1

    def getHistoricalEvents(self):
        return self.historicalEvents
    def setHistoricalEvents(self, count):
        self.historicalEvents = count
    def incrementHistoricalEvents(self):
        self.historicalEvents += 1

    def getEventsByPriority(self):
        return self.eventsByPriority
    def setEventsByPriority(self, priority, count):
        if priority in self.eventsByPriority:
            self.eventsByPriority[priority] = count
        else:
            raise ValueError("Invalid priority level. Must be 1, 2, or 3.")
    def incrementEventsByPriority(self, priority):
        if priority in self.eventsByPriority:
            self.eventsByPriority[priority] += 1
        else:
            raise ValueError("Invalid priority level. Must be 1, 2, or 3.")

    def getPendingAttention(self):
        return self.pendingAttention
    def setPendingAttention(self, count):
        self.pendingAttention = count
    def incrementPendingAttention(self):
        self.pendingAttention += 1

    def getHighCostAccessEvents(self):
        return self.highCostAccessEvents    
    def setHighCostAccessEvents(self, count):
        self.highCostAccessEvents = count   
    def incrementHighCostAccessEvents(self):
        self.highCostAccessEvents += 1

    def getAcceptedCorrections(self):
        return self.acceptedCorrections
    def setAcceptedCorrections(self, count):
        self.acceptedCorrections = count
    def incrementAcceptedCorrections(self):
        self.acceptedCorrections += 1

    def getDiscardedReports(self):
        return self.discardedReports    
    def setDiscardedReports(self, count):
        self.discardedReports = count   
    def incrementDiscardedReports(self):
        self.discardedReports += 1

    def getConflicts(self):
        return self.conflicts   
    def setConflicts(self, count):
        self.conflicts = count
    def incrementConflicts(self):
        self.conflicts += 1

    def getMassArchives(self):
        return self.massArchives    
    def setMassArchives(self, count):
        self.massArchives = count   
    def incrementMassArchives(self):
        self.massArchives += 1

    def getArchivedEvents(self):
        return self.archivedEvents
    def setArchivedEvents(self, count):
        self.archivedEvents = count
    def incrementArchivedEvents(self):
        self.archivedEvents += 1

    def getLLCases(self):
        return self.llCases
    def setLLCases(self, count):
        self.llCases = count
    def incrementLLCases(self):
        self.llCases += 1

    def getRRCases(self):
        return self.rrCases 
    def setRRCases(self, count):
        self.rrCases = count
    def incrementRRCases(self):
            self.rrCases += 1

    def getLRCases(self):
        return self.lrCases 
    def setLRCases(self, count):
        self.lrCases = count
    def incrementLRCases(self):
            self.lrCases += 1

    def getRLCases(self):
        return self.rlCases 
    def setRLCases(self, count):
        self.rlCases = count
    def incrementRLCases(self):
            self.rlCases += 1

    def getSimpleLeftRotations(self):
        return self.simpleLeftRotations    
    def setSimpleLeftRotations(self, count):
        self.simpleLeftRotations = count 
    def incrementSimpleLeftRotations(self):
        self.simpleLeftRotations += 1

    def getSimpleRightRotations(self):
        return self.simpleRightRotations
    def setSimpleRightRotations(self, count):
        self.simpleRightRotations = count
    def incrementSimpleRightRotations(self):
        self.simpleRightRotations += 1
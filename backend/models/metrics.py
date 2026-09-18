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

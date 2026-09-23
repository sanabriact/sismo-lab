from datetime import datetime
class SimulationClock:
    def __init__(self, current_time: datetime):
        self.current_time = current_time

    def getCurrentTime(self):
        return self.current_time
    def setCurrentTime(self, time):
        self.current_time = time
    def toDict(self):
        return {
            "current_time": self.current_time.isoformat()
        }
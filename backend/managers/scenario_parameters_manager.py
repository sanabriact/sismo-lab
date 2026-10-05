
class ScenarioParametersManager:
    
    def _init(self):
        self.L = 3,
        self.W = 48,
        self.R = 40,
        self.T = 72,
        
    def getL(self):
        return self.L
    def setL(self, L):
        self.L = L
        
    def getW(self):
        return self.W
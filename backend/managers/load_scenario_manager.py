from backend.models.event import Event
from backend.services.seismic_observatory_service import SeismicObservatoryService

class LoadScenarioManager:
    
    # Method to load the scenario
    def load(self, data):
        if not isinstance(data, dict):
            return None
        else:
            self.caseScenary(data)
    
    # Method to see the case of scenario
    def caseScenary(self, data):
        match data.get("load_type"):
            case "insertion":
                if self.comprobateJson():
                    self.addEvents(data["events"])
                    return data
                else:
                    return None
            case "topology":
                if self.comprobateJson():
                    self.comprobateTree(data["tree"])
                    events = []
                    result = self.createArchive(data, events)
                    return result

    # Method to comprobate if json is usable
    def comprobateJson(self, data):
        required_fields = ["datetime", "zones", "stations", "events"]
        for field in required_fields:
            if field not in data:
                return False
        return True
    
    # Method to add events to trees
    def addEvents(self, event_list):
        observatory_service = SeismicObservatoryService()
        observatory = observatory_service.getObservatory()
        avl = observatory.getAVLTree()
        bst = observatory.getBSTTree()
        for e in event_list:
            event = Event.fromDict(e)
            avl.insert(event)
            bst.insert(event)
    
    # Method to comprobate if tree is usable
    def comprobateTree(self, tree):
        a = 0
    
    # Method to create archive to return to frontend
    def createArchive(self, data, events):
        result = {}
        result["datetime"] = data["datetime"]
        result["zones"] = data["zones"]
        result["stations"] = data["stations"]
        result["events"] = events
        return result
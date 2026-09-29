
class LoadScenarioManager:
    def load(self, data):
        if not isinstance(data, dict):
            return None
        else:
            return self.caseScenary(data)
        
    def caseScenary(self, data):
        match data.get("load_type"):
            case "insertion":
                if self.comprobateJson():
                    list_events = data["events"]
                    
                else:
                    return None

    def comprobateJson(self, data):
        required_fields = ["datetime", "zones", "stations", "events"]
        for field in required_fields:
            if field not in data:
                return False
        return True

            


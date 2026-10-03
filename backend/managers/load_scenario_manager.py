import json
from datetime import datetime
from backend.services.seismic_observatory_service import SeismicObservatoryService
from backend.repositories.json_scenario_repository import JsonScenarioRepository
from backend.models.event import Event
from backend.utils.quantities import parseDatetime
class LoadScenarioManager:
    
    def __init__(self):
        self.errors = []
        self.eventIds = set()
        self.repository = JsonScenarioRepository()
    
    # Method to load the scenario
    def load(self, data, stress_mode):
        self.errors = []
        if not isinstance(data, dict):
            self.errors.append("invalid format of the json")
            return None
        else:
            return self.caseScenary(data, stress_mode)
    
    def loadFromFile(self, filepath, stress_mode):
        self.errors = []
        data = self.repository.load(filepath)
        if data is None:
            self.errors.append(self.repository.error)
            return None
        try:
            return self.load(
                data,
                stress_mode or data.get("execution_mode") == "stress",
            )
        except (AttributeError, IndexError, KeyError, TypeError, ValueError) as error:
            self.errors.append(f"invalid scenario data: {error}")
            return None

    def loadFromText(self, content, stress_mode=False):
        """Validate JSON content received from an uploaded scenario file."""
        self.errors = []
        if not isinstance(content, str) or not content.strip():
            self.errors.append("the json file is empty")
            return None
        try:
            data = json.loads(content, object_pairs_hook=self.repository._rejectDuplicateKeys)
        except json.JSONDecodeError as error:
            self.errors.append(
                f"Invalid JSON at line {error.lineno}, column {error.colno}: {error.msg}"
            )
            return None
        except ValueError as error:
            self.errors.append(str(error))
            return None
        if not isinstance(data, dict):
            self.errors.append("invalid format of the json")
            return None
        if "load_type" not in data:
            data = {
                **data,
                "load_type": "topology" if "tree" in data else "insertion",
            }
        try:
            return self.load(
                data,
                stress_mode or data.get("execution_mode") == "stress",
            )
        except (AttributeError, IndexError, KeyError, TypeError, ValueError) as error:
            self.errors.append(f"invalid scenario data: {error}")
            return None
    
    # Method to see the case of scenario
    def caseScenary(self, data, stress_mode):
        match data.get("load_type"):
            case "insertion":
                if self.comprobateJson(data):
                    return data
                else:
                    return None
            case "topology":
                if self.comprobateJsonTopology(data):
                    if self.comprobateTree(data, stress_mode):
                        events = self.getEvents(data["tree"]["root"], [])
                        self.addEvents(events)
                        result = self.createArchive(data, events)
                        return result
                    return None
                else:
                    return None
            case _:
                self.errors.append("load_type must be 'insertion' or 'topology'")
                return None

    # Method to comprobate if json is usable
    def comprobateJson(self, data):
        required_fields = ["datetime", "zones", "stations", "events"]
        for field in required_fields:
            if field not in data:
                self.errors.append("data not has a required fields")
                return False

        if not isinstance(data["events"], list):
            self.errors.append("events must be a list")
            return False

        # Insertion scenarios sent by the current API use the event fields
        # consumed by SeismicObservatoryService. Legacy tree events are also
        # accepted when the manager is used directly with old scenario files.
        event_fields = ("id", "magnitude", "depth", "epicenter_x", "epicenter_y", "datetime", "station")
        for event in data["events"]:
            if not isinstance(event, dict):
                self.errors.append("each event must be an object")
                return False
            if "key" not in event and any(field not in event for field in event_fields):
                self.errors.append("an insertion event has missing required fields")
                return False

        return True
    
    # Method to comprobate if json is usable
    def comprobateJsonTopology(self, data):
        required_fields = ["datetime", "zones", "stations", "tree"]
        for field in required_fields:
            if field not in data:
                self.errors.append("data not has a required fields")
                return False
        return True

    # Method to add events to trees
    def addEvents(self, event_list):
        observatory_service = SeismicObservatoryService()
        observatory = observatory_service.getObservatory()
        history = observatory.getHistory()
        avl = observatory.getAVLTree()
        bst = observatory.getBSTTree()
        for e in event_list:
            event = Event.fromDict(e)
            history.addIdEvent(e["key"][2])
            avl.insert(event)
            bst.insert(event)
    
    # Method to comprobate if tree is usable
    def comprobateTree(self, data, stress_mode):
        self.eventIds = []
        
        if not (
            self.validateDataTree(data["tree"]) and
            self.validateAutenticityIds(data["tree"]["root"], self.eventIds) and
            self.validateOrder(data["tree"]["root"], None, None)
            ):
            return False
        
        if not stress_mode:
            if not self.validateBalance(data["tree"]["root"]):
                return False

        return (
            self.validateReferences(data) and
            self.validatePriority(data["tree"]["root"], data["zones"])
        )
    
    def validateDataTree(self, tree):
            if not isinstance(tree, dict):
                self.errors.append("'tree' must be an object.")
                return False
            root = "root"
            if root not in tree:
                self.errors.append("'tree' has no root")
                return False
            for key in tree:
                if key != "root":
                    self.errors.append(f"{key} shouldn't belong to the same root level")
                    return False
            return self.validateData(tree["root"])
        
    def validateDataRootFields(self, currentRoot):
        if not isinstance(currentRoot, dict):
            self.errors.append("a node must be an object or null")
            return False
        required_fields= ["event", "left_child", "right_child"]
        for field in required_fields:
            if field not in currentRoot:
                self.errors.append("root not has a necesary required files")
                return False
            if field == "event":
                 if not self.validateDataEventFields(currentRoot["event"]):
                    return False
        return True
                
    def validateDataEventFields(self, event):
        if not isinstance(event, dict):
            self.errors.append("'event' must be an object")
            return False
        required_fields = ["key", "epicenter_x", "epicenter_y", "depth", "datetime", "revision", "reporting_stations", "attention_status", "event_status", "populated_zone", "expensive_access", "eliminated", "archived"]
        for field in required_fields:
            if field not in event:
                self.errors.append(f"event not has a requeried fields: {field}")
                return False
            if field == "key":
                if not self.validateDataKey(event["key"]):
                    self.errors.append(f"key no has a required fields: {field}")
                    return False
        return True
    
    def validateDataKey(self, key):
        try:
            if len(key) != 3:
                return False
            for i in key:
                if not isinstance(i, (int, float)):
                    return False
            return True
        except Exception:
            return False
        
    def validateData(self, currentRoot):
        if currentRoot is not None:
            if self.validateDataRootFields(currentRoot):
                event = currentRoot["event"]
                id = event["key"][2]
                magnitude = event["key"][1]
                depth = event["depth"]
                epicenter_x =  event["epicenter_x"]
                epicenter_y = event["epicenter_y"]
                try:
                    date = parseDatetime(event["datetime"])
                    self._validateData(id, magnitude, depth, epicenter_x, epicenter_y, date)
                except (ValueError, TypeError) as e:
                    self.errors.append("the data are invalid")
                    return False
                left_child= self.validateData(currentRoot["left_child"])
                right_child = self.validateData(currentRoot["right_child"])
                return left_child and right_child
            else:
                return False
        return True
    
    def _validateData(self, id, magnitude, depth, epicenter_x, epicenter_y, date):
            if not (-2 <= magnitude <= 10):
                raise ValueError("magnitud debe estar entre -2 y 10")
            if not isinstance(id, int) or not (1 <= id <= 999999):
                raise ValueError("Id debe estar entre 1 y 999999")
            if not (0 <= depth <= 700):
                raise ValueError("Profundidad debe estar entre 0 y 700")
            if not (0 <= epicenter_x <= 1000) or not (0 <= epicenter_y <= 1000):
                raise ValueError("Epicentro debe estar entre 0 y 1000")
            if not isinstance(date, datetime):
                raise TypeError("La fecha debe ser de tipo datetime")

    def validateAutenticityIds(self, currentRoot, list_ids):
        if currentRoot is not None:
            event = currentRoot["event"]
            id = event["key"][2]
            if id in list_ids:
                self.errors.append(f"this {id} already existing in another event")
                return False
            list_ids.append(id)
            left_child = self.validateAutenticityIds(currentRoot["left_child"], list_ids)
            right_child = self.validateAutenticityIds(currentRoot["right_child"], list_ids)
            return left_child and right_child
        else:
            return True
        
    def validateReferences(self, data):
        stationIds = self.getStationIds(data["stations"])
        return (
            self.validateEventStations(data["tree"]["root"], stationIds)
            and self.validateStationEvents(data["stations"])
        )

    def getStationIds(self, stations):
        stationIds = set()
        for station in stations:
            stationIds.add(station["id"])
        return stationIds
    
    def validateEventStations(self, currentRoot, stationIds):
        if currentRoot is not None:
            event = currentRoot["event"]
            eventId = event["key"][2]
            for stationId in event["reporting_stations"]:
                if stationId not in stationIds:
                    self.errors.append(f"Event {eventId} references unknown station {stationId}")
                    return False
            return (
                self.validateEventStations(currentRoot["left_child"], stationIds)
                and self.validateEventStations(currentRoot["right_child"], stationIds)
            )
        return True
    
    def validateStationEvents(self, stations):
        valid = True
        for station in stations:
            for eventId in station["emmited_events"]:
                if eventId not in self.eventIds:
                    self.errors.append(f"Station {station['id']} references unknown event {eventId}")
                    valid = False
        return valid
            
    # Method to create archive to return to frontend, completar
    def createArchive(self, data, events):
        result = {}
        result["datetime"] = data["datetime"]
        result["zones"] = data["zones"]
        result["stations"] = data["stations"]
        result["events"] = events
        return result

    def validatePriority(self, currentRoot, zones):
        if currentRoot is not None:
            event = currentRoot["event"]
            key = event["key"]
            storedPriority = key[0]
            magnitude = key[1]
            eventId = key[2]
            depth = event["depth"]
            valid = True
            populated = self.isPopulatedZone(event["epicenter_x"], event["epicenter_y"], zones)
            calculatedPriority = self.calculatePriority(magnitude, depth, populated)
            if storedPriority != calculatedPriority:
                self.errors.append(
                    f"Event {eventId}: stored priority: {storedPriority}, not is correct, real priority: {calculatedPriority}"
                )
                valid = False
            if event["populated_zone"] != populated:
                self.errors.append(
                    f"Event {eventId}: populated_zone is : {event['populated_zone']},not is correct, real populated_zona: {populated}"
                )
                valid = False
            left_child = self.validatePriority(currentRoot["left_child"], zones)
            rigth_child = self.validatePriority(currentRoot["right_child"], zones)
            return left_child and rigth_child and valid
        return True
    
    def isPopulatedZone(self, x, y, zones):
        for zone in zones:
            if (zone["is_populated"] and zone["x_min"] <= x <= zone["x_max"] and zone["y_min"] <= y <= zone["y_max"]):
                return True
        return False

    def calculatePriority(self, magnitude, depth, populated):
        if magnitude >= 6.0:
            return 3
        if magnitude >= 4.5 and depth <= 30.0 and populated:
            return 3
        if magnitude >= 4.5:
            return 2
        return 1
    
    def validateOrder(self, currentRoot, minKey, maxKey):
        if currentRoot is None:
            return True

        valid = True
        key = currentRoot["event"]["key"]
        eventId = key[2]

        if minKey is not None and self.compareKeys(key, minKey) <= 0:
            self.errors.append(f"Event {eventId}: key {key} must be greater than {list(minKey)}")
            valid = False
        if maxKey is not None and self.compareKeys(key, maxKey) >= 0:
            self.errors.append(f"Event {eventId}: key {key} must be less than {list(maxKey)}")
            valid = False

        left = self.validateOrder(currentRoot["left_child"], minKey, key)
        right = self.validateOrder(currentRoot["right_child"], key, maxKey)
        return valid and left and right
    
    def compareKeys(self, a, b):
        a = tuple(a)
        b = tuple(b)
        if a < b:
            return -1
        if a > b:
            return 1
        return 0
    
    def validateBalance(self, root):
        errorsBefore = len(self.errors)
        self.calculateHeight(root)
        return len(self.errors) == errorsBefore

    def calculateHeight(self, currentRoot):
        if currentRoot is None:
            return -1

        leftHeight = self.calculateHeight(currentRoot["left_child"])
        rightHeight = self.calculateHeight(currentRoot["right_child"])

        balance = leftHeight - rightHeight
        if balance not in (-1, 0, 1):
            eventId = currentRoot["event"]["key"][2]
            self.errors.append(f"Event {eventId}: balance factor {balance}, the tree is not AVL")

        return 1 + max(leftHeight, rightHeight)
    
    def getEvents(self, currentRoot, events):
        if currentRoot is None:
            return events
        self.getEvents(currentRoot["left_child"], events)
        events.append(currentRoot["event"])
        self.getEvents(currentRoot["right_child"], events)
        return events

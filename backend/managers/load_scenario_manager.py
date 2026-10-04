import json
from datetime import datetime
from backend.services.seismic_observatory_service import SeismicObservatoryService
from backend.repositories.json_scenario_repository import JsonScenarioRepository
from backend.models.event import Event
from backend.utils.quantities import parseDatetime
from backend.services.parameters.scenario_parameters_service import ScenarioParametersService

class LoadScenarioManager:
    
    def __init__(self, parameters_service=None):
        self.errors = []
        self.eventIds = set()
        self.repository = JsonScenarioRepository()
        self.parameters_service = parameters_service or ScenarioParametersService()
    
    # Method to load the scenario
    def load(self, data, stress_mode):
        self.errors = []
        if not isinstance(data, dict):
            self.errors.append("invalid format of the json")
            return None
        parameters = self._normalize_parameters(data)
        if parameters is None:
            return None
        scenario = self.caseScenary(data, stress_mode)
        if scenario is not None:
            self.parameters_service.update(parameters)
            # Parameters configure the scenario service; they are not events
            # and should not appear in the loaded event payload.
            scenario = {
                key: value for key, value in scenario.items()
                if key not in ("parameters", "parametros")
            }
        return scenario

    def _normalize_parameters(self, data):
        """Validate the optional scenario parameter object and apply defaults."""
        try:
            normalized_parameters = self.parameters_service.parameters_from_scenario(data)
        except (TypeError, ValueError) as error:
            self.errors.append(f"parameters: {error}")
            return None
        return normalized_parameters
    
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
                valid = self.comprobateJsonTopology(data)
                if isinstance(data.get("tree"), dict):
                    valid = self.comprobateTree(data, stress_mode) and valid
                if valid:
                    if "tree" in data:
                        events = self.getEvents(data["tree"]["root"], [])
                        self.addEvents(events)
                        result = self.createArchive(data, events)
                        return result
                return None
            case _:
                self.errors.append("load_type must be 'insertion' or 'topology'")
                return None

    # Method to comprobate if json is usable
    def comprobateJson(self, data):
        required_fields = ["datetime", "zones", "stations", "events"]
        valid = True
        for field in required_fields:
            if field not in data:
                self.errors.append(f"data is missing required field: {field}")
                valid = False

        for field in ("zones", "stations", "events"):
            if field in data and not isinstance(data[field], list):
                self.errors.append(f"{field} must be a list")
                valid = False
        if "datetime" in data:
            try:
                parseDatetime(data["datetime"])
            except (TypeError, ValueError, AttributeError) as error:
                self.errors.append(f"datetime is invalid: {error}")
                valid = False

        zones = data.get("zones", []) if isinstance(data.get("zones", []), list) else []
        stations = data.get("stations", []) if isinstance(data.get("stations", []), list) else []
        events = data.get("events", []) if isinstance(data.get("events", []), list) else []

        zone_ids = set()
        for index, zone in enumerate(zones):
            label = f"zone at index {index}"
            if not isinstance(zone, dict):
                self.errors.append(f"{label} must be an object")
                valid = False
                continue
            required = ("id", "name", "is_populated", "x_min", "x_max", "y_min", "y_max")
            missing = [field for field in required if field not in zone]
            if missing:
                self.errors.append(f"{label} is missing required fields: {', '.join(missing)}")
                valid = False
                continue
            if not isinstance(zone["id"], (str, int, float)) or isinstance(zone["id"], bool):
                self.errors.append(f"{label} id must be a string or number")
                valid = False
            elif zone["id"] in zone_ids:
                self.errors.append(f"{label} has duplicate id {zone['id']}")
                valid = False
            else:
                zone_ids.add(zone["id"])
            if not isinstance(zone["is_populated"], bool):
                self.errors.append(f"{label} is_populated must be boolean")
                valid = False
            bounds = (zone["x_min"], zone["x_max"], zone["y_min"], zone["y_max"])
            if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1000 for value in bounds):
                self.errors.append(f"{label} boundaries must be numeric values from 0 to 1000")
                valid = False
            elif zone["x_min"] >= zone["x_max"] or zone["y_min"] >= zone["y_max"]:
                self.errors.append(f"{label} minimum boundaries must be less than maximum boundaries")
                valid = False

        station_ids = set()
        for index, station in enumerate(stations):
            label = f"station at index {index}"
            if not isinstance(station, dict):
                self.errors.append(f"{label} must be an object")
                valid = False
                continue
            missing = [field for field in ("id", "name", "x", "y") if field not in station]
            if missing:
                self.errors.append(f"{label} is missing required fields: {', '.join(missing)}")
                valid = False
                continue
            station_id = station["id"]
            if not isinstance(station_id, (str, int, float)) or isinstance(station_id, bool):
                self.errors.append(f"{label} id must be a string or number")
                valid = False
            elif station_id in station_ids:
                self.errors.append(f"{label} has duplicate id {station_id}")
                valid = False
            else:
                station_ids.add(station_id)
            for coordinate in ("x", "y"):
                value = station[coordinate]
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1000:
                    self.errors.append(f"{label} {coordinate} must be numeric and between 0 and 1000")
                    valid = False

        # Insertion scenarios sent by the current API use the event fields
        # consumed by SeismicObservatoryService. Legacy tree events are also
        # accepted when the manager is used directly with old scenario files.
        event_fields = ("id", "magnitude", "depth", "epicenter_x", "epicenter_y", "datetime", "station")
        event_ids = set()
        for index, event in enumerate(events):
            if not isinstance(event, dict):
                self.errors.append(f"event at index {index} must be an object")
                valid = False
                continue
            valid = self.validateInsertionEventMetadata(event, index) and valid
            if "key" in event:
                required = ("key", "epicenter_x", "epicenter_y", "depth", "datetime", "revision", "reporting_stations", "attention_status", "event_status", "populated_zone", "expensive_access", "eliminated", "archived")
                missing = [field for field in required if field not in event]
                if missing:
                    self.errors.append(f"event at index {index} is missing required fields: {', '.join(missing)}")
                    valid = False
                key = event["key"]
                if not self.validateDataKey(key):
                    self.errors.append(f"event at index {index} key must contain three numeric values")
                    valid = False
                    continue
                event_id, magnitude = key[2], key[1]
                if event_id in event_ids:
                    self.errors.append(f"event at index {index} has duplicate id {event_id}")
                    valid = False
                event_ids.add(event_id)
                if isinstance(magnitude, bool) or not isinstance(magnitude, (int, float)) or not -2 <= magnitude <= 10:
                    self.errors.append(f"event at index {index} magnitude must be between -2 and 10")
                    valid = False
                for field, low, high, label in (("depth", 0, 700, "depth"), ("epicenter_x", 0, 1000, "epicenter_x"), ("epicenter_y", 0, 1000, "epicenter_y")):
                    if field not in event:
                        continue
                    value = event[field]
                    if isinstance(value, bool) or not isinstance(value, (int, float)) or not low <= value <= high:
                        self.errors.append(f"event at index {index} {label} must be between {low} and {high}")
                        valid = False
                if "datetime" in event:
                    try:
                        parseDatetime(event["datetime"])
                    except (TypeError, ValueError, AttributeError) as error:
                        self.errors.append(f"event at index {index} datetime is invalid: {error}")
                        valid = False
                if "reporting_stations" in event and not isinstance(event["reporting_stations"], list):
                    self.errors.append(f"event at index {index} reporting_stations must be a list")
                    valid = False
                elif "reporting_stations" in event:
                    for station_id in event["reporting_stations"]:
                        if station_id not in station_ids:
                            self.errors.append(f"event at index {index} references unknown station {station_id}")
                            valid = False
                continue
            if any(field not in event for field in event_fields):
                missing = [field for field in event_fields if field not in event]
                self.errors.append(f"event at index {index} is missing required fields: {', '.join(missing)}")
                valid = False
        for index, station in enumerate(stations):
            if not isinstance(station, dict):
                continue
            emitted = station.get("emmited_events", [])
            if not isinstance(emitted, list):
                self.errors.append(f"station at index {index} emmited_events must be a list")
                valid = False
            else:
                for event_key in emitted:
                    event_id = event_key[2] if isinstance(event_key, (list, tuple)) and len(event_key) == 3 else event_key
                    if event_id not in event_ids:
                        self.errors.append(f"station {station.get('id')} references unknown event {event_id}")
                        valid = False

        return valid

    def validateInsertionEventMetadata(self, event, index):
        """Validate event metadata shared by insertion event representations."""
        valid = True
        if "revision" in event:
            revision = event["revision"]
            if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
                self.errors.append(f"event at index {index} revision must be a non-negative integer")
                valid = False

        allowed_statuses = {
            "attention_status": {"pending", "revised"},
            "event_status": {"active", "archived", "deleted"},
        }
        for field, allowed in allowed_statuses.items():
            if field in event and (
                not isinstance(event[field], str) or event[field] not in allowed
            ):
                self.errors.append(
                    f"event at index {index} {field} must be one of: {', '.join(sorted(allowed))}"
                )
                valid = False

        for field in ("populated_zone", "expensive_access", "eliminated", "archived"):
            if field in event and not isinstance(event[field], bool):
                self.errors.append(f"event at index {index} {field} must be boolean")
                valid = False
        return valid
    
    # Method to comprobate if json is usable
    def comprobateJsonTopology(self, data):
        required_fields = ["datetime", "zones", "stations", "tree"]
        valid = True
        for field in required_fields:
            if field not in data:
                self.errors.append(f"data is missing required field: {field}")
                valid = False
        if "datetime" in data:
            try:
                parseDatetime(data["datetime"])
            except (TypeError, ValueError, AttributeError) as error:
                self.errors.append(f"datetime is invalid: {error}")
                valid = False
        for field in ("zones", "stations"):
            if field in data and not isinstance(data[field], list):
                self.errors.append(f"{field} must be a list")
                valid = False
        return valid

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

        structure_valid = self.validateDataTree(data["tree"])
        if not structure_valid:
            return False

        root = data["tree"]["root"]
        valid = self.validateAutenticityIds(root, self.eventIds)
        valid = self.validateOrder(root, None, None) and valid
        
        if not stress_mode:
            valid = self.validateBalance(root) and valid

        stations = data.get("stations")
        if isinstance(stations, list) and all(isinstance(station, dict) for station in stations):
            valid = self.validateReferences(data) and valid
        zones = data.get("zones")
        if isinstance(zones, list) and all(isinstance(zone, dict) for zone in zones):
            valid = self.validatePriority(root, zones) and valid
        return valid
    
    def validateDataTree(self, tree):
        if not isinstance(tree, dict):
            self.errors.append("'tree' must be an object.")
            return False
        valid = True
        if "root" not in tree:
            self.errors.append("'tree' has no root")
            valid = False
        for key in tree:
            if key != "root":
                self.errors.append(f"{key} shouldn't belong to the same root level")
                valid = False
        if "root" in tree:
            valid = self.validateData(tree["root"]) and valid
        return valid
        
    def validateDataRootFields(self, currentRoot):
        if not isinstance(currentRoot, dict):
            self.errors.append("a node must be an object or null")
            return False
        required_fields= ["event", "left_child", "right_child"]
        valid = True
        for field in required_fields:
            if field not in currentRoot:
                self.errors.append(f"node is missing required field: {field}")
                valid = False
            if field == "event":
                if field in currentRoot and not self.validateDataEventFields(currentRoot[field]):
                    valid = False
        return valid
                
    def validateDataEventFields(self, event):
        if not isinstance(event, dict):
            self.errors.append("'event' must be an object")
            return False
        required_fields = ["key", "epicenter_x", "epicenter_y", "depth", "datetime", "revision", "reporting_stations", "attention_status", "event_status", "populated_zone", "expensive_access", "eliminated", "archived"]
        valid = True
        for field in required_fields:
            if field not in event:
                self.errors.append(f"event not has a requeried fields: {field}")
                valid = False
        if "key" in event and not self.validateDataKey(event["key"]):
            self.errors.append("event key must contain three numeric values")
            valid = False
        if "reporting_stations" in event and not isinstance(event["reporting_stations"], list):
            self.errors.append("event reporting_stations must be a list")
            valid = False
        return valid
    
    def validateDataKey(self, key):
        try:
            if len(key) != 3:
                return False
            for i in key:
                if isinstance(i, bool) or not isinstance(i, (int, float)):
                    return False
            return True
        except Exception:
            return False
        
    def validateData(self, currentRoot):
        if currentRoot is None:
            return True
        valid = self.validateDataRootFields(currentRoot)
        if not isinstance(currentRoot, dict):
            return False

        event = currentRoot.get("event")
        if isinstance(event, dict) and self.validateDataKey(event.get("key")):
            fields = ("depth", "epicenter_x", "epicenter_y", "datetime")
            if all(field in event for field in fields):
                try:
                    data_issues = self._validateData(
                        event["key"][2], event["key"][1], event["depth"],
                        event["epicenter_x"], event["epicenter_y"],
                        parseDatetime(event["datetime"]),
                    )
                    self.errors.extend(data_issues)
                    if data_issues:
                        valid = False
                except (ValueError, TypeError, AttributeError) as error:
                    self.errors.append(f"event {event['key'][2]}: {error}")
                    valid = False

        for child in ("left_child", "right_child"):
            if child in currentRoot:
                valid = self.validateData(currentRoot[child]) and valid
        return valid
    
    def _validateData(self, id, magnitude, depth, epicenter_x, epicenter_y, date):
        issues = []
        if isinstance(magnitude, bool) or not isinstance(magnitude, (int, float)) or not (-2 <= magnitude <= 10):
            issues.append("magnitud debe estar entre -2 y 10")
        if isinstance(id, bool) or not isinstance(id, int) or not (1 <= id <= 999999):
            issues.append("Id debe estar entre 1 y 999999")
        if isinstance(depth, bool) or not isinstance(depth, (int, float)) or not (0 <= depth <= 700):
            issues.append("Profundidad debe estar entre 0 y 700")
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in (epicenter_x, epicenter_y)) or not (0 <= epicenter_x <= 1000) or not (0 <= epicenter_y <= 1000):
            issues.append("Epicentro debe estar entre 0 y 1000")
        if not isinstance(date, datetime):
            issues.append("La fecha debe ser de tipo datetime")
        return issues

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
        event_stations_valid = self.validateEventStations(data["tree"]["root"], stationIds)
        station_events_valid = self.validateStationEvents(data["stations"])
        return event_stations_valid and station_events_valid

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
                    # Keep checking this event and the remaining nodes.
            left_valid = self.validateEventStations(currentRoot["left_child"], stationIds)
            right_valid = self.validateEventStations(currentRoot["right_child"], stationIds)
            own_valid = all(stationId in stationIds for stationId in event["reporting_stations"])
            return own_valid and left_valid and right_valid
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

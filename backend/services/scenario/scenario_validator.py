import json
from datetime import datetime
from backend.repositories.json_scenario_repository import JsonScenarioRepository
from backend.models.event import Event
from backend.models.report import Report
from backend.models.station import Station
from backend.utils.quantities import parseDatetime
from backend.services.parameters.scenario_parameters_service import ScenarioParametersService


# Validate scenario data and load its optional sections
class ScenarioValidator:

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    # Create the validator with its repository and parameters service
    def __init__(self, parameters_service=None):
        self.errors = []
        self.eventIds = set()
        self.repository = JsonScenarioRepository()
        self.parameters_service = parameters_service or ScenarioParametersService()

    # -------------------------------------------------------------------------
    # Scenario loading
    # -------------------------------------------------------------------------

    # Load the scenario
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

    # Validate the optional scenario parameter object and apply defaults
    def _normalize_parameters(self, data):
        try:
            normalized_parameters = self.parameters_service.parameters_from_scenario(data)
        except (TypeError, ValueError) as error:
            self.errors.append(f"parameters: {error}")
            return None
        return normalized_parameters

    # Load and validate a scenario from a file path
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

    # Validate JSON content received from an uploaded scenario file
    def loadFromText(self, content, stress_mode=False):
        self.errors = []
        if not isinstance(content, str) or not content.strip():
            self.errors.append("the json file is empty")
            return None
        try:
            data = self.repository.parse_text(content)
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

    # -------------------------------------------------------------------------
    # Scenario type dispatch
    # -------------------------------------------------------------------------

    # Check which type of scenario was received and validate it
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
                        result = self.createArchive(data, events)
                        return result
                return None
            case _:
                self.errors.append("load_type must be 'insertion' or 'topology'")
                return None

    # -------------------------------------------------------------------------
    # Insertion scenario validation
    # -------------------------------------------------------------------------

    # Check that an insertion scenario is usable
    def comprobateJson(self, data):
        # Check the required top-level fields
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

        # Validate the zones
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

        # Validate the stations
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

        # Validate the events
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

        # Check that the events emitted by each station exist
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

    # Validate event metadata shared by insertion event representations
    def validateInsertionEventMetadata(self, event, index):
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

    # -------------------------------------------------------------------------
    # Topology scenario validation
    # -------------------------------------------------------------------------

    # Check that a topology scenario is usable
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

    # Check that the tree is usable
    def comprobateTree(self, data, stress_mode):
        self.eventIds = []

        structure_valid = self.validateDataTree(data["tree"])
        if not structure_valid:
            return False

        root = data["tree"]["root"]
        _, metadata_valid = self.validateTreeMetadata(root)
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
        return valid and metadata_valid

    # Check saved node heights and balance factors against the links
    def validateTreeMetadata(self, node):
        if node is None:
            return -1, True

        left_height, left_valid = self.validateTreeMetadata(node["left_child"])
        right_height, right_valid = self.validateTreeMetadata(node["right_child"])
        expected_height = max(left_height, right_height) + 1
        expected_balance = left_height - right_height
        event_id = node["event"]["key"][2]
        valid = left_valid and right_valid

        if "height" not in node:
            self.errors.append(f"Event {event_id}: node is missing stored height")
            valid = False
        elif isinstance(node["height"], bool) or not isinstance(node["height"], int) or node["height"] != expected_height:
            self.errors.append(
                f"Event {event_id}: stored height {node['height']} does not match calculated height {expected_height}"
            )
            valid = False

        if "balance_factor" not in node:
            self.errors.append(f"Event {event_id}: node is missing stored balance_factor")
            valid = False
        elif isinstance(node["balance_factor"], bool) or not isinstance(node["balance_factor"], int) or node["balance_factor"] != expected_balance:
            self.errors.append(
                f"Event {event_id}: stored balance_factor {node['balance_factor']} does not match calculated balance_factor {expected_balance}"
            )
            valid = False

        return expected_height, valid

    # -------------------------------------------------------------------------
    # Tree structure validation
    # -------------------------------------------------------------------------

    # Validate the tree object and every node it contains
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

    # Validate the required fields of a node
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

    # Validate the required fields of an event
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

    # Check that a key has exactly three numeric values
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

    # Validate a node and its descendants recursively
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

    # Return the list of issues found in the basic values of an event
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

    # -------------------------------------------------------------------------
    # Tree integrity checks
    # -------------------------------------------------------------------------

    # Check that no event id appears twice in the tree
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

    # Check that the tree keeps the binary search order
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

    # Compare two keys and return -1, 0 or 1
    def compareKeys(self, a, b):
        a = tuple(a)
        b = tuple(b)
        if a < b:
            return -1
        if a > b:
            return 1
        return 0

    # Check that the tree is balanced like an AVL tree
    def validateBalance(self, root):
        errorsBefore = len(self.errors)
        self.calculateHeight(root)
        return len(self.errors) == errorsBefore

    # Calculate node heights and report any invalid balance factor
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

    # -------------------------------------------------------------------------
    # Station and event references
    # -------------------------------------------------------------------------

    # Check the references between events and stations in both directions
    def validateReferences(self, data):
        stationIds = self.getStationIds(data["stations"])
        event_stations_valid = self.validateEventStations(data["tree"]["root"], stationIds)
        station_events_valid = self.validateStationEvents(data["stations"])
        return event_stations_valid and station_events_valid

    # Return the set of station ids
    def getStationIds(self, stations):
        stationIds = set()
        for station in stations:
            stationIds.add(station["id"])
        return stationIds

    # Check that every station reported by an event exists
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

    # Check that every event emitted by a station exists
    def validateStationEvents(self, stations):
        valid = True
        for station in stations:
            for eventId in station["emmited_events"]:
                if eventId not in self.eventIds:
                    self.errors.append(f"Station {station['id']} references unknown event {eventId}")
                    valid = False
        return valid

    # -------------------------------------------------------------------------
    # Priority validation
    # -------------------------------------------------------------------------

    # Check the stored priority and populated zone of every event
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

    # Return whether a point falls inside any populated zone
    def isPopulatedZone(self, x, y, zones):
        for zone in zones:
            if (zone["is_populated"] and zone["x_min"] <= x <= zone["x_max"] and zone["y_min"] <= y <= zone["y_max"]):
                return True
        return False

    # Calculate the priority of an event from its magnitude, depth and zone
    def calculatePriority(self, magnitude, depth, populated):
        if magnitude >= 6.0:
            return 3
        if magnitude >= 4.5 and depth <= 30.0 and populated:
            return 3
        if magnitude >= 4.5:
            return 2
        return 1

    # -------------------------------------------------------------------------
    # Archive creation
    # -------------------------------------------------------------------------

    # Create the archive to return to the frontend (pending completion)
    def createArchive(self, data, events):
        result = {}
        result["datetime"] = data["datetime"]
        result["zones"] = data["zones"]
        result["stations"] = data["stations"]
        result["events"] = events
        for section in ("history", "report_queue", "association_manager", "metrics"):
            if section in data:
                result[section] = data[section]
        return result

    # Collect the events of the tree in order
    def getEvents(self, currentRoot, events):
        if currentRoot is None:
            return events
        self.getEvents(currentRoot["left_child"], events)
        events.append(currentRoot["event"])
        self.getEvents(currentRoot["right_child"], events)
        return events

    # -------------------------------------------------------------------------
    # Optional sections
    # -------------------------------------------------------------------------

    # Restore optional state included in a topology scenario export
    def loadOptionalSections(self, observatory, data):
        if not isinstance(data, dict):
            return observatory
        self.loadOptionalHistory(observatory, data.get("history"))
        observatory.recalculateAssociations()
        self.loadOptionalReportQueue(observatory, data.get("report_queue"))
        self.loadOptionalAssociations(observatory, data.get("association_manager"))
        self.loadOptionalMetrics(observatory, data.get("metrics"))
        return observatory

    # -------------------------------------------------------------------------
    # Optional history
    # -------------------------------------------------------------------------

    # Restore the archived and deleted events of the history
    def loadOptionalHistory(self, observatory, section):
        if section is None:
            return
        if not isinstance(section, dict):
            raise ValueError("history must be an object")
        history = observatory.getHistory()
        active_ids = set(observatory.getAVLTree().index)
        archived_ids = set()
        deleted_event_ids = set()
        for field, status in (("archived", "archived"), ("eliminated", "deleted")):
            if field == "eliminated" and field not in section:
                field = "deleted"
            values = section.get(field, [])
            if isinstance(values, dict):
                values = list(values.values())
            if not isinstance(values, list):
                raise ValueError(f"history.{field} must be a list")
            for item in values:
                if isinstance(item, (int, str)):
                    if status == "deleted":
                        history.addDeletedId(int(item))
                        continue
                    raise ValueError("archived history entries must contain event data")
                if not isinstance(item, dict):
                    raise ValueError(f"history.{field} entries must be objects")
                event = self._event_from_optional_history(item, observatory, status)
                event_id = event.getKey()[2]
                if status == "archived":
                    if event_id in active_ids or event_id in archived_ids or event_id in deleted_event_ids:
                        raise ValueError(f"history contains duplicate event id {event_id}")
                    archived_ids.add(event_id)
                    history.addArchived(event_id, event)
                else:
                    if event_id in active_ids or event_id in archived_ids or event_id in deleted_event_ids:
                        raise ValueError(f"history contains duplicate event id {event_id}")
                    deleted_event_ids.add(event_id)
                    history.addDeleted(event_id, event)

        deleted_ids = section.get("deletedIds", [])
        if not isinstance(deleted_ids, list):
            raise ValueError("history.deletedIds must be a list")
        for value in deleted_ids:
            if isinstance(value, bool) or not isinstance(value, (int, str)):
                raise ValueError("history.deletedIds entries must be positive integer ids")
            if isinstance(value, str) and not value.isdigit():
                raise ValueError("history.deletedIds entries must be positive integer ids")
            event_id = int(value)
            if not 1 <= event_id <= 999999:
                raise ValueError("history.deletedIds entries must be between 1 and 999999")
            if event_id in active_ids or event_id in archived_ids:
                raise ValueError(f"history contains duplicate event id {event_id}")
            history.addDeletedId(event_id)

        archived_trees = section.get("archivedTrees", [])
        if not isinstance(archived_trees, list):
            raise ValueError("history.archivedTrees must be a list")
        history.archivedTrees = archived_trees

    # Build and validate an event from a history entry
    def _event_from_optional_history(self, item, observatory, status):
        if "key" in item:
            normalized = dict(item)
            normalized.setdefault("attention_status", "pending")
            normalized.setdefault("event_status", status)
            normalized.setdefault("populated_zone", False)
            normalized.setdefault("expensive_access", False)
            normalized.setdefault("reporting_stations", [])
            event = Event.fromDict(normalized)
            return self._validateHistoricalEvent(event, observatory, status)

        event_id = int(item.get("id", item.get("event_id")))
        magnitude = float(item["magnitude"])
        populated = any(
            zone.getIsPopulated()
            and zone.contains(item["epicenter_x"], item["epicenter_y"])
            for zone in observatory.getZones()
        )
        event_data = {
            "key": [
                self.calculatePriority(magnitude, item["depth"], populated),
                magnitude,
                event_id,
            ],
            "depth": item["depth"],
            "epicenter_x": item["epicenter_x"],
            "epicenter_y": item["epicenter_y"],
            "datetime": item["datetime"],
            "revision": item.get("revision", 1),
            "reporting_stations": item.get("reporting_stations", []),
            "attention_status": item.get("attention_status", "pending"),
            "event_status": status,
            "populated_zone": item.get("populated_zone", populated),
            "expensive_access": item.get("expensive_access", False),
        }
        event = Event.fromDict(event_data)
        return self._validateHistoricalEvent(event, observatory, status)

    # Validate retained event data before adding it to scenario history
    def _validateHistoricalEvent(self, event, observatory, expected_status):
        priority, magnitude, event_id = event.getKey()
        issues = self._validateData(
            event_id,
            magnitude,
            event.getDepth(),
            event.getEpicenterX(),
            event.getEpicenterY(),
            event.getDateTime(),
        )
        if issues:
            raise ValueError(f"historical event {event_id}: {'; '.join(issues)}")
        if isinstance(event.getCurrentRevision(), bool) or not isinstance(event.getCurrentRevision(), int) or event.getCurrentRevision() <= 0:
            raise ValueError(f"historical event {event_id} has an invalid revision")
        if event.getEventStatus() != expected_status:
            raise ValueError(f"historical event {event_id} has an invalid status")
        if not observatory.getClock().canOccurAt(event.getDateTime()):
            raise ValueError(f"historical event {event_id} occurs after the scenario clock")

        populated = self.isPopulatedZone(
            event.getEpicenterX(), event.getEpicenterY(), observatory.getZones()
        )
        if event.getPopulatedZone() != populated:
            raise ValueError(f"historical event {event_id} has an inconsistent populated_zone")
        if priority != self.calculatePriority(magnitude, event.getDepth(), populated):
            raise ValueError(f"historical event {event_id} has an inconsistent priority")

        station_ids = {station.getId() for station in observatory.getStations()}
        unknown_stations = event.getReportingStations() - station_ids
        if unknown_stations:
            raise ValueError(
                f"historical event {event_id} references unknown stations: "
                f"{', '.join(map(str, sorted(unknown_stations, key=str)))}"
            )
        return event

    # -------------------------------------------------------------------------
    # Optional report queue
    # -------------------------------------------------------------------------

    # Restore the pending reports of the report queue
    def loadOptionalReportQueue(self, observatory, section):
        if section is None:
            return
        if not isinstance(section, dict) or not isinstance(section.get("items", []), list):
            raise ValueError("report_queue.items must be a list")
        stations = {station.getId(): station for station in observatory.getStations()}
        queue = observatory.getReportQueue()
        for item in section.get("items", []):
            if not isinstance(item, dict):
                raise ValueError("report_queue entries must be objects")
            station_data = item.get("station")
            station_id = item.get("station_id")
            if isinstance(station_data, dict):
                station_id = station_data.get("id")
                station = stations.get(station_id)
                if station is None and all(key in station_data for key in ("name", "x", "y")):
                    station = Station.fromDict(station_data)
            else:
                station = stations.get(station_id)
            if station is None:
                raise ValueError(f"report references unknown station {station_id}")
            queue.enqueue(Report(
                event_id=item.get("event_id", item.get("id")),
                revision=item.get("revision", 1),
                station=station,
                magnitude=item["magnitude"],
                depth=item["depth"],
                epicenter_x=item["epicenter_x"],
                epicenter_y=item["epicenter_y"],
                datetime_=parseDatetime(item["datetime"]),
            ))

    # -------------------------------------------------------------------------
    # Optional associations
    # -------------------------------------------------------------------------

    # Check that the stored associations match the ones calculated for the scenario
    def loadOptionalAssociations(self, observatory, section):
        if section is None:
            return
        if not isinstance(section, dict):
            raise ValueError("association_manager must be an object")
        manager = observatory.getAssociationManager()
        candidates = section.get("candidates")
        if candidates is not None:
            if not isinstance(candidates, dict):
                raise ValueError("association_manager.candidates must be an object")
            if any(not isinstance(ids, list) for ids in candidates.values()):
                raise ValueError("association_manager candidate values must be lists")
            restored_candidates = {
                int(event_id): [int(candidate) for candidate in ids]
                for event_id, ids in candidates.items()
            }
            if restored_candidates != manager.getCandidates():
                raise ValueError("association_manager candidates do not match the scenario")

        selected_references = section.get("selected_references")
        if selected_references is not None:
            if not isinstance(selected_references, dict):
                raise ValueError("association_manager.selected_references must be an object")
            restored_references = {
                int(event_id): int(reference_id)
                for event_id, reference_id in selected_references.items()
            }
            if restored_references != manager.getSelectedReferences():
                raise ValueError("association_manager selected references do not match the scenario")

    # -------------------------------------------------------------------------
    # Optional metrics
    # -------------------------------------------------------------------------

    # Restore the stored metrics over the current ones
    def loadOptionalMetrics(self, observatory, section):
        if section is None:
            return
        if not isinstance(section, dict):
            raise ValueError("metrics must be an object")
        from backend.models.metrics import Metrics
        values = observatory.getMetrics().toDict()
        values.update(section)
        observatory.setMetrics(Metrics.fromDict(values))
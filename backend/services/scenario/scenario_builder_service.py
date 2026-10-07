from uuid import uuid4

from backend.models.seismic_observatory import SeismicObservatory
from backend.models.station import Station
from backend.models.zone import Zone
from backend.services.audit.structure_audit_service import StructureAuditService
from backend.services.scenario.scenario_data_normalizer import ScenarioDataNormalizer
from backend.services.scenario.scenario_errors import ScenarioValidationError
from backend.utils.quantities import hasAtMostOneDecimal, parseDatetime


EXECUTION_MODES = ("normal", "stress")


# Build a validated observatory from insertion or topology data
class ScenarioBuilderService:

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    # Create the service with its parameters service, metrics service and normalizer
    def __init__(self, parameters_service, metrics_service):
        self.parameters_service = parameters_service
        self.metrics_service = metrics_service
        self.normalizer = ScenarioDataNormalizer()

    # -------------------------------------------------------------------------
    # Scenario building
    # -------------------------------------------------------------------------

    # Build the correct scenario representation and apply its parameters
    def build(self, data):
        # Validate the execution mode
        mode = data.get("execution_mode", "normal")
        if mode not in EXECUTION_MODES:
            raise ScenarioValidationError(["execution_mode debe ser 'normal' o 'stress'"])

        # Read and validate the scenario parameters
        try:
            parameters = self.parameters_service.parameters_from_scenario(data)
        except (TypeError, ValueError) as error:
            raise ScenarioValidationError([f"Parámetros inválidos: {error}"])

        # Choose the builder that matches the scenario format
        if "tree" in data:
            observatory = self._build_from_topology({**data, "avl_tree": data["tree"]}, mode)
        else:
            observatory = self._build_from_insertions(data, mode)

        # Apply identifiers, parameters and derived metrics
        versions = data.get("versions", [])
        observatory.scenario_versions = versions if isinstance(versions, list) else []
        observatory.scenario_id = str(uuid4())
        self.parameters_service.update(parameters)
        observatory.setL(parameters["L"])
        observatory.setT(parameters["T"])
        observatory.setAssociationLimits(parameters["W"], parameters["R"])
        self.metrics_service.refresh_derived_metrics(observatory)
        return observatory

    # -------------------------------------------------------------------------
    # Insertion-based building
    # -------------------------------------------------------------------------

    # Build the observatory by inserting stations, zones and events one by one
    def _build_from_insertions(self, data, mode):
        issues = []
        observatory = SeismicObservatory()

        # Set the scenario clock
        clock_text = data.get("datetime") or (data.get("clock") or {}).get("current_time")
        if clock_text is not None:
            try:
                observatory.getClock().setCurrentTime(parseDatetime(clock_text))
            except (ValueError, TypeError, AttributeError):
                issues.append("El reloj (datetime) no es una fecha ISO 8601 válida")

        # Load the stations
        stations = data.get("stations")
        station_ids = set()
        if not isinstance(stations, list) or len(stations) == 0:
            issues.append("El escenario debe tener al menos una estación")
        else:
            for index, item in enumerate(stations):
                required = ("id", "name", "x", "y")
                if not isinstance(item, dict) or any(field not in item for field in required):
                    issues.append(f"Estación #{index + 1}: debe tener 'id', 'name', 'x' y 'y'")
                    continue
                if item["id"] in station_ids:
                    issues.append(f"Estación #{index + 1}: id {item['id']} repetido")
                    continue
                try:
                    station = Station(item["id"], item["name"], item["x"], item["y"])
                except (TypeError, ValueError) as error:
                    issues.append(f"Estación #{index + 1}: {error}")
                    continue
                station_ids.add(item["id"])
                observatory.addStation(station)

        # Load the zones
        zones = data.get("zones", [])
        if not isinstance(zones, list):
            issues.append("'zones' debe ser una lista")
            zones = []
        for index, item in enumerate(zones):
            try:
                observatory.addZone(Zone(
                    item["id"], item["name"], item["x_min"], item["x_max"],
                    item["y_min"], item["y_max"], item["is_populated"],
                ))
            except (KeyError, TypeError, ValueError) as error:
                issues.append(f"Zona #{index + 1}: {error}")

        # Load the events
        events = data.get("events", [])
        if not isinstance(events, list):
            issues.append("'events' debe ser una lista")
            events = []

        seen_ids = set()
        required = ("id", "magnitude", "depth", "epicenter_x", "epicenter_y", "datetime", "station")
        for index, raw_item in enumerate(events):
            label = f"Evento #{index + 1}"

            # Normalize the raw event and check its shape
            try:
                item = self.normalizer.insertion_event(raw_item, station_ids)
            except (KeyError, TypeError, ValueError) as error:
                issues.append(f"{label}: {error}")
                continue
            if not isinstance(item, dict):
                issues.append(f"{label}: debe ser un objeto")
                continue
            missing = [field for field in required if field not in item]
            if missing:
                issues.append(f"{label}: faltan campos {', '.join(missing)}")
                continue

            # Check for repeated ids
            label = f"Evento #{index + 1} (id {item['id']})"
            if item["id"] in seen_ids:
                issues.append(f"{label}: id repetido en el archivo")
                continue
            seen_ids.add(item["id"])

            # Check numeric fields and the station
            numeric_ok = True
            for field in ("magnitude", "depth", "epicenter_x", "epicenter_y"):
                value = item[field]
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    issues.append(f"{label}: '{field}' debe ser numérico")
                    numeric_ok = False
                elif not hasAtMostOneDecimal(value):
                    issues.append(f"{label}: '{field}' admite máximo un decimal")
                    numeric_ok = False
            if not numeric_ok:
                continue
            if station_ids and item["station"] not in station_ids:
                issues.append(f"{label}: la estación {item['station']} no existe")
                continue

            # Check the event date against the scenario clock
            try:
                event_time = parseDatetime(item["datetime"])
            except (ValueError, TypeError, AttributeError):
                issues.append(f"{label}: 'datetime' no es una fecha ISO 8601 válida")
                continue
            if not observatory.getClock().canOccurAt(event_time):
                issues.append(f"{label}: la fecha supera el reloj del escenario")
                continue

            # Create the event and register its rotation steps
            try:
                observatory.begin_visual_operation()
                result = observatory.createEvent(
                    id=item["id"], magnitude=item["magnitude"], depth=item["depth"],
                    epicenter_x=item["epicenter_x"], epicenter_y=item["epicenter_y"],
                    datetime=event_time, revision=item.get("revision", 1),
                    station=item["station"],
                )
                steps = observatory.finish_visual_operation()
                if result is False or not all(result):
                    issues.append(f"{label}: ya existe un evento con esa clave")
                    continue
                self.metrics_service.register_rotation_steps(observatory.getMetrics(), steps)
            except (ValueError, TypeError) as error:
                issues.append(f"{label}: {error}")

        if issues:
            raise ScenarioValidationError(issues)

        observatory.setExecutionMode(mode)
        observatory.getAVLTree().balance = mode == "normal"
        return observatory

    # -------------------------------------------------------------------------
    # Topology-based building
    # -------------------------------------------------------------------------

    # Build the observatory from a serialized tree topology and audit it
    def _build_from_topology(self, data, mode):
        issues = []

        # Normalize the tree when it comes in the nested event format
        if "tree" in data and "avl_tree" in data:
            root = data["avl_tree"].get("root") if isinstance(data["avl_tree"], dict) else None
            if isinstance(root, dict) and "event" in root:
                try:
                    data = {**data, "avl_tree": self.normalizer.topology_tree(data["tree"])}
                except (AttributeError, KeyError, TypeError, ValueError) as error:
                    raise ScenarioValidationError([f"Topología inválida: {error}"])

        # Merge the supplied data over the default observatory structure
        base = SeismicObservatory().toDict()
        optional_sections = {"history", "report_queue", "association_manager", "metrics"}
        merged = {
            **base,
            **{key: value for key, value in data.items() if key in base and key not in optional_sections},
        }
        merged["scenario_id"] = None
        if "datetime" in data and "clock" not in data:
            merged["clock"] = {"current_time": data["datetime"]}

        # Rebuild the observatory from the merged dictionary
        try:
            observatory = SeismicObservatory.fromDict(merged)
        except (KeyError, TypeError, ValueError, AttributeError) as error:
            raise ScenarioValidationError([f"Topología inválida: {type(error).__name__}: {error}"])

        # Check stations and event dates
        if len(observatory.getStations()) == 0:
            issues.append("El escenario debe tener al menos una estación")
        for event in observatory.getAVLTree().preorder() or []:
            if not observatory.getClock().canOccurAt(event.getDateTime()):
                issues.append(f"El evento {event.getKey()[2]}: la fecha supera el reloj del escenario")

        # Fill the BST when the scenario did not provide one
        if "bst_tree" not in data:
            for event in observatory.getAVLTree().preorder() or []:
                observatory.getBSTTree().insert(event)

        # Audit the AVL tree and check its balance
        audit = StructureAuditService().audit_avl(observatory.getAVLTree(), mode)
        for issue in audit["issues"]:
            detail = ", ".join(f"{key}={value}" for key, value in issue.items() if key != "type")
            issues.append(f"AVL: {issue['type']} ({detail})")
        if not audit["balanced"] and mode != "stress":
            issues.append(
                f"La topología está desbalanceada (desbalance máx. {audit['max_imbalance']}): "
                "solo puede cargarse con execution_mode 'stress'"
            )
        if issues:
            raise ScenarioValidationError(issues)

        observatory.setExecutionMode(mode)
        observatory.getAVLTree().balance = mode == "normal"
        return observatory

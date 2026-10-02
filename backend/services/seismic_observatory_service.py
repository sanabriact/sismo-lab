import json
from datetime import datetime
from uuid import uuid4
from backend.repositories.seismic_observatory_repository import SeismicObservatoryRepository
from backend.services.metrics.metrics_service import MetricsService
from backend.models.seismic_observatory import SeismicObservatory
from backend.models.station import Station
from backend.models.zone import Zone
from backend.utils.quantities import parseDatetime, hasAtMostOneDecimal

EXECUTION_MODES = ("normal", "stress")

class ScenarioValidationError(Exception):
    """El escenario no es válido. `issues` lista todos los problemas encontrados."""
    def __init__(self, issues):
        super().__init__("; ".join(issues))
        self.issues = issues

class SeismicObservatoryService:
    def __init__(self):
        self.repository = SeismicObservatoryRepository()
        self.metrics_service = MetricsService()

    def getObservatory(self):
        observatory = self.repository.load()
        if observatory is None:
            observatory = SeismicObservatory()
        return observatory
 

    def createEvent(self, id, magnitude, depth, epicenter_x, epicenter_y, datetime: datetime, revision, station):
        # load the observatory
        obs = self.getObservatory()
        try:
            # try of create the event
            event = obs.createEvent(
                id, magnitude, depth, epicenter_x, epicenter_y, datetime, revision, station)
        except ValueError as error:
            # if we have an error return an object with false and the reason
            return {
                "success": False,
                "reason": str(error)
            }

        if not event:
            # if createEvent() return False the id already exists
            return {
                "success": False,
                "reason": "The id belongs to another event created, archived or deleted"
            }
        # Saving the observatory
        self.repository.save(obs)
        event_ = obs.searchEventById(id)
        return {
            "success": True,
            "event": event_.toDict()
        }

    def searchEventById(self, id):
        obs = self.getObservatory()
        event = obs.searchEventById(id)
        if event is None:
            return {
                "success": False,
                "reason": "The event doesn't exist"
            }

        return {
            "success": True,
            "event": event.toDict()
        }

    def deleteEventById(self, id):
        obs = self.getObservatory()
        event = obs.searchEventById(id)
        if event is None:
            return {
                "success": False,
                "reason": "The event doesn't exist"
            }
        deleted = obs.deleteEventById(id)
        if not deleted:
            return {
                "success": False,
                "reason": "An error has occurred."
            }

        self.repository.save(obs)
        return {
                "success": True,
                "event": event.toDict()
            }

    def markAsRevised(self, id):
        obs = self.getObservatory()
        event = obs.searchEventById(id)
        if event is None:
            return {
                "success": False,
                "reason": "The event doesn't exist"
            }
        event.setAttentionStatus("revised")
        self.repository.save(obs)
        return {
            "success": True,
            "event": event.toDict()
        }
    
    # ===================== Carga de escenarios =====================
    # La carga es completa o no se aplica: primero se construye y valida un
    # observatorio nuevo; solo si no hay problemas se guarda en disco.

    def loadScenarioFromText(self, content):
        observatory = self.buildScenario(self.parseScenarioText(content))
        self.repository.save(observatory)
        return observatory

    def loadScenarioFromAI(self, ai_mode):
        # Aún no hay generación de escenarios con la IA: "empty" usa una
        # configuración base (estaciones y zonas fijas, sin eventos).
        if ai_mode != "empty":
            raise ScenarioValidationError([
                "La generación de escenarios con IA en el modo '" + str(ai_mode) + "' aún no está implementada"
            ])
        observatory = self.buildScenario({
            "execution_mode": "normal",
            "stations": [
                {"id": 1, "name": "Estación Norte", "x": 250, "y": 750},
                {"id": 2, "name": "Estación Centro", "x": 500, "y": 500},
                {"id": 3, "name": "Estación Sur", "x": 750, "y": 250},
            ],
            "zones": [
                {"id": 1, "name": "Zona Suroccidental", "x_min": 0, "x_max": 500, "y_min": 0, "y_max": 500, "is_populated": True},
                {"id": 2, "name": "Zona Nororiental", "x_min": 500, "x_max": 1000, "y_min": 500, "y_max": 1000, "is_populated": False},
            ],
            "events": [],
        })
        self.repository.save(observatory)
        return observatory

    def parseScenarioText(self, content):
        if not isinstance(content, str) or not content.strip():
            raise ScenarioValidationError(["El archivo está vacío"])
        try:
            data = json.loads(content)
        except json.JSONDecodeError as error:
            raise ScenarioValidationError([
                f"JSON inválido (línea {error.lineno}, columna {error.colno}): {error.msg}"
            ])
        if isinstance(data, dict) and "seismic_observatory" in data:
            data = data["seismic_observatory"]
        if not isinstance(data, dict):
            raise ScenarioValidationError(["El escenario debe ser un objeto JSON"])
        return data

    def buildScenario(self, data):
        """
        Construye y valida un SeismicObservatory a partir de un dict.

        - Con "avl_tree" se carga por topología (se recupera el árbol tal cual).
        - Sin "avl_tree" se carga por inserciones: los eventos de "events" se
          insertan uno a uno, con balanceo, en el AVL y en el BST.
        """
        mode = data.get("execution_mode", "normal")
        if mode not in EXECUTION_MODES:
            raise ScenarioValidationError(["execution_mode debe ser 'normal' o 'stress'"])

        if "tree" in data:
            topology_data = {
                **data,
                "avl_tree": data["tree"]
            }
            observatory = self._buildFromTopology(topology_data, mode)
        else:
            observatory = self._buildFromInsertions(data, mode)

        # Siempre un id nuevo: evita que eventos en cola de un escenario
        # anterior con el mismo id se apliquen a este.
        observatory.scenario_id = str(uuid4())
        self.metrics_service.refresh_derived_metrics(observatory)
        return observatory

    def _buildFromInsertions(self, data, mode):
        issues = []
        observatory = SeismicObservatory()

        # ---- reloj ----
        clock_text = data.get("datetime") or (data.get("clock") or {}).get("current_time")
        if clock_text is not None:
            try:
                observatory.getClock().setCurrentTime(parseDatetime(clock_text))
            except (ValueError, TypeError, AttributeError):
                issues.append("El reloj (datetime) no es una fecha ISO 8601 válida")

        # ---- estaciones ----
        stations = data.get("stations")
        station_ids = set()
        if not isinstance(stations, list) or len(stations) == 0:
            issues.append("El escenario debe tener al menos una estación")
        else:
            for i, item in enumerate(stations):
                required_station_fields = ("id", "name", "x", "y")
                if not isinstance(item, dict) or any(field not in item for field in required_station_fields):
                    issues.append(f"Estación #{i + 1}: debe tener 'id', 'name', 'x' y 'y'")
                    continue
                if item["id"] in station_ids:
                    issues.append(f"Estación #{i + 1}: id {item['id']} repetido")
                    continue
                try:
                    station = Station(
                        item["id"],
                        item["name"],
                        item["x"],
                        item["y"],
                    )
                except (TypeError, ValueError) as error:
                    issues.append(f"Estación #{i + 1}: {error}")
                    continue

                station_ids.add(item["id"])
                observatory.addStation(station)

        # ---- zonas ----
        zones = data.get("zones", [])
        if not isinstance(zones, list):
            issues.append("'zones' debe ser una lista")
            zones = []
        for i, item in enumerate(zones):
            try:
                observatory.addZone(Zone(
                    item["id"], item["name"], item["x_min"], item["x_max"],
                    item["y_min"], item["y_max"], item["is_populated"],
                ))
            except (KeyError, TypeError, ValueError) as error:
                issues.append(f"Zona #{i + 1}: {error}")

        # ---- eventos ----
        events = data.get("events", [])
        if not isinstance(events, list):
            issues.append("'events' debe ser una lista")
            events = []

        seen_ids = set()
        required = ("id", "magnitude", "depth", "epicenter_x", "epicenter_y", "datetime", "station")
        for i, raw_item in enumerate(events):
            label = f"Evento #{i + 1}"
            try:
                item = self._normalizeInsertionEvent(raw_item, station_ids)
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

            label = f"Evento #{i + 1} (id {item['id']})"
            if item["id"] in seen_ids:
                issues.append(f"{label}: id repetido en el archivo")
                continue
            seen_ids.add(item["id"])

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

            # Sin estaciones válidas ya hay un error propio; no se repite por evento.
            if station_ids and item["station"] not in station_ids:
                issues.append(f"{label}: la estación {item['station']} no existe")
                continue

            try:
                event_time = parseDatetime(item["datetime"])
            except (ValueError, TypeError, AttributeError):
                issues.append(f"{label}: 'datetime' no es una fecha ISO 8601 válida")
                continue
            if not observatory.getClock().canOccurAt(event_time):
                issues.append(f"{label}: la fecha supera el reloj del escenario")
                continue

            try:
                observatory.begin_visual_operation()
                result = observatory.createEvent(
                    id=item["id"],
                    magnitude=item["magnitude"],
                    depth=item["depth"],
                    epicenter_x=item["epicenter_x"],
                    epicenter_y=item["epicenter_y"],
                    datetime=event_time,
                    revision=item.get("revision", 1),
                    station=item["station"],
                )

                steps = observatory.finish_visual_operation()

                if result is False or not all(result):
                    issues.append(f"{label}: ya existe un evento con esa clave")
                    continue

                self.metrics_service.register_rotation_steps(
                    observatory.getMetrics(),
                    steps,
                )
            except (ValueError, TypeError) as error:
                issues.append(f"{label}: {error}")
                continue
            if result is False or not all(result):
                issues.append(f"{label}: ya existe un evento con esa clave")

        if issues:
            raise ScenarioValidationError(issues)

        observatory.setExecutionMode(mode)
        # Keep the AVL policy synchronized with the scenario mode.
        observatory.getAVLTree().balance = mode == "normal"
        return observatory

    def _buildFromTopology(self, data, mode):
        issues = []

        # LoadScenarioManager validates the compact topology format used by
        # scenario files. The observatory model stores equivalent nodes with
        # the serialized Node field names, so normalize them before loading.
        if "tree" in data and "avl_tree" in data:
            root = data["avl_tree"].get("root") if isinstance(data["avl_tree"], dict) else None
            if isinstance(root, dict) and "event" in root:
                try:
                    data = {**data, "avl_tree": self._normalizeScenarioTree(data["tree"])}
                except (AttributeError, KeyError, TypeError, ValueError) as error:
                    raise ScenarioValidationError([f"Topología inválida: {error}"])

        # Se completa lo que falte con los valores por defecto de un
        # observatorio vacío, para aceptar exportaciones parciales.
        base = SeismicObservatory().toDict()
        merged = {**base, **{key: value for key, value in data.items() if key in base}}
        merged["scenario_id"] = None
        if "datetime" in data and "clock" not in data:
            merged["clock"] = {"current_time": data["datetime"]}

        try:
            observatory = SeismicObservatory.fromDict(merged)
        except (KeyError, TypeError, ValueError, AttributeError) as error:
            raise ScenarioValidationError([f"Topología inválida: {type(error).__name__}: {error}"])

        if len(observatory.getStations()) == 0:
            issues.append("El escenario debe tener al menos una estación")

        # A topology must not contain an event that occurs after its restored clock.
        for event in observatory.getAVLTree().preorder() or []:
            if not observatory.getClock().canOccurAt(event.getDateTime()):
                issues.append(
                    f"El evento {event.getKey()[2]}: la fecha supera el reloj del escenario"
                )

        # Si el archivo no trae BST, se reconstruye insertando los eventos.
        if "bst_tree" not in data:
            for event in observatory.getAVLTree().preorder() or []:
                observatory.getBSTTree().insert(event)

        audit = observatory.getAVLTree().audit()
        for issue in audit["issues"]:
            detail = ", ".join(f"{k}={v}" for k, v in issue.items() if k != "type")
            issues.append(f"AVL: {issue['type']} ({detail})")

        if not audit["balanced"] and mode != "stress":
            issues.append(
                f"La topología está desbalanceada (desbalance máx. {audit['max_imbalance']}): "
                "solo puede cargarse con execution_mode 'stress'"
            )

        if issues:
            raise ScenarioValidationError(issues)

        observatory.setExecutionMode(mode)
        # A topology loaded in stress mode must keep accepting unbalanced inserts.
        observatory.getAVLTree().balance = mode == "normal"
        return observatory

    def _normalizeInsertionEvent(self, item, station_ids):
        """Accept both the legacy key-based event format and the API format."""
        if not isinstance(item, dict) or "key" not in item:
            return item

        key = item["key"]
        if not isinstance(key, (list, tuple)) or len(key) != 3:
            raise ValueError("'key' debe contener prioridad, magnitud e id")

        reporting_stations = item.get("reporting_stations", [])
        if not isinstance(reporting_stations, list):
            raise TypeError("'reporting_stations' debe ser una lista")

        station = reporting_stations[0] if reporting_stations else next(iter(station_ids), None)
        if station is None:
            raise ValueError("el evento debe referenciar una estación")

        return {
            "id": key[2],
            "magnitude": key[1],
            "depth": item.get("depth"),
            "epicenter_x": item.get("epicenter_x"),
            "epicenter_y": item.get("epicenter_y"),
            "datetime": item.get("datetime"),
            "revision": item.get("revision", 1),
            "station": station,
        }

    def _normalizeScenarioTree(self, tree):
        if not isinstance(tree, dict) or "root" not in tree:
            raise ValueError("la topología debe contener un root")

        def normalize_node(node):
            if node is None:
                return None, -1
            if not isinstance(node, dict) or "event" not in node:
                raise ValueError("cada nodo debe contener un event")

            left, left_height = normalize_node(node.get("left_child"))
            right, right_height = normalize_node(node.get("right_child"))
            height = 1 + max(left_height, right_height)
            return {
                "value": node["event"],
                "height": height,
                "left_child": left,
                "right_child": right,
                "node_creation_time": None,
            }, height

        root, _ = normalize_node(tree["root"])
        return {"root": root}

    # ===================== Métodos para el EventEngine =====================
    # El EventEngine trabaja con el observatorio que tiene en memoria
    # (el escenario activo), por eso estos métodos reciben la instancia
    # en lugar de cargarla desde disco.

    def saveObservatory(self, observatory):
        return self.repository.save(observatory)

    def nextAvailableEventId(self, observatory):
        used_ids = set(observatory.getAVLTree().index.keys())
        used_ids.update(observatory.getHistory().getArchived().keys())
        used_ids.update(observatory.getHistory().getDeletedIds())

        for event_id in range(1, 1000000):
            if event_id not in used_ids:
                return event_id

        raise RuntimeError("No hay ids disponibles.")

    def createGeneratedEvent(self, observatory, station, data):
        """
        Inserta un evento generado (por la IA) en el observatorio activo, lo
        guarda y devuelve la operación visual que se enviará al frontend.
        En modo normal el AVL se balancea; en modo estrés no.
        """
        if not observatory.getClock().canOccurAt(data["datetime"]):
            raise ValueError("La fecha del evento supera el reloj del escenario")
        event_id = self.nextAvailableEventId(observatory)
        mode = observatory.getExecutionMode()
        before_version = observatory.toVersion()
        before_indicators = self.metrics_service.capture_display(observatory)
        observatory.begin_visual_operation()

        result = observatory.createEvent(
            id=event_id,
            magnitude=data["magnitude"],
            depth=data["depth"],
            epicenter_x=data["epicenter_x"],
            epicenter_y=data["epicenter_y"],
            datetime=data["datetime"],
            revision=1,
            station=station.getId(),
        )

        if result is False or not all(result):
            raise ValueError("No se pudo insertar el evento generado")

        event = observatory.searchEventById(event_id)
        if event is None:
            raise ValueError("El evento generado no quedó en el árbol")

        steps = observatory.finish_visual_operation()
        self.metrics_service.refresh_derived_metrics(observatory)
        self.metrics_service.register_rotation_steps(
            observatory.getMetrics(),
            steps,
        )
        self.metrics_service.record_operation(
            observatory=observatory,
            action_type="create_event",
            before_version=before_version,
            before_indicators=before_indicators,
            details={
                "event_id": event_id,
                "source": "realtime",
            },
        )
        self.repository.save(observatory)

        return {
            "mode": mode,
            "stationId": station.getId(),
            "event": event.toDict(),
            "steps": steps,
        }

    def createManualEvent(self, observatory, data):
        """Inserta un evento manual y produce los parches para AVL y BST."""
        required = ("id", "magnitude", "depth", "epicenter_x", "epicenter_y", "datetime", "station")
        if not isinstance(data, dict) or any(field not in data for field in required):
            raise ValueError("Faltan datos obligatorios para crear el evento")

        event_id = data["id"]
        station_id = data["station"]
        if isinstance(event_id, bool) or not isinstance(event_id, int):
            raise ValueError("El id debe ser numérico entero")
        if isinstance(station_id, bool) or not isinstance(station_id, int):
            raise ValueError("La estación seleccionada no es válida")
        if station_id not in {station.getId() for station in observatory.getStations()}:
            raise ValueError("La estación seleccionada no pertenece al escenario")

        for field in ("magnitude", "depth", "epicenter_x", "epicenter_y"):
            value = data[field]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{field} debe ser numérico")
        if not hasAtMostOneDecimal(data["depth"]):
            raise ValueError("La profundidad admite máximo un decimal")

        try:
            event_datetime = parseDatetime(data["datetime"])
        except (TypeError, ValueError, AttributeError) as error:
            raise ValueError("La fecha del evento no es válida") from error
        if not observatory.getClock().canOccurAt(event_datetime):
            raise ValueError("La fecha del evento supera el reloj del escenario")

        before_version = observatory.toVersion()
        before_indicators = self.metrics_service.capture_display(observatory)
        observatory.begin_visual_operation()
        try:
            result = observatory.createEvent(
                id=event_id,
                magnitude=data["magnitude"],
                depth=data["depth"],
                epicenter_x=data["epicenter_x"],
                epicenter_y=data["epicenter_y"],
                datetime=event_datetime,
                revision=1,
                station=station_id,
            )
            steps = observatory.finish_visual_operation()
        except Exception:
            observatory.finish_visual_operation()
            raise

        if result is False or not all(result):
            raise ValueError("El id ya pertenece a un evento activo, eliminado o archivado")

        event = observatory.searchEventById(event_id)
        self.metrics_service.refresh_derived_metrics(observatory)
        self.metrics_service.register_rotation_steps(observatory.getMetrics(), steps)
        self.metrics_service.record_operation(
            observatory=observatory,
            action_type="create_manual_event",
            before_version=before_version,
            before_indicators=before_indicators,
            details={"event_id": event_id, "source": "manual"},
        )
        self.repository.save(observatory)

        return {
            "mode": observatory.getExecutionMode(),
            "stationId": station_id,
            "event": event.toDict(),
            "steps": steps,
        }

    def auditBalance(self, observatory):
        audit = observatory.getAVLTree().audit()
        return {
            "ok": audit["ok"],
            "balanced": audit["balanced"],
            "maxImbalance": audit["max_imbalance"],
            "issues": audit["issues"],
        }

    def auditStructure(self, observatory):
        mode = observatory.getExecutionMode()

        return {
            "mode": mode,
            "audit": observatory.getAVLTree().audit(mode),
            "indicators": self.metrics_service.capture_display(observatory),
        }
    
    def archiveAndGetTree(self, actualTime, T):
        observatory = self.getObservatory() 
        rootToArchivate, objectToPaintTree = observatory.archivateSubTree(actualTime, T)
        return rootToArchivate, objectToPaintTree
    
    def buildArchivedJson(self, currentRoot):
        observatory = self.getObservatory()
        avl = observatory.getAVLTree()
        node = avl.searchById(currentRoot.getValue().getKey()[2])
        nodeToDict = node.toDict()
        avl.eliminateReferences(node)
        return nodeToDict
    
    def getActiveEvents(self, observatory):
        events = []
        for event_id, node in observatory.getAVLTree().index.items():
            event = node.getValue()
            data = event.toDict()
            data["priority"] = event.getKey()[0]
            data["magnitude"] = event.getKey()[1]
            events.append(data)
        return events
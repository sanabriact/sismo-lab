import json
from backend.repositories.seismic_observatory_repository import SeismicObservatoryRepository
from backend.repositories.json_scenario_repository import JsonScenarioRepository
from backend.services.metrics.metrics_service import MetricsService
from backend.services.audit.structure_audit_service import StructureAuditService
from backend.services.ai_client.scenario_generator_client import AIScenarioGeneratorService
from backend.models.seismic_observatory import SeismicObservatory
from backend.models.report import Report
from backend.utils.quantities import parseDatetime, hasAtMostOneDecimal
from backend.services.parameters.scenario_parameters_service import ScenarioParametersService
from backend.services.scenario.scenario_builder_service import ScenarioBuilderService
from backend.services.scenario.scenario_errors import ScenarioValidationError

class SeismicObservatoryService:
    def __init__(self, parameters_service=None):
        self.repository = SeismicObservatoryRepository()
        self.scenario_repository = JsonScenarioRepository()
        self.metrics_service = MetricsService()
        self.parameters_service = parameters_service or ScenarioParametersService()
        self.scenario_builder = ScenarioBuilderService(
            self.parameters_service,
            self.metrics_service,
        )

    def getObservatory(self):
        observatory = self.repository.load()
        if observatory is None:
            observatory = SeismicObservatory()
        return observatory
 

    def build_manual_update_report(self, observatory, event_id, data):
        # These fields are required to create a valid update report.
        required = (
            "magnitude",
            "depth",
            "epicenter_x",
            "epicenter_y",
            "datetime",
            "station",
        )

        # Reject the request if its data is invalid or incomplete.
        if not isinstance(data, dict) or any(field not in data for field in required):
            raise ValueError("Faltan datos obligatorios para editar el evento")

        # The event can be active in the trees or archived in history.
        event = observatory.searchEventById(event_id)
        if event is None:
            event = observatory.getHistory().getArchived().get(event_id)
        if event is None:
            raise ValueError("El evento ya no existe")

        # Validate that the station ID is an integer.
        station_id = data["station"]
        if isinstance(station_id, bool) or not isinstance(station_id, int):
            raise ValueError("La estación seleccionada no es válida")

        # Create a quick lookup table for the scenario stations.
        stations = {
            station.getId(): station
            for station in observatory.getStations()
        }

        # The selected station must belong to the current scenario.
        station = stations.get(station_id)
        if station is None:
            raise ValueError("La estación no pertenece al escenario")

        # Validate numeric fields and allow only one decimal place.
        for field in ("magnitude", "depth", "epicenter_x", "epicenter_y"):
            value = data[field]

            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{field} debe ser numérico")

            if not hasAtMostOneDecimal(value):
                raise ValueError(f"{field} admite máximo un decimal")

        try:
            # Convert the received text into a valid UTC datetime.
            event_datetime = parseDatetime(data["datetime"])
        except (TypeError, ValueError, AttributeError) as error:
            raise ValueError("La fecha del evento no es válida") from error

        # The event cannot occur after the current simulation clock time.
        if not observatory.getClock().canOccurAt(event_datetime):
            raise ValueError("La fecha del evento supera el reloj del escenario")

        # Find pending corrections for this same event.
        # Their revisions are considered to avoid duplicate or old revisions.
        pending_revisions = [
            queued.getRevision()
            for queued in observatory.getReportQueue().items
            if queued.getEventId() == event_id
        ]

        # The new correction gets a revision greater than the event
        # and any pending correction for that event.
        revision = max(
            [event.getCurrentRevision(), *pending_revisions],
        ) + 1

        # Return a validated Report object ready to be applied or enqueued.
        return Report(
            event_id=event_id,
            revision=revision,
            station=station,
            magnitude=data["magnitude"],
            depth=data["depth"],
            epicenter_x=data["epicenter_x"],
            epicenter_y=data["epicenter_y"],
            datetime_=event_datetime,
        )

    # ===================== Carga de escenarios =====================
    # La carga es completa o no se aplica: primero se construye y valida un
    # observatorio nuevo; solo si no hay problemas se guarda en disco.

    def loadScenarioFromText(self, content):
        observatory = self.buildScenario(self.parseScenarioText(content))
        return observatory

    def loadScenarioFromAI(self, ai_mode):
        # Aún no hay generación de escenarios con la IA: "empty" usa una
        # configuración base (estaciones y zonas fijas, sin eventos).
        scenario_generator_service = AIScenarioGeneratorService()
        data = scenario_generator_service.generate(ai_mode)
        observatory = self.buildScenario(data)
        self.repository.save(observatory)
        return observatory

    def parseScenarioText(self, content):
        if not isinstance(content, str) or not content.strip():
            raise ScenarioValidationError(["El archivo está vacío"])
        try:
            data = self.scenario_repository.parse_text(content)
        except json.JSONDecodeError as error:
            raise ScenarioValidationError([
                f"JSON inválido (línea {error.lineno}, columna {error.colno}): {error.msg}"
            ])
        except ValueError as error:
            raise ScenarioValidationError([str(error)])
        if isinstance(data, dict) and "seismic_observatory" in data:
            data = data["seismic_observatory"]
        if not isinstance(data, dict):
            raise ScenarioValidationError(["El escenario debe ser un objeto JSON"])
        return data

    def buildScenario(self, data):
        """Build a scenario through the dedicated builder service."""
        return self.scenario_builder.build(data)

    def _buildFromInsertions(self, data, mode):
        """Compatibility entry point that uses the canonical scenario builder."""
        return self.scenario_builder.build({**data, "execution_mode": mode})

    def _buildFromTopology(self, data, mode):
        """Compatibility entry point that uses the canonical scenario builder."""
        return self.scenario_builder.build({**data, "execution_mode": mode})

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

    def _create_event(self, observatory, event_id, station_id, data, action_type, source, failure_reason):
        """Insert one event and apply the shared metrics and persistence steps."""
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
                datetime=data["datetime"],
                revision=1,
                station=station_id,
            )
            steps = observatory.finish_visual_operation()
        except Exception:
            observatory.finish_visual_operation()
            raise

        if result is False or not all(result):
            raise ValueError(failure_reason)

        event = observatory.searchEventById(event_id)
        if event is None:
            raise ValueError("El evento creado no quedó en el árbol")

        self.metrics_service.refresh_derived_metrics(observatory)
        self.metrics_service.register_rotation_steps(observatory.getMetrics(), steps)
        self.metrics_service.record_operation(
            observatory=observatory,
            action_type=action_type,
            before_version=before_version,
            before_indicators=before_indicators,
            details={"event_id": event_id, "source": source},
        )
        self.repository.save(observatory)

        return {
            "mode": observatory.getExecutionMode(),
            "stationId": station_id,
            "event": event.toDict(),
            "steps": steps,
        }

    def createGeneratedEvent(self, observatory, station, data):
        """
        Inserta un evento generado (por la IA) en el observatorio activo, lo
        guarda y devuelve la operación visual que se enviará al frontend.
        En modo normal el AVL se balancea; en modo estrés no.
        """
        if not observatory.getClock().canOccurAt(data["datetime"]):
            raise ValueError("La fecha del evento supera el reloj del escenario")
        event_id = self.nextAvailableEventId(observatory)
        return self._create_event(
            observatory,
            event_id,
            station.getId(),
            data,
            "create_event",
            "realtime",
            "No se pudo insertar el evento generado",
        )

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

        return self._create_event(
            observatory,
            event_id,
            station_id,
            {**data, "datetime": event_datetime},
            "create_manual_event",
            "manual",
            "El id ya pertenece a un evento activo, eliminado o archivado",
        )

    def auditBalance(self, observatory):
        audit = StructureAuditService().audit_avl(observatory.getAVLTree())
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
            "audit": StructureAuditService().audit_avl(
                observatory.getAVLTree(),
                mode,
            ),
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

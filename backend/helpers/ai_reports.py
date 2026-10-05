import json
import os
import random
from datetime import timedelta

from dotenv import load_dotenv
from groq import Groq

from backend.utils.quantities import hasAtMostOneDecimal, parseDatetime

load_dotenv()


REPORT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["reports"],
    "properties": {
        "reports": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "event_id",
                    "revision",
                    "station",
                    "magnitude",
                    "depth",
                    "epicenter_x",
                    "epicenter_y",
                    "datetime",
                ],
                "properties": {
                    "event_id": {"type": "integer"},
                    "revision": {"type": "integer"},
                    "station": {"type": "integer"},
                    "magnitude": {"type": "number"},
                    "depth": {"type": "number"},
                    "epicenter_x": {"type": "number"},
                    "epicenter_y": {"type": "number"},
                    "datetime": {"type": "string"},
                },
            },
        }
    },
}


class AIReportClient:
    """Generate report batches using the same Groq pattern as the scenario client."""

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY_REPORTS")
        model = os.getenv("GROQ_MODEL")
        self.client = Groq(api_key=api_key)
        self.model = model

    def generate(self, context, count, scenario_hint=None):
        prompt = self._build_prompt(context, count, scenario_hint)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You generate valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_completion_tokens=8192,
            reasoning_effort="low",
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "reports",
                    "strict": True,
                    "schema": REPORT_SCHEMA,
                },
            },
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("La IA no devolvió contenido")

        try:
            data = json.loads(content)
        except json.JSONDecodeError as error:
            raise ValueError(f"La IA devolvió un JSON inválido: {error}") from error

        reports = data.get("reports")
        if not isinstance(reports, list):
            raise ValueError("La IA no devolvió una lista de reportes")

        return reports[:count]

    def _build_prompt(self, context, count, scenario_hint):
        existing = context["events"]
        return f"""
                Genera exactamente {count} reportes sísmicos ficticios para SismoLab.

                RELOJ:
                {context["clock"]}

                ESTACIONES VÁLIDAS:
                {context["station_ids"]}

                EVENTOS ACTIVOS O ARCHIVADOS:
                {json.dumps(existing, ensure_ascii=False)}

                IDs ELIMINADOS (NO USAR):
                {context["deleted_ids"]}

                REGLAS DE IDENTIDAD:
                1. Un reporte crea un evento ÚNICAMENTE si su event_id no existe entre los eventos
                activos ni archivados Y revision = 1.
                2. Si event_id ya existe en activos o archivados, el reporte debe usar ese mismo id.
                3. Para un evento existente puedes generar:
                - revision igual a la actual y exactamente los mismos datos: confirmación;
                - revision menor que la actual: reporte antiguo;
                - revision mayor que la actual: corrección.
                4. Nunca generes revision > 1 para un event_id que no exista en activos o archivados.
                5. No uses IDs eliminados.

                REGLAS DE DATOS:
                - event_id entero entre 1 y 999999.
                - revision entero positivo.
                - station debe pertenecer a las estaciones válidas.
                - magnitude entre -2.0 y 10.0.
                - depth entre 0.0 y 700.0.
                - epicenter_x y epicenter_y entre 0.0 y 1000.0.
                - todos los valores numéricos tienen máximo un decimal.
                - datetime es UTC ISO-8601 y no puede superar el reloj.
                - Para confirmaciones, conserva exactamente magnitud, profundidad, epicentro y fecha
                del evento existente y cambia solamente la estación si quieres representar otra estación.
                - Para correcciones, aumenta la revisión y modifica al menos un dato del evento.
                - Prioriza una mezcla natural de creaciones, confirmaciones y correcciones.
                - Si no hay eventos existentes, genera creaciones nuevas con revision 1.

                CONTEXTO OPCIONAL:
                {scenario_hint or "sin contexto adicional"}

                Devuelve únicamente el JSON solicitado por el esquema.
                """


def request_reports_from_llm(context, count, scenario_hint=None):
    """Compatibility wrapper around the report client."""
    return AIReportClient().generate(context, count, scenario_hint)


def generate_deterministic_reports(context, count, seed):
    """Deterministic fallback that respects active/archived identity semantics."""
    rng = random.Random(seed)
    clock = context["clock"]
    stations = list(context["station_ids"])
    existing = list(context["events"])
    used_ids = set(context["used_ids"])
    reports = []

    for _ in range(count):
        if not stations:
            break

        if not existing:
            kind = "new"
        else:
            kind = rng.choice(["new", "new", "confirm", "stale", "correct"])

        station = rng.choice(stations)

        if kind == "new":
            new_id = rng.randint(1, 999_999)
            while new_id in used_ids:
                new_id = rng.randint(1, 999_999)
            used_ids.add(new_id)

            report = {
                "event_id": new_id,
                "revision": 1,
                "station": station,
                "magnitude": round(rng.uniform(1.0, 7.5), 1),
                "depth": round(rng.uniform(0.0, 120.0), 1),
                "epicenter_x": round(rng.uniform(0.0, 1000.0), 1),
                "epicenter_y": round(rng.uniform(0.0, 1000.0), 1),
                "datetime": (
                    clock - timedelta(minutes=rng.randint(1, 4000))
                ).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            reports.append(report)
            continue

        base = dict(rng.choice(existing))
        base["station"] = station

        if kind == "confirm":
            pass
        elif kind == "stale":
            if base["revision"] > 1:
                base["revision"] -= 1
            else:
                # Revision 1 has no valid stale predecessor; keep it as a confirmation.
                kind = "confirm"
        elif kind == "correct":
            base["revision"] += 1
            base["magnitude"] = round(
                min(10.0, base["magnitude"] + rng.choice([0.5, 1.0, 1.5])), 1
            )

        reports.append(base)

    return reports


def validate_generated_report_shape(report, station_ids, clock):
    """Validate only transport/domain shape; identity is validated by EventEngine."""
    if not isinstance(report, dict):
        return "El reporte debe ser un objeto"

    required = (
        "event_id",
        "revision",
        "station",
        "magnitude",
        "depth",
        "epicenter_x",
        "epicenter_y",
        "datetime",
    )
    missing = [field for field in required if field not in report]
    if missing:
        return f"Faltan campos: {', '.join(missing)}"

    if not isinstance(report["event_id"], int) or not 1 <= report["event_id"] <= 999999:
        return "event_id inválido"
    if not isinstance(report["revision"], int) or report["revision"] <= 0:
        return "revision inválida"
    if report["station"] not in station_ids:
        return f"La estación {report['station']} no pertenece al escenario"

    for field, minimum, maximum in (
        ("magnitude", -2.0, 10.0),
        ("depth", 0.0, 700.0),
        ("epicenter_x", 0.0, 1000.0),
        ("epicenter_y", 0.0, 1000.0),
    ):
        value = report[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return f"{field} debe ser numérico"
        if not hasAtMostOneDecimal(value):
            return f"{field} admite máximo un decimal"
        if not minimum <= value <= maximum:
            return f"{field} fuera de rango"

    try:
        date = parseDatetime(report["datetime"])
    except (TypeError, ValueError, KeyError):
        return "datetime inválido"

    if not clock.canOccurAt(date):
        return "La fecha del reporte supera el reloj del escenario"

    return None

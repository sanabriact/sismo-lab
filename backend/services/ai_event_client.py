import json
import math
import os
from datetime import datetime, timezone

from openai import OpenAI


class AIEventClient:
    def __init__(self):
        """ self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"]) """
        self.model = os.getenv("OPENAI_MODEL", "gpt-5-mini")

    def generate_event_data(self, station, scenario_clock, zones):
        current_time = scenario_clock.current_time.astimezone(timezone.utc)

        prompt = f"""
            You simulate a seismic station in a fictional academic scenario.

            Station:
            - id: {station.id}
            - name: {station.name}

            Simulation clock:
            - current UTC time: {current_time.isoformat()}

            Return ONLY valid JSON with these fields:
            {{
                "magnitude": number,
                "depth": number,
                "epicenter_x": number,
                "epicenter_y": number,
                "datetime": "ISO-8601 UTC"
            }}

            Rules:
            - magnitude: -2.0 to 10.0, at most one decimal.
            - depth: 0.0 to 700.0, at most one decimal.
            - epicenter_x and epicenter_y: 0.0 to 1000.0, at most one decimal.
            - datetime cannot be later than the simulation clock.
            - This is fictional simulation data.
            """

        response = self.client.responses.create(
            model=self.model,
            input=prompt,
        )

        return json.loads(response.output_text)
    
def validate_ai_response(data, clock):
    magnitude = round(float(data["magnitude"]), 1)
    depth = round(float(data["depth"]), 1)
    x = round(float(data["epicenter_x"]), 1)
    y = round(float(data["epicenter_y"]), 1)

    date = datetime.fromisoformat(data["datetime"].replace("Z", "+00:00"))
    date = date.astimezone(timezone.utc)

    if not -2 <= magnitude <= 10:
        raise ValueError("Magnitud inválida")

    if not 0 <= depth <= 700:
        raise ValueError("Profundidad inválida")

    if not 0 <= x <= 1000 or not 0 <= y <= 1000:
        raise ValueError("Epicentro inválido")

    if date > clock.current_time:
        raise ValueError("La fecha supera el reloj del escenario")

    return {
        "magnitude": magnitude,
        "depth": depth,
        "epicenter_x": x,
        "epicenter_y": y,
        "datetime": date,
    }
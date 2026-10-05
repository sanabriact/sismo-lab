import json
import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from backend.utils.quantities import parseDatetime

# Path of the .env file located three levels above this file
env_path = Path(__file__).resolve().parent.parent.parent / ".env"

# Load the environment variables from the .env file
load_dotenv(env_path)

# JSON schema that the AI response must follow
EVENT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "magnitude": {
            "type": "number",
        },
        "depth": {
            "type": "number",
        },
        "epicenter_x": {
            "type": "number",
        },
        "epicenter_y": {
            "type": "number",
        },
        "datetime": {
            "type": "string",
        },
    },
    "required": [
        "magnitude",
        "depth",
        "epicenter_x",
        "epicenter_y",
        "datetime",
    ],
}

# -----------------------------------------------------------------------------
# Validation of the AI response
# -----------------------------------------------------------------------------

# Validate the AI response and return its values rounded and converted
def validate_ai_response(data, clock):
    magnitude = round(float(data["magnitude"]), 1)
    depth = round(float(data["depth"]), 1)
    x = round(float(data["epicenter_x"]), 1)
    y = round(float(data["epicenter_y"]), 1)

    date = parseDatetime(data["datetime"])

    if not -2 <= magnitude <= 10:
        raise ValueError("Magnitud inválida")

    if not 0 <= depth <= 700:
        raise ValueError("Profundidad inválida")

    if not 0 <= x <= 1000 or not 0 <= y <= 1000:
        raise ValueError("Epicentro inválido")

    if not clock.canOccurAt(date):
        raise ValueError("La fecha supera el reloj del escenario")

    return {
        "magnitude": magnitude,
        "depth": depth,
        "epicenter_x": x,
        "epicenter_y": y,
        "datetime": date,
    }


class AIEventClient:

    # Initialize the client with the Groq API key and model from the environment
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY_REPORTS")
        model = os.getenv("GROQ_MODEL")
        self.client = Groq(api_key=api_key)
        self.model = model

    # -------------------------------------------------------------------------
    # Generating events with the AI
    # -------------------------------------------------------------------------

    # Request one fictional seismic event for a station from the AI
    def generate(self, station, clock):
        current_time = clock.getCurrentTimeText()

        prompt = f"""
                    Generate one fictional seismic event for this station.

                    Station ID: {station.id}
                    Station name: {station.name}

                    Simulation clock in UTC: {current_time}

                    Return JSON only.

                    Rules:
                    - magnitude must be between -2.0 and 10.0.
                    - depth must be between 0.0 and 700.0.
                    - epicenter_x and epicenter_y must be between 0.0 and 1000.0.
                    - datetime must be UTC ISO-8601.
                    - datetime cannot be later than the simulation clock.
                    - Use at most one decimal for all numeric values.
                """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You generate valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "seismic_event",
                    "strict": True,
                    "schema": EVENT_SCHEMA
                }
            }
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("La IA no devolvió contenido")

        return json.loads(content)
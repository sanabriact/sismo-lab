import json
import os
import random
from datetime import timedelta, datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from backend.utils.quantities import parseDatetime

# Accepted spellings for the three generation modes (Spanish and English).
VALID_MODES = ("empty", "insertion", "topology")

SCENARIO_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["stations", "zones", "events"],
    "properties": {
        "stations": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["id", "name", "x", "y"],
            "properties": {"id": {"type": "integer"}, "name": {"type": "string"},
                           "x": {"type": "number"}, "y": {"type": "number"}}}},
        "zones": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["id", "name", "x_min", "x_max", "y_min", "y_max", "is_populated"],
            "properties": {"id": {"type": "integer"}, "name": {"type": "string"},
                           "x_min": {"type": "number"}, "x_max": {"type": "number"},
                           "y_min": {"type": "number"}, "y_max": {"type": "number"},
                           "is_populated": {"type": "boolean"}}}},
        "events": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["id", "magnitude", "depth", "epicenter_x", "epicenter_y",
                         "datetime", "revision", "station"],
            "properties": {"id": {"type": "integer"}, "magnitude": {"type": "number"},
                           "depth": {"type": "number"}, "epicenter_x": {"type": "number"},
                           "epicenter_y": {"type": "number"}, "datetime": {"type": "string"},
                           "revision": {"type": "integer"}, "station": {"type": "integer"}}}},
    },
}

# In the request:
response_format={
    "type": "json_schema",
    "json_schema": {"name": "scenario", "strict": True, "schema": SCENARIO_SCHEMA},
}

# Placeholders use <<NAME>> so they never collide with the JSON braces
# inside the prompt (an f-string would break on them).
SCENARIO_PROMPT_TEMPLATE = """Eres un generador de escenarios de prueba para SismoLab AVL, un simulador académico
de un observatorio sísmico ficticio. Tu ÚNICA salida es un objeto JSON válido.
No escribas texto antes ni después, no uses bloques de código markdown, no pongas
comentarios dentro del JSON.

PARÁMETROS DE ESTA SOLICITUD
- MODE: <<MODE>>                      (insertion | topology | empty)
- CLOCK: <<CLOCK>>                    (reloj de simulación)
- N_STATIONS: <<N_STATIONS>>
- N_ZONES: <<N_ZONES>>
- N_EVENTS: <<N_EVENTS>>              (0 si MODE es empty)
- EXECUTION_MODE: <<EXECUTION_MODE>>  (normal | stress)

========================================================
PARTE 1. REGLAS COMUNES (se aplican a los tres modos)
========================================================

Plano: el territorio es un plano de 0 a 1000 km en X y en Y.
Todo número decimal tiene como máximo UN decimal (ej. 4.5 sí, 4.55 no).
Usa punto como separador decimal.

1) Reloj de simulación (CLOCK = <<CLOCK>>)
   - Ningún evento puede ocurrir DESPUÉS de CLOCK.
   - Reparte las fechas de los eventos en los 10 días anteriores a CLOCK.
   - CLOCK NO se escribe en la salida: lo agrega el sistema.

2) "stations" (exactamente N_STATIONS)
   - Cada una: {"id": int, "name": str, "x": num, "y": num}
   - ids enteros consecutivos desde 1. Nombres distintos y descriptivos.
   - x, y entre 0.0 y 1000.0, repartidas por el plano (no todas juntas).

3) "zones" (exactamente N_ZONES)
   - Cada una: {"id": int, "name": str, "x_min": num, "x_max": num,
                "y_min": num, "y_max": num, "is_populated": bool}
   - ids enteros consecutivos desde 1.
   - Rectángulos con 0 <= x_min < x_max <= 1000 y 0 <= y_min < y_max <= 1000.
   - Debe haber al menos una zona poblada (true) y al menos una NO poblada (false).
   - Los interiores no deben solaparse. Pueden compartir borde (ej. una termina en
     x=500 y otra empieza en x=500). NO es obligatorio cubrir todo el plano: un punto
     fuera de toda zona se considera no poblado.
   - Zonas con tamaños variados, no todas iguales.

4) Pertenencia a zona poblada de un epicentro (x, y)
   - Está en una zona si x_min <= x <= x_max y y_min <= y <= y_max (bordes incluidos).
   - Es poblado si pertenece a AL MENOS UNA zona con is_populated = true
     (si está en el borde entre una poblada y una no poblada, es poblado).

5) Datos de un evento (rangos válidos)
   - id: entero 1..999999, único, nunca repetido.
   - magnitude: -2.0 a 10.0
   - depth (profundidad del hipocentro en km): 0.0 a 700.0
   - epicenter_x, epicenter_y: 0.0 a 1000.0
   - datetime: ISO 8601 UTC con segundos y sufijo Z, por ejemplo "2026-03-22T08:00:00Z",
     y siempre <= CLOCK
   - revision: siempre 1
   - station: id de una estación que exista en "stations"

6) Prioridad (solo para que ordenes y diseñes los datos; NO se escribe en la salida)
   Aplica en este orden:
   - 3 (alta):  M >= 6.0, o bien (M >= 4.5 y H <= 30.0 y epicentro poblado)
   - 2 (media): no es alta y M >= 4.5
   - 1 (baja):  todo lo demás
   Los límites son inclusivos (M=4.5, H=30.0 en zona poblada => prioridad 3).
   La clave de un evento es (P, M, id) y se compara en ese orden: primero P,
   luego M, luego id. (P=2 siempre es menor que P=3, aunque su M sea mayor.)

7) Variedad (aplica cuando N_EVENTS > 0)
   Genera datos realistas y diversos. Incluye de forma natural, sin exagerar:
   - magnitudes en los tres rangos de prioridad,
   - al menos un evento con M exactamente 4.5, uno con M 6.0 y uno con H 30.0,
   - al menos un epicentro exactamente sobre el borde de una zona,
   - al menos dos eventos con igual prioridad e igual magnitud pero distinto id,
   - algunos eventos cercanos entre sí (<= 40 km y <= 48 h) donde el más antiguo
     tenga mayor magnitud, para que existan candidatos a réplica.

========================================================
PARTE 2. FORMA DE LA SALIDA (igual para los tres modos)
========================================================

Devuelve un único objeto con EXACTAMENTE estas tres claves:
{
  "stations": [...],
  "zones": [...],
  "events": [...]
}
- No agregues ninguna otra clave: ni "tree", ni "execution_mode", ni "datetime".
- Cada estación tiene EXACTAMENTE: {"id": int, "name": str, "x": num, "y": num}
  (sin "emmited_events" ni otros campos).
- Cada evento tiene EXACTAMENTE estos campos:
  {"id": int, "magnitude": num, "depth": num, "epicenter_x": num,
   "epicenter_y": num, "datetime": "...Z", "revision": 1, "station": int}
- No incluyas prioridad, clave, zona poblada ni ningún campo derivado:
  el sistema los calcula.
- Ids de eventos únicos dentro del archivo (un id repetido invalida el escenario).

Número de eventos y orden del arreglo "events" según MODE:

--- MODE = "empty" ---
"events" es una lista vacía [].

--- MODE = "insertion" o MODE = "topology" ---
"events" tiene exactamente N_EVENTS eventos. El ORDEN del arreglo es el orden
en que el sistema los inserta en el árbol, así que depende de EXECUTION_MODE:
- EXECUTION_MODE = "normal": mezcla el orden (no lo dejes ordenado). Incluye una
  subsecuencia de 3 o 4 eventos con claves (P, M, id) en orden ascendente, para
  que un árbol sin balanceo se degrade frente a uno AVL.
- EXECUTION_MODE = "stress": ordena la mayor parte del arreglo (al menos la mitad
  inicial) de menor a mayor clave (P, luego M, luego id), una tras otra. Así el
  árbol queda desbalanceado a propósito, con diferencias de altura de 2 o más.
  Los eventos restantes pueden ir al final en cualquier orden.

========================================================
AUTOVERIFICACIÓN FINAL (hazla en silencio antes de responder)
========================================================
- ¿El JSON parsea? ¿Hay solo UN objeto con las claves stations, zones y events?
- ¿Número exacto de estaciones, zonas y eventos pedidos?
- ¿Todos los números con máximo un decimal y dentro de rango?
- ¿Ningún evento posterior a CLOCK? ¿Ids únicos? ¿Cada "station" existe?
- ¿Hay al menos una zona poblada y una no poblada, sin solapar interiores?
- ¿El orden del arreglo "events" respeta EXECUTION_MODE?
Si alguna comprobación falla, corrige antes de responder.
"""
def generate_random_clock():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    span_seconds = int((end - start).total_seconds())
    clock = start + timedelta(seconds=random.randint(0, span_seconds))
    return clock.strftime("%Y-%m-%dT%H:%M:%SZ")

class AIScenarioGeneratorService:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY_SCENARIO")
        model = os.getenv("GROQ_MODEL")
        self.client = Groq(api_key=api_key)
        self.model = model

    def generate(self, mode):
        if mode not in VALID_MODES:
            raise ValueError(f"Modo de generación no soportado: {mode}. Utiliza {', '.join(VALID_MODES)}")
        current_time = generate_random_clock()
        station_quantity = random.randint(1, 9)
        zone_quantity = random.randint(2, 5)
        event_quantity = {
            "empty": 0,
            "insertion": random.randint(10, 20),
            "topology": random.randint(7, 15),  # small: the AI must build the tree by hand
        }[mode]
        execution_mode = "normal"
        replacements = {
            "<<MODE>>": mode,
            "<<CLOCK>>": current_time,
            "<<N_STATIONS>>": str(station_quantity),
            "<<N_ZONES>>": str(zone_quantity),
            "<<N_EVENTS>>": str(event_quantity),
            "<<EXECUTION_MODE>>": execution_mode,
        }
        
        prompt = SCENARIO_PROMPT_TEMPLATE
        for placeholder, value in replacements.items():
            prompt = prompt.replace(placeholder, value)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You generate valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_completion_tokens=16384,
            reasoning_effort="low",
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "scenario",
                    "strict": True,
                    "schema": SCENARIO_SCHEMA,
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

        # Never trust the model for values we already know.
        data["datetime"] = current_time
        data["execution_mode"] = execution_mode

        return data

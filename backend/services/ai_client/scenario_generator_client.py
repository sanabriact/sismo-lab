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
No escribas texto antes ni después, no uses bloques de markdown (```), no pongas
comentarios dentro del JSON.

PARÁMETROS DE ESTA SOLICITUD
- MODE: <<MODE>>                      (insertion | topology | empty)
- CLOCK: <<CLOCK>>                    (reloj de simulación, úsalo tal cual)
- N_STATIONS: <<N_STATIONS>>
- N_ZONES: <<N_ZONES>>
- N_EVENTS: <<N_EVENTS>>              (0 si MODE es empty)
- EXECUTION_MODE: <<EXECUTION_MODE>>  (solo aplica a topology: normal | stress)

========================================================
PARTE 1. REGLAS COMUNES (se aplican a los tres modos)
========================================================

Plano: el territorio es un plano de 0 a 1000 km en X y en Y.
Todo número decimal tiene como máximo UN decimal (ej. 4.5 sí, 4.55 no).
Usa punto como separador decimal.

1) "datetime" (reloj de simulación)
   - Debe ser EXACTAMENTE el valor de CLOCK: <<CLOCK>>
   - Ningún evento puede ocurrir DESPUÉS de este reloj. Reparte los eventos en los
     10 días anteriores al reloj.

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
   - datetime: ISO 8601 UTC con segundos y sufijo Z, <= reloj del escenario
   - revision: entero positivo

6) Prioridad (se DERIVA, nunca se inventa). Aplica en este orden:
   - 3 (alta):  M >= 6.0, o bien (M >= 4.5 y H <= 30.0 y epicentro poblado)
   - 2 (media): no es alta y M >= 4.5
   - 1 (baja):  todo lo demás
   Los límites son inclusivos (M=4.5, H=30.0 en zona poblada => prioridad 3).

7) Variedad (aplica a los modos con eventos)
   Genera datos realistas y diversos. Incluye de forma natural, sin exagerar:
   - magnitudes en los tres rangos de prioridad,
   - al menos un evento con M exactamente 4.5, uno con M 6.0 y uno con H 30.0,
   - al menos un epicentro exactamente sobre el borde de una zona,
   - al menos dos eventos con igual prioridad e igual magnitud pero distinto id,
   - algunos eventos cercanos entre sí (<= 40 km y <= 48 h) donde el más antiguo
     tenga mayor magnitud, para que existan candidatos a réplica.

========================================================
PARTE 2. FORMA DE LA SALIDA SEGÚN MODE
========================================================

--- MODE = "empty" ---
Genera SOLO el escenario base, sin eventos:
{
  "execution_mode": "normal",
  "datetime": "<<CLOCK>>",
  "stations": [...],
  "zones": [...],
  "events": []
}
No incluyas la clave "tree".

--- MODE = "insertion" ---
Igual que "empty" pero con N_EVENTS eventos en "events".
- "execution_mode" siempre "normal".
- El ORDEN del arreglo es el orden de inserción: mézclalo (no lo dejes ordenado).
  Incluye una subsecuencia de 3 o 4 eventos cuyas claves (prioridad, magnitud, id)
  vayan en orden ascendente, para que el BST se degrade frente al AVL.
- Cada evento tiene EXACTAMENTE estos campos:
  {"id": int, "magnitude": num, "depth": num, "epicenter_x": num,
   "epicenter_y": num, "datetime": "...Z", "revision": 1, "station": int}
- "station" debe ser el id de una estación existente.
- Ids únicos dentro del archivo (un id repetido invalida todo el escenario).
- No incluyas la clave "tree" ni campos derivados (prioridad, clave, etc.).

--- MODE = "topology" ---
Genera el escenario base (sin la clave "events") y en su lugar la clave "tree"
con la topología explícita del árbol, de N_EVENTS nodos:
{
  "execution_mode": "<<EXECUTION_MODE>>",
  "datetime": "<<CLOCK>>",
  "stations": [...],
  "zones": [...],
  "tree": { "root": <nodo o null> }
}
En este modo cada estación lleva además "emmited_events": [] (lista vacía):
{"id": int, "name": str, "x": num, "y": num, "emmited_events": []}

Cada nodo tiene la forma:
{ "event": {...}, "left_child": <nodo o null>, "right_child": <nodo o null> }
Un enlace vacío se escribe null. No escribas alturas ni factores de balance
(el sistema los calcula).

Cada "event" tiene EXACTAMENTE estos campos:
{
  "key": [P, M, I],                 // prioridad, magnitud, id numérico
  "epicenter_x": num, "epicenter_y": num,
  "depth": num,                     // km del hipocentro
  "datetime": "...Z",
  "revision": 1,
  "reporting_stations": [int],      // ids de estaciones existentes
  "attention_status": "pending" | "revised",
  "event_status": "active",
  "populated_zone": bool,           // según la regla 4
  "expensive_acces": bool,          // ver paso 6
  "eliminated": false,
  "archived": false
}

PROCEDIMIENTO OBLIGATORIO (síguelo en orden antes de escribir el JSON):
 1. Genera los N_EVENTS eventos con ids únicos y datos válidos.
 2. Para cada uno calcula populated_zone (regla 4) y luego P (regla 6).
    "key" = [P, M, id]. Debe coincidir EXACTAMENTE con lo calculado.
 3. Ordena los eventos de menor a mayor clave, comparando en este orden:
    P, luego M, luego id. (P=2 siempre va antes que P=3, aunque su M sea mayor.)
 4. Construye el árbol según EXECUTION_MODE:
    - "normal": árbol BST perfectamente equilibrado. Con la lista ordenada, la raíz
      es el elemento del medio (si hay dos centrales, el de la izquierda); repite
      recursivamente en cada mitad. Resultado: en todo nodo, la diferencia de
      altura entre subárbol izquierdo y derecho es -1, 0 o 1.
    - "stress": árbol BST válido pero DESBALANCEADO a propósito. Inserta las claves
      en un orden que degrade el árbol (por ejemplo, la mitad de ellas en orden
      ascendente, una tras otra, SIN rotaciones) hasta que al menos un nodo tenga
      una diferencia de alturas de 2 o más. El orden BST debe seguir siendo correcto.
 5. Verifica el orden global: todo nodo del subárbol izquierdo tiene clave menor
    que la raíz de ese subárbol, y todo nodo del derecho, clave mayor (no basta
    con comparar al hijo inmediato). Cada evento aparece UNA sola vez en el árbol.
 6. expensive_acces = true solo si P = 3 y la profundidad del nodo en el árbol
    (raíz = 0) es estrictamente mayor que 3. En caso contrario, false.

EJEMPLO MÍNIMO de "tree" (3 nodos, árbol normal; claves A < B < C):
"tree": {"root": {
  "event": {"key": [2, 5.1, 2], "epicenter_x": 210.0, "epicenter_y": 150.0,
            "depth": 45.0, "datetime": "2026-09-27T14:40:00Z", "revision": 1,
            "reporting_stations": [2], "attention_status": "pending",
            "event_status": "active", "populated_zone": true,
            "expensive_acces": false, "eliminated": false, "archived": false},
  "left_child": {"event": {"key": [1, 2.4, 1], ...}, "left_child": null, "right_child": null},
  "right_child": {"event": {"key": [3, 6.3, 3], ...}, "left_child": null, "right_child": null}
}}
(Los "..." son solo para abreviar este ejemplo; en tu salida escribe todos los campos.)

========================================================
AUTOVERIFICACIÓN FINAL (hazla en silencio antes de responder)
========================================================
- ¿El JSON parsea? ¿Hay solo UN objeto raíz y nada de texto fuera de él?
- ¿Número exacto de estaciones, zonas y eventos pedidos?
- ¿Todos los números con máximo un decimal y dentro de rango?
- ¿Ningún evento posterior al reloj? ¿Ids únicos? ¿Estaciones referenciadas existentes?
- Si es topology: ¿las claves coinciden con la prioridad calculada? ¿Orden BST global
  correcto? ¿Balance acorde a EXECUTION_MODE?
Si alguna comprobación falla, corrige antes de responder.
"""
def generate_random_clock():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    span_seconds = int((end - start).total_seconds())
    clock = start + timedelta(seconds=random.randint(0, span_seconds))
    return clock.strftime("%Y-%m-%dT%H:%M:%SZ")

class ScenarioGeneratorService:
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
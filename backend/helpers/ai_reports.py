import json
import random
from datetime import timedelta

def request_reports_from_llm(context, count, scenario_hint):
    """Ask the LLM for `count` reports as strict JSON and return them as a list of dicts."""
    system = (
        "You generate simulated seismic reports. Reply ONLY with a JSON array, no prose, no markdown. "
        "Each item: id (int 1-999999), magnitude (-2.0..10.0, 1 decimal), depth (0.0..700.0, 1 decimal), "
        "x and y (0.0..1000.0, 1 decimal), occurred_at (ISO 8601 UTC, never after the given clock), "
        "revision (int >= 1), station_id (one of the given stations)."
    )
    user = json.dumps({"count": count, "hint": scenario_hint, **context})
    raw = call_llm(system, user)  # ASSUMPTION: your existing LLM client wrapper
    raw = raw.strip().removeprefix("```json").removesuffix("```").strip()
    parsed = json.loads(raw)
    return parsed if isinstance(parsed, list) else []


def generate_deterministic_reports(context, count, seed):
    """Build a reproducible mix of new events, confirmations, stale reports and corrections."""
    rng = random.Random(seed)
    clock = context["clock"]  # datetime
    stations = context["station_ids"]
    existing = context["events"]  # list of report-shaped dicts with the current revision
    used_ids = set(context["used_ids"])  # active + archived + deleted + queued
    reports = []

    for _ in range(count):
        kind = rng.choice(["new", "new", "new", "confirm", "stale", "correct"]) if existing else "new"
        station = rng.choice(stations)

        if kind == "new":
            new_id = rng.randint(1, 999_999)
            while new_id in used_ids:
                new_id = rng.randint(1, 999_999)
            used_ids.add(new_id)
            reports.append({
                "id": new_id,
                "magnitude": round(rng.uniform(1.0, 7.5), 1),
                "depth": round(rng.uniform(0.0, 120.0), 1),
                "x": round(rng.uniform(0.0, 1000.0), 1),
                "y": round(rng.uniform(0.0, 1000.0), 1),
                "occurred_at": (clock - timedelta(minutes=rng.randint(1, 4000))).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "revision": 1,
                "station_id": station,
            })
            continue

        base = dict(rng.choice(existing))
        base["station_id"] = station
        if kind == "stale" and base["revision"] > 1:
            base["revision"] -= 1
        elif kind == "correct":
            base["revision"] += 1
            base["magnitude"] = round(min(10.0, base["magnitude"] + rng.choice([0.5, 1.0, 1.5])), 1)
        reports.append(base)  # "confirm" keeps the same revision and data, only the station changes

    return reports
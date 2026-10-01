from datetime import datetime, timezone


def toTenths(value):
    # Compare quantities as integer tenths to avoid float errors
    return int(round(float(value) * 10))


def hasAtMostOneDecimal(value):
    scaled = float(value) * 10
    return abs(scaled - round(scaled)) < 1e-9


def normalizeDatetime(value):
    # Every datetime in the system is UTC, timezone-aware, second precision
    if not isinstance(value, datetime):
        raise TypeError("value must be a datetime object")
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0)


def parseDatetime(text):
    # Accepts ISO 8601, including the trailing Z shown in the specification.
    # The Z is removed only when it is the last character: a blind replace would
    # corrupt any other Z in the string.
    if not isinstance(text, str):
        raise TypeError(
            f"Expected an ISO 8601 string, not {type(text).__name__}"
        )
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return normalizeDatetime(datetime.fromisoformat(text))
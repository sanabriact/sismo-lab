from datetime import datetime, timedelta
import math
from backend.utils.quantities import normalizeDatetime, parseDatetime

SECONDS_PER_HOUR = 3600

class SimulationClock:
    
    # Inicializate clock
    def __init__(self, current_time):
        self._current_time = self._validate(current_time)

    # -------------------------------------------------------------------------
    # Validates and normalizes the dates and times used by the simulation clock.
    # --------------------------------------------------------------------------

    @staticmethod
    def _validate(value):
        """Accept a datetime or an ISO 8601 string and return a normalized datetime."""
        if isinstance(value, datetime):
            return normalizeDatetime(value)
        if isinstance(value, str):
            return parseDatetime(value)
        raise TypeError(
            "SimulationClock requires a datetime or an ISO 8601 string, "
            f"not {type(value).__name__}"
        )

    @staticmethod
    def _validate_hours(hours):
        """Validate a duration expressed in hours."""
        if isinstance(hours, bool) or not isinstance(hours, (int, float)):
            raise TypeError("Hours must be a number")
        if not math.isfinite(hours):
            raise ValueError("Hours must be a finite number")
        if hours <= 0:
            raise ValueError("Hours must be greater than zero")
        return float(hours)

    # ------------------------------------------------------------------
    # Reading the current instant
    # ------------------------------------------------------------------

    def getCurrentTime(self):
        return self._current_time

    # Expose the current instant without allowing direct reassignment
    @property
    def current_time(self):
        return self._current_time

    # Compare clocks by their normalized simulation instant
    def __eq__(self, other):
        if not isinstance(other, SimulationClock):
            return NotImplemented
        return self._current_time == other._current_time

    def getCurrentTimeText(self):
        return self._toText(self._current_time)
    
    # Format an instant the way the specification shows it in JSON
    @staticmethod
    def _toText(moment):
        return moment.replace(tzinfo=None).isoformat() + "Z"

    # ------------------------------------------------------------------
    
    # Restore the clock from a persisted scenario
    def setCurrentTime(self, time):
        self._current_time = self._validate(time)
        return self._current_time

    # ------------------------------------------------------------------
    # Advancing the clock (the user action)
    # ------------------------------------------------------------------

    # Advance the clock by a positive number of hours
    def advanceHours(self, hours):
        hours = self._validate_hours(hours)
        target = self._current_time + timedelta(hours=hours)
        return self.advanceTo(target)

    # Advance the clock to an absolute instant strictly after the current one
    def advanceTo(self, moment):
        target = self._validate(moment)
        if target <= self._current_time:
            raise ValueError(
                "The simulation clock can only advance: "
                f"{self._toText(target)} is not after "
                f"{self._toText(self._current_time)}"
            )
        self._current_time = target
        return self._current_time

    # ------------------------------------------------------------------
    # Queries derived from the clock
    # ------------------------------------------------------------------

    # Check if an event happened right now
    def canOccurAt(self, occurrence):
        occurrence = self._validate(occurrence)
        return occurrence <= self._current_time

    # Calculate the age of an event in seconds with respect to the simulation clock.
    def ageSeconds(self, occurrence):
        occurrence = self._validate(occurrence)
        if occurrence > self._current_time:
            raise ValueError(
                "An event cannot occur after the simulation clock: "
                f"{self._toText(occurrence)} > "
                f"{self._toText(self._current_time)}"
            )
        return int((self._current_time - occurrence).total_seconds())
    
    # Calculate the age of an event in hours.
    def ageHours(self, occurrence):
        return self.ageSeconds(occurrence) / SECONDS_PER_HOUR

    # Check if an event is older than the set time T.
    def isOlderThan(self, occurrence, t_hours):
        """
        True when an event is older than the archive threshold T.

        Spec section 11: the age is measured between the simulation clock and
        the occurrence time, and it must be *strictly* greater than T hours.
        The comparison runs on integer seconds so an event sitting exactly on
        the threshold is correctly reported as not old enough.
        """
        t_hours = self._validate_hours(t_hours)
        return self.ageSeconds(occurrence) > round(t_hours * SECONDS_PER_HOUR)

    # Calculate the time difference in hours between two events, no matter which happened first.
    def hoursBetween(self, first, second):
        first = self._validate(first)
        second = self._validate(second)
        return abs((second - first).total_seconds()) / SECONDS_PER_HOUR

    # ------------------------------------------------------------------
    
    # Convert object to dictionary
    def toDict(self):
        return {"current_time": self.getCurrentTimeText()}

    # Convert dictionary to object
    @classmethod
    def fromDict(cls, data):
        if isinstance(data, dict):
            if "current_time" not in data:
                raise KeyError("clock object has no 'current_time' field")
            return cls(data["current_time"])
        return cls(data)

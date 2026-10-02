from datetime import datetime, timedelta

import math

from backend.utils.quantities import normalizeDatetime, parseDatetime

SECONDS_PER_HOUR = 3600


class SimulationClock:
    """
    Explicit simulation clock for the scenario.

    The project specification requires every instant in the system to be an
    aware UTC value with second precision, saved together with the scenario,
    and advanced by the EventEngine in real time or by an explicit user
    action. This class is the single place where that rule is enforced, so no
    other part of the backend has to repeat it.

    Two kinds of change are deliberately separated:

    - setCurrentTime() restores a state (scenario load). Any valid instant is
      accepted, because the file being read is the source of truth.
    - advanceHours() / advanceTo() model a forward clock action. They are
      monotonic: the simulation clock never travels backwards while the
      scenario runs.

    Comments in English, as required by the deliverables (spec section 18).
    """

    def __init__(self, current_time):
        # Normalizing here makes a naive or microsecond-bearing clock
        # impossible to construct, which is what broke comparisons before.
        self._current_time = self._validate(current_time)

    # ------------------------------------------------------------------
    # Ingestion helpers
    # ------------------------------------------------------------------

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

    @property
    def current_time(self):
        """Expose the current instant without allowing direct reassignment."""
        return self._current_time

    def __eq__(self, other):
        """Compare clocks by their normalized simulation instant."""
        if not isinstance(other, SimulationClock):
            return NotImplemented
        return self._current_time == other._current_time

    def getCurrentTimeText(self):
        return self._toText(self._current_time)

    @staticmethod
    def _toText(moment):
        """Format an instant the way the specification shows it in JSON."""
        return moment.replace(tzinfo=None).isoformat() + "Z"

    # ------------------------------------------------------------------
    # Restoring a saved state
    # ------------------------------------------------------------------

    def setCurrentTime(self, time):
        """
        Restore the clock from a persisted scenario.

        No monotonicity check: loading a file must reproduce exactly what was
        saved. Monotonicity is enforced by advanceHours()/advanceTo().
        """
        self._current_time = self._validate(time)
        return self._current_time

    # ------------------------------------------------------------------
    # Advancing the clock (the user action)
    # ------------------------------------------------------------------

    def advanceHours(self, hours):
        """
        Advance the clock by a positive number of hours.

        This is the explicit duration-based clock action. It returns the new
        instant and never moves the clock backwards.
        """
        hours = self._validate_hours(hours)
        target = self._current_time + timedelta(hours=hours)
        return self.advanceTo(target)

    def advanceTo(self, moment):
        """
        Advance the clock to an absolute instant strictly after the current one.

        Raises ValueError if the target is not in the future, so a scenario can
        never silently rewind simulated time.
        """
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

    def canOccurAt(self, occurrence):
        """
        True when an event may have occurred at the given instant.

        Spec section 3: occurrence times cannot be later than the clock.
        Callers use this to reject a creation, a correction or a report before
        any structure is modified.
        """
        occurrence = self._validate(occurrence)
        return occurrence <= self._current_time

    def ageSeconds(self, occurrence):
        """
        Age of an occurrence in whole seconds.

        Integer seconds are the reference unit on purpose: comparing floats at
        the T boundary is fragile, so the boundary test in isOlderThan() runs
        on integers. Raises ValueError when the occurrence is after the clock,
        because that already violates section 3 and must not be hidden.
        """
        occurrence = self._validate(occurrence)
        if occurrence > self._current_time:
            raise ValueError(
                "An event cannot occur after the simulation clock: "
                f"{self._toText(occurrence)} > "
                f"{self._toText(self._current_time)}"
            )
        return int((self._current_time - occurrence).total_seconds())

    def ageHours(self, occurrence):
        """Age of an occurrence in hours. Float, for reporting only."""
        return self.ageSeconds(occurrence) / SECONDS_PER_HOUR

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

    def hoursBetween(self, first, second):
        """
        Absolute difference in hours between two instants.

        Spec section 8 needs "the time difference is at most W hours" between
        two events without caring which one happened first, so this is
        unsigned and order independent.
        """
        first = self._validate(first)
        second = self._validate(second)
        return abs((second - first).total_seconds()) / SECONDS_PER_HOUR


    def toDict(self):
        """Serialize the clock; round-trips exactly through fromDict()."""
        return {"current_time": self.getCurrentTimeText()}

    @classmethod
    def fromDict(cls, data):
        """
        Rebuild the clock from JSON.

        Accepts the documented object form {"current_time": "..."} and also a
        bare ISO 8601 string, because hand-written scenario files (required by
        spec section 13) naturally use the short form.
        """
        if isinstance(data, dict):
            if "current_time" not in data:
                raise KeyError("clock object has no 'current_time' field")
            return cls(data["current_time"])
        return cls(data)

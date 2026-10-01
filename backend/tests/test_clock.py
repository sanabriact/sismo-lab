"""
Test suite for the simulation clock (spec sections 3, 8, 11).

Runs with plain python (no pytest needed) and is also collectable by pytest,
because every check is a test_* function built only from asserts.

    python3 backend/tests/test_clock.py

Sections covered:
    3  explicit clock, saved with the scenario, UTC with second precision,
       occurrence never after the clock, advanced by user action, determines age
    8  time difference bounded by W hours
    11 age strictly greater than T hours
"""

import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
)

from backend.models.clock import SECONDS_PER_HOUR, SimulationClock
from backend.models.seismic_observatory import SeismicObservatory

# Reference instants used across the suite.
T0 = datetime(2026, 9, 7, 10, 0, 0, tzinfo=timezone.utc)
T0_TEXT = "2026-09-07T10:00:00Z"


def clockAt(text=T0_TEXT):
    return SimulationClock(text)


def at(hoursAfterT0):
    return T0 + timedelta(hours=hoursAfterT0)


# =====================================================================
# Group 1 - the state invariant: always aware UTC, second precision
# =====================================================================

def test_constructor_normalizes_naive_datetime_to_utc():
    clock = SimulationClock(datetime(2026, 9, 7, 10, 0, 0))
    assert clock.getCurrentTime().tzinfo is timezone.utc
    assert clock.getCurrentTime() == T0


def test_constructor_converts_other_offsets_to_utc():
    # 10:00 at -05:00 is 15:00 UTC
    clock = SimulationClock(datetime(2026, 9, 7, 10, 0, 0, tzinfo=timezone(timedelta(hours=-5))))
    assert clock.getCurrentTime() == datetime(2026, 9, 7, 15, 0, 0, tzinfo=timezone.utc)
    assert clock.getCurrentTimeText() == "2026-09-07T15:00:00Z"


def test_constructor_strips_microseconds():
    # Spec section 3 asks for second precision.
    clock = SimulationClock(datetime(2026, 9, 7, 10, 0, 0, 670590, tzinfo=timezone.utc))
    assert clock.getCurrentTime().microsecond == 0
    assert clock.getCurrentTime() == T0


def test_constructor_accepts_iso_with_trailing_z():
    assert SimulationClock("2026-09-07T10:00:00Z") == clockAt()


def test_constructor_accepts_iso_with_explicit_offset():
    assert SimulationClock("2026-09-07T10:00:00+00:00") == clockAt()


def test_constructor_rejects_unsupported_types():
    for bad in (123, None, [], {}, 4.5):
        try:
            SimulationClock(bad)
        except TypeError:
            continue
        raise AssertionError(f"SimulationClock accepted {bad!r}")


def test_current_time_attribute_is_read_only():
    # The AI clients read clock.current_time; nobody may assign a raw datetime.
    clock = clockAt()
    try:
        clock.current_time = datetime(2020, 1, 1)
    except AttributeError:
        return
    raise AssertionError("current_time should not be writable")


def test_setCurrentTime_normalizes_instead_of_storing_raw():
    clock = clockAt()
    clock.setCurrentTime(datetime(2026, 9, 8, 10, 0, 0, 500000))  # naive + microseconds
    assert clock.getCurrentTime() == datetime(2026, 9, 8, 10, 0, 0, tzinfo=timezone.utc)


def test_setCurrentTime_may_rewind_because_it_restores_a_saved_state():
    # Monotonicity is not enforced on the load path on purpose.
    clock = clockAt()
    clock.setCurrentTime("2020-01-01T00:00:00Z")
    assert clock.getCurrentTimeText() == "2020-01-01T00:00:00Z"


def test_fromDict_accepts_the_object_form():
    assert SimulationClock.fromDict({"current_time": T0_TEXT}) == clockAt()


def test_fromDict_accepts_a_bare_iso_string():
    # Hand-written scenario files (spec section 13) use the short form.
    assert SimulationClock.fromDict(T0_TEXT) == clockAt()


def test_fromDict_rejects_an_object_without_current_time():
    try:
        SimulationClock.fromDict({"hour": 10})
    except KeyError:
        return
    raise AssertionError("a clock object without 'current_time' should raise KeyError")


def test_serialization_round_trip_is_exact():
    original = SimulationClock("2026-01-02T03:04:05Z")
    restored = SimulationClock.fromDict(original.toDict())
    assert restored == original
    assert restored.getCurrentTimeText() == original.getCurrentTimeText()


def test_toDict_uses_the_z_form_shown_in_the_specification():
    assert clockAt().toDict() == {"current_time": T0_TEXT}


# =====================================================================
# Group 2 - advancing the clock is monotonic
# =====================================================================

def test_advanceHours_moves_the_clock_forward():
    clock = clockAt()
    clock.advanceHours(48)
    assert clock.getCurrentTime() == at(48)


def test_advanceTo_accepts_a_later_instant():
    clock = clockAt()
    clock.advanceTo("2026-09-09T10:00:00Z")
    assert clock.getCurrentTimeText() == "2026-09-09T10:00:00Z"


def test_advanceTo_refuses_to_rewind():
    clock = clockAt()
    try:
        clock.advanceTo("2026-09-07T09:00:00Z")
    except ValueError:
        return
    raise AssertionError("the clock must never travel backwards")


def test_advanceTo_refuses_the_same_instant():
    clock = clockAt()
    try:
        clock.advanceTo(T0)
    except ValueError:
        return
    raise AssertionError("advancing to the current instant is not an advance")


def test_advanceHours_refuses_non_positive_durations():
    for bad in (0, -1, -0.5):
        try:
            clockAt().advanceHours(bad)
        except ValueError:
            continue
        raise AssertionError(f"advanceHours accepted {bad}")


def test_advanceHours_refuses_non_finite_durations():
    for bad in (float("inf"), float("nan")):
        try:
            clockAt().advanceHours(bad)
        except ValueError:
            continue
        raise AssertionError(f"advanceHours accepted {bad}")


def test_advanceHours_refuses_non_numeric_durations():
    for bad in ("24", None, True, [24]):
        try:
            clockAt().advanceHours(bad)
        except TypeError:
            continue
        raise AssertionError(f"advanceHours accepted {bad!r}")


def test_repeated_advances_accumulate():
    clock = clockAt()
    for _ in range(3):
        clock.advanceHours(24)
    assert clock.getCurrentTime() == at(72)


# =====================================================================
# Section 3 - an occurrence may never be after the clock
# =====================================================================

def test_canOccurAt_accepts_the_clock_instant_itself():
    # The boundary is inclusive.
    assert clockAt().canOccurAt(T0) is True


def test_canOccurAt_accepts_the_past():
    assert clockAt().canOccurAt(at(-24)) is True


def test_canOccurAt_rejects_the_future():
    assert clockAt().canOccurAt(at(1)) is False


def test_canOccurAt_treats_a_naive_occurrence_as_utc():
    # Events are always aware; a naive input must not crash the comparison.
    assert clockAt().canOccurAt(datetime(2026, 9, 7, 9, 0, 0)) is True


def test_advancing_the_clock_makes_older_events_still_valid():
    clock = clockAt()
    occurrence = at(-1)
    assert clock.canOccurAt(occurrence) is True
    clock.advanceHours(100)
    assert clock.canOccurAt(occurrence) is True
    assert clock.ageHours(occurrence) == 101


# =====================================================================
# Section 11 - age and the strictly-greater-than T threshold
# =====================================================================

def test_age_is_measured_from_the_occurrence_to_the_clock():
    clock = clockAt()
    assert clock.ageHours(at(-72)) == 72
    assert clock.ageSeconds(at(-72)) == 72 * SECONDS_PER_HOUR


def test_age_is_zero_for_an_event_at_the_current_instant():
    assert clockAt().ageSeconds(T0) == 0


def test_age_refuses_an_occurrence_after_the_clock():
    # That already violates section 3 and must be surfaced, not clamped.
    try:
        clockAt().ageHours(at(1))
    except ValueError:
        return
    raise AssertionError("age should refuse a future occurrence")


def test_isOlderThan_uses_a_strict_comparison_at_the_boundary():
    # Spec section 11: "antigüedad estrictamente mayor que T horas".
    clock = clockAt()
    assert clock.isOlderThan(at(-72), 72) is False, "exactly T hours is not older than T"


def test_isOlderThan_accepts_one_second_past_the_boundary():
    clock = clockAt()
    occurrence = T0 - timedelta(hours=72, seconds=1)
    assert clock.isOlderThan(occurrence, 72) is True


def test_isOlderThan_rejects_one_second_short_of_the_boundary():
    clock = clockAt()
    occurrence = T0 - timedelta(hours=72) + timedelta(seconds=1)
    assert clock.isOlderThan(occurrence, 72) is False


def test_isOlderThan_handles_fractional_thresholds_exactly():
    clock = clockAt()
    assert clock.isOlderThan(at(-1.5), 1.5) is False
    assert clock.isOlderThan(T0 - timedelta(hours=1, minutes=30, seconds=1), 1.5) is True


def test_isOlderThan_refuses_a_non_positive_threshold():
    for bad in (0, -72):
        try:
            clockAt().isOlderThan(at(-100), bad)
        except ValueError:
            continue
        raise AssertionError(f"isOlderThan accepted T={bad}; spec says T is positive")


def test_advancing_the_clock_turns_a_fresh_event_into_an_old_one():
    # This is the mechanism behind mass archiving (spec section 11).
    clock = clockAt()
    occurrence = T0 - timedelta(hours=10)
    assert clock.isOlderThan(occurrence, 72) is False
    clock.advanceHours(72)
    assert clock.isOlderThan(occurrence, 72) is True


# =====================================================================
# Section 8 - the time difference bounded by W hours
# =====================================================================

def test_hoursBetween_is_independent_of_argument_order():
    clock = clockAt()
    assert clock.hoursBetween(at(0), at(-5)) == 5
    assert clock.hoursBetween(at(-5), at(0)) == 5


def test_hoursBetween_matches_the_late_report_case_of_spec_section_17():
    # Events at 10:00, 10:20 and 09:55 must all fall inside W = 48 hours.
    clock = clockAt()
    t1000 = at(0)
    t1020 = t1000 + timedelta(minutes=20)
    t0955 = t1000 - timedelta(minutes=5)
    w = 48
    for other in (t1020, t0955):
        assert clock.hoursBetween(t1000, other) <= w


def test_hoursBetween_is_zero_for_the_same_instant():
    clock = clockAt()
    assert clock.hoursBetween(T0, T0_TEXT) == 0


# =====================================================================
# Reproducibility - the defect this clock was rewritten to fix
# =====================================================================

def test_two_clocks_declaring_the_same_instant_are_equal():
    # Before the rewrite the default clock carried microseconds, so the same
    # declared instant produced different ages depending on how it was built.
    withMicros = SimulationClock(datetime(2026, 9, 7, 10, 0, 0, 670590, tzinfo=timezone.utc))
    fromText = SimulationClock(T0_TEXT)
    assert withMicros == fromText
    assert withMicros.ageHours(at(-24)) == fromText.ageHours(at(-24)) == 24


def test_default_observatory_clock_has_second_precision():
    observatory = SeismicObservatory()
    assert observatory.getClock().getCurrentTime().microsecond == 0
    assert observatory.getClock().getCurrentTime().tzinfo is timezone.utc


def test_clock_survives_a_full_observatory_round_trip():
    observatory = SeismicObservatory()
    observatory.getClock().setCurrentTime("2026-09-07T10:00:00Z")
    restored = SeismicObservatory.fromDict(observatory.toDict())
    assert restored.getClock() == observatory.getClock()
    assert restored.getClock().getCurrentTimeText() == T0_TEXT


# =====================================================================
# Runner
# =====================================================================

def main():
    tests = [
        (name, obj)
        for name, obj in sorted(globals().items())
        if name.startswith("test_") and callable(obj)
    ]
    passed, failed = 0, []
    for name, test in tests:
        try:
            test()
            passed += 1
            print(f"  PASS  {name}")
        except AssertionError as error:
            failed.append((name, error))
            print(f"  FAIL  {name}: {error}")
        except Exception as error:  # noqa: BLE001
            failed.append((name, error))
            print(f"  ERROR {name}: {type(error).__name__}: {error}")

    print()
    print(f"  {passed}/{len(tests)} pruebas pasaron")
    if failed:
        print(f"  {len(failed)} fallo(s):")
        for name, error in failed:
            print(f"    - {name}: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
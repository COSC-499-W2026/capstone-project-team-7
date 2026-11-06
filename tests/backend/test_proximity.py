from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from proximity import LocationReading, ProximityTarget, check_proximity, distance_metres

NOW = datetime(2026, 10, 23, tzinfo=timezone.utc)
TARGET = ProximityTarget(latitude=49.94, longitude=-119.4, radius_metres=50)


@pytest.mark.parametrize("changes, result", [
    ({}, "within_radius"),
    ({"latitude": 49.95}, "outside_radius"),
    ({"accuracy": 51}, "inaccurate_location"),
    ({"captured_at": NOW - timedelta(seconds=31)}, "stale_location"),
    ({"captured_at": NOW + timedelta(seconds=6)}, "stale_location"),
    ({"captured_at": NOW - timedelta(seconds=30)}, "within_radius"),
    ({"accuracy": 50}, "within_radius"),
])
def test_proximity(changes, result):
    values = dict(latitude=49.94, longitude=-119.4, accuracy=10, captured_at=NOW)
    reading = LocationReading(**(values | changes))
    assert check_proximity(reading, TARGET, now=NOW) == result


@pytest.mark.parametrize("changes", [
    {"latitude": 91}, {"longitude": -181}, {"latitude": float("nan")},
    {"accuracy": float("inf")}, {"accuracy": 0}, {"accuracy": -1},
    {"captured_at": "2026-10-23T00:00:00"}, {"radius_metres": 1000},
])
def test_invalid_reading(changes):
    with pytest.raises(ValidationError):
        LocationReading(**(dict(latitude=0, longitude=0, accuracy=10, captured_at=NOW) | changes))


@pytest.mark.parametrize("radius", [0, -1, float("inf"), float("nan")])
def test_invalid_target(radius):
    with pytest.raises(ValidationError):
        ProximityTarget(latitude=0, longitude=0, radius_metres=radius)


def test_distance_and_exact_boundary():
    reading = LocationReading(latitude=0, longitude=0, accuracy=1, captured_at=NOW)
    target = ProximityTarget(latitude=0, longitude=1, radius_metres=120000)
    distance = distance_metres(reading, target)
    assert distance == pytest.approx(111195.08, abs=0.1)
    assert distance_metres(reading, reading) == 0
    target.radius_metres = distance
    assert check_proximity(reading, target, now=NOW) == "within_radius"
    target.radius_metres = distance - 0.01
    assert check_proximity(reading, target, now=NOW) == "outside_radius"

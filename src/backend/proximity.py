"""GPS validation for future answer handlers; targets must come from the server."""

from datetime import datetime, timezone
from math import asin, cos, radians, sin, sqrt

from pydantic import BaseModel, ConfigDict, Field, AwareDatetime


class Coordinates(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class LocationReading(Coordinates):
    accuracy: float = Field(gt=0, description="Reported horizontal accuracy in metres")
    captured_at: AwareDatetime = Field(description="Device time when the position was measured")


class ProximityTarget(Coordinates):
    radius_metres: float = Field(gt=0, description="Server-configured arrival radius in metres")


def distance_metres(first: Coordinates, second: Coordinates) -> float:
    """Great-circle distance using the mean Earth radius."""
    lat1, lat2 = radians(first.latitude), radians(second.latitude)
    dlat = lat2 - lat1
    dlon = radians(second.longitude - first.longitude)
    haversine = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 6371008.8 * 2 * asin(sqrt(min(1.0, max(0.0, haversine))))


def check_proximity(
    reading: LocationReading, target: ProximityTarget, *, now: datetime | None = None,
) -> str:
    """Return a result without exposing the target or accepting uncertain fixes."""
    age = ((now or datetime.now(timezone.utc)) - reading.captured_at).total_seconds()
    if age < -5 or age > 30:
        return "stale_location"
    if reading.accuracy > target.radius_metres:
        return "inaccurate_location"
    if distance_metres(reading, target) > target.radius_metres:
        return "outside_radius"
    return "within_radius"

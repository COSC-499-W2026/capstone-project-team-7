"""Validate submitted GPS readings against the current server-owned target."""

from fastapi import HTTPException
from pydantic import ValidationError

from proximity import LocationReading, ProximityTarget, check_proximity


def validate_answer_location(reading: LocationReading, location):
    try:
        target = ProximityTarget(**{key: location[key] for key in
                                    ("latitude", "longitude", "radius_metres")})
    except ValidationError:
        raise HTTPException(status_code=503, detail="Location verification is unavailable for this spot.") from None
    result = check_proximity(reading, target)
    messages = {
        "stale_location": "Your location reading has expired. Please refresh your location.",
        "inaccurate_location": "Your location is not accurate enough. Please try again.",
        "outside_radius": "You are too far from this spot. Move closer and try again.",
    }
    if result != "within_radius":
        raise HTTPException(status_code=422, detail=messages[result])

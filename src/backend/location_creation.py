"""Teachers add a location, with a clue in their class's language, to the pool every class in that language uses."""

from typing import Annotated
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from auth import require_teacher
from database import get_connection
from schemas import RequiredText
from teacher_access import database_unavailable, owned_class
from utils.ocr import ROOM_NUMBER

router = APIRouter(prefix="/api/teacher/classes", tags=["teacher"])

ARRIVAL_RADIUS_METRES = 50
UpperText = Annotated[str, StringConstraints(strip_whitespace=True, to_upper=True, min_length=1, max_length=10)]


class NewLocation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    building: Annotated[UpperText, Field(description="Building code, e.g. COM")]
    room_number: Annotated[UpperText, Field(description="Room number, e.g. 316")]
    number_text: Annotated[RequiredText, Field(description="The room number as spoken in the class's language")]
    description_text: Annotated[RequiredText, Field(description="A description of the room in the class's language")]
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)

    @model_validator(mode="after")
    def check_room(self):
        # The photo step can only confirm rooms its OCR pattern reads.
        if not ROOM_NUMBER.fullmatch(f"{self.building} {self.room_number}"):
            raise ValueError("Use a campus building code and room number, like COM 316")
        return self


def save_location(connection, info, teacher_id):
    """The new location, or the existing one with the same building and room."""
    location = connection.execute(
        """INSERT INTO locations (building, room_number, latitude, longitude, radius_metres, created_by)
        VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (building, room_number) DO NOTHING
        RETURNING id, building, room_number, latitude, longitude, radius_metres""",
        (info.building, info.room_number, info.latitude, info.longitude, ARRIVAL_RADIUS_METRES, teacher_id),
    ).fetchone()
    return location or connection.execute(
        """SELECT id, building, room_number, latitude, longitude, radius_metres FROM locations
        WHERE building = %s AND room_number = %s""",
        (info.building, info.room_number),
    ).fetchone()


@router.post("/{class_id}/locations", status_code=201,
             summary="Add a location with a clue in your class's language; an existing room gets the new clue")
def add_location(class_id: UUID, info: NewLocation, user=Depends(require_teacher)):
    try:
        with get_connection() as connection:
            classroom = owned_class(connection, class_id, user["id"])
            if not classroom:
                raise HTTPException(status_code=404, detail="Class not found")
            location = save_location(connection, info, user["id"])
            connection.execute(
                """INSERT INTO location_clues (location_id, language_code, number_text, description_text, base_game)
                VALUES (%s, %s, %s, %s, FALSE)""",
                (location["id"], classroom["language_code"], info.number_text, info.description_text),
            )
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="This room already has a clue in this language") from None
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
    return location

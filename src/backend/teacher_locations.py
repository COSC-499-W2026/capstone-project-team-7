"""Teachers view the locations in their class's language and upload clue audio for them."""

import logging
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Request

from database import get_connection
from teacher_access import database_unavailable, owned_class, require_teacher, teacher_connection
from utils.audio_storage import audio_path, is_mp3, save_audio
from utils.request_body import read_limited_body

router = APIRouter(prefix="/api/teacher/classes", tags=["teacher"])

MAX_AUDIO_BYTES = 5 * 1024 * 1024
NOT_AN_MP3 = "Please upload an MP3 file"


def location_summary(location, language_code):
    return {**location, "has_audio": audio_path(language_code, location).is_file()}


def class_language(connection, class_id, teacher_id):
    classroom = owned_class(connection, class_id, teacher_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Class not found")
    return classroom["language_code"]


@router.get("/{class_id}/locations", summary="List the locations with a clue in the class's language")
def list_locations(class_id: UUID, access=Depends(teacher_connection)):
    connection, teacher_id = access
    language_code = class_language(connection, class_id, teacher_id)
    locations = connection.execute(
        """SELECT locations.id, locations.building, locations.room_number FROM locations
        JOIN location_clues ON location_clues.location_id = locations.id
        WHERE location_clues.language_code = %s
        ORDER BY locations.building, locations.room_number""",
        (language_code,),
    ).fetchall()
    return [location_summary(location, language_code) for location in locations]


async def read_audio(request: Request):
    """The MP3 sent as the request body (audio/mpeg)."""
    return await read_limited_body(request, MAX_AUDIO_BYTES, "Audio file is too large", NOT_AN_MP3)


def class_location(class_id, location_id, teacher_id):
    """The location and language, using a short connection so saving a file doesn't hold one open."""
    try:
        with get_connection() as connection:
            language_code = class_language(connection, class_id, teacher_id)
            location = connection.execute(
                """SELECT locations.id, locations.building, locations.room_number FROM locations
                JOIN location_clues ON location_clues.location_id = locations.id
                WHERE locations.id = %s AND location_clues.language_code = %s""",
                (location_id, language_code),
            ).fetchone()
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location, language_code


@router.put("/{class_id}/locations/{location_id}/audio", summary="Add or replace a location's clue audio")
def upload_audio(class_id: UUID, location_id: UUID, user=Depends(require_teacher), audio=Depends(read_audio)):
    location, language_code = class_location(class_id, location_id, user["id"])
    if not is_mp3(audio):
        raise HTTPException(status_code=422, detail=NOT_AN_MP3)
    try:
        save_audio(language_code, location, audio)
    except OSError:
        logging.getLogger(__name__).warning("Saving clue audio failed")
        raise HTTPException(status_code=503, detail="Could not save the audio, please try again") from None
    return location_summary(location, language_code)

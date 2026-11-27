"""Teachers add, list, play and retire their own extra clips; other teachers never see them."""

import logging
from typing import Annotated
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

from database import get_connection
from difficulties import Difficulty
from schemas import RequiredText
from teacher_access import database_unavailable, require_teacher, teacher_connection
from teacher_locations import NOT_AN_MP3, class_language, class_location, read_audio
from utils.audio_storage import clip_path, is_mp3, save_clip

router = APIRouter(prefix="/api/teacher/classes", tags=["teacher"])

CLIP_NOT_FOUND = "Clip not found"


class NewClip(BaseModel):
    model_config = ConfigDict(extra="forbid")
    difficulty: Difficulty = Field(description="Which level the clip is for")
    label: Annotated[RequiredText, Field(max_length=60, description="Short name only you see, e.g. 'Café clue'")]
    description: Annotated[RequiredText | None, Field(max_length=300, description="Optional note only you see")] = None


def own_clips(connection, teacher_id, language_code, difficulty=None, clip_id=None):
    """The teacher's clips that aren't retired, newest first, optionally one level or one clip."""
    return connection.execute(
        """SELECT clip.id, clip.location_id, locations.building, locations.room_number, clip.difficulty,
            clip.label, clip.description, clip.created_at
        FROM location_clips AS clip JOIN locations ON locations.id = clip.location_id
        WHERE clip.created_by = %(teacher)s AND clip.language_code = %(language)s AND clip.retired_at IS NULL
            AND (%(difficulty)s::text IS NULL OR clip.difficulty = %(difficulty)s)
            AND (%(clip)s::uuid IS NULL OR clip.id = %(clip)s)
        ORDER BY clip.created_at DESC, clip.id""",
        {"teacher": teacher_id, "language": language_code,
         "difficulty": difficulty.value if difficulty else None, "clip": clip_id},
    ).fetchall()


def own_clip(connection, class_id, clip_id, teacher_id):
    """One of the teacher's clips in the class's language; 404 also hides other teachers' clips."""
    language_code = class_language(connection, class_id, teacher_id)
    clips = own_clips(connection, teacher_id, language_code, clip_id=clip_id)
    if not clips:
        raise HTTPException(status_code=404, detail=CLIP_NOT_FOUND)
    return language_code, clips[0]


def insert_clip(location, language_code, clip, teacher_id):
    try:
        with get_connection() as connection:
            clip_id = connection.execute(
                """INSERT INTO location_clips (location_id, language_code, difficulty, label, description, created_by)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                (location["id"], language_code, clip.difficulty.value, clip.label, clip.description, teacher_id),
            ).fetchone()["id"]
            return own_clips(connection, teacher_id, language_code, clip_id=clip_id)[0]
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None


def remove_clip_row(clip_id):
    """Undo the insert when the file can't be saved, so no clip is listed without audio."""
    try:
        with get_connection() as connection:
            connection.execute("DELETE FROM location_clips WHERE id = %s", (clip_id,))
    except (psycopg.Error, RuntimeError):
        logging.getLogger(__name__).warning("Removing a clip whose file failed to save also failed")


@router.post("/{class_id}/locations/{location_id}/clips", status_code=201,
             summary="Add your own extra clip for a location; only you see it")
def add_clip(class_id: UUID, location_id: UUID, clip: Annotated[NewClip, Query()],
             user=Depends(require_teacher), audio=Depends(read_audio)):
    location, language_code = class_location(class_id, location_id, user["id"])
    if not is_mp3(audio):
        raise HTTPException(status_code=422, detail=NOT_AN_MP3)
    saved = insert_clip(location, language_code, clip, user["id"])
    try:
        save_clip(language_code, saved["id"], audio)
    except OSError:
        remove_clip_row(saved["id"])
        logging.getLogger(__name__).warning("Saving a teacher clip failed")
        raise HTTPException(status_code=503, detail="Could not save the audio, please try again") from None
    return saved


@router.get("/{class_id}/clips", summary="List your own clips in the class's language, newest first")
def list_clips(class_id: UUID,
               difficulty: Annotated[Difficulty | None, Query(description="Only clips for this level")] = None,
               access=Depends(teacher_connection)):
    connection, teacher_id = access
    language_code = class_language(connection, class_id, teacher_id)
    return own_clips(connection, teacher_id, language_code, difficulty)


@router.get("/{class_id}/clips/{clip_id}/audio", summary="Play one of your own clips")
def clip_audio(class_id: UUID, clip_id: UUID, user=Depends(require_teacher)):
    try:
        with get_connection() as connection:
            language_code, clip = own_clip(connection, class_id, clip_id, user["id"])
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
    path = clip_path(language_code, clip["id"])
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Audio not found for this clip")
    return FileResponse(path, media_type="audio/mpeg")


@router.delete("/{class_id}/clips/{clip_id}", status_code=204,
               summary="Retire one of your own clips; hunts that chose it play the default clip")
def retire_clip(class_id: UUID, clip_id: UUID, user=Depends(require_teacher)):
    try:
        with get_connection() as connection:
            own_clip(connection, class_id, clip_id, user["id"])
            connection.execute("UPDATE location_clips SET retired_at = now() WHERE id = %s", (clip_id,))
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
    return Response(status_code=204)

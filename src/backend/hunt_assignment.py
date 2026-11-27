"""Teachers assign a hunt to a class they own."""

from datetime import date
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator

from database import get_connection
from difficulties import Difficulty
from teacher_access import database_unavailable, owned_class, require_teacher, teacher_connection
from teacher_clips import own_clips

router = APIRouter(prefix="/api/teacher/classes", tags=["teacher"])


class HuntClipChoice(BaseModel):
    model_config = ConfigDict(extra="forbid")
    location_id: UUID = Field(description="The room that plays the clip")
    clip_id: UUID = Field(description="One of your own clips for that room and the hunt's difficulty")


class HuntAssignmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    difficulty: Difficulty
    due_date: date | None = None
    clips: list[HuntClipChoice] = Field(
        default=[], max_length=20, description="Rooms that play one of your clips; other rooms play the default")

    @field_validator("clips")
    @classmethod
    def one_clip_per_room(cls, value):
        if len({choice.location_id for choice in value}) < len(value):
            raise ValueError("Choose only one clip per room")
        return value

    @field_validator("due_date")
    @classmethod
    def not_in_past(cls, value):
        if value is not None and value < date.today():
            raise ValueError("Due date cannot be in the past")
        return value


def check_clip_choices(connection, choices, teacher_id, language_code, difficulty):
    """422 unless every choice is the teacher's own live clip for that room, language and difficulty."""
    clips = own_clips(connection, teacher_id, language_code, difficulty)
    usable = {(clip["id"], clip["location_id"]) for clip in clips}
    for choice in choices:
        if (choice.clip_id, choice.location_id) not in usable:
            room = connection.execute(
                "SELECT building, room_number FROM locations WHERE id = %s", (choice.location_id,),
            ).fetchone()
            where = f" for {room['building']} {room['room_number']}" if room else ""
            raise HTTPException(status_code=422, detail=f"Your clip{where} can't be used in this hunt")


def save_clip_choices(connection, hunt_id, choices):
    for choice in choices:
        connection.execute(
            "INSERT INTO hunt_clips (hunt_id, location_id, clip_id) VALUES (%s, %s, %s)",
            (hunt_id, choice.location_id, choice.clip_id),
        )


def hunt_clips(connection, hunt_ids, teacher_id):
    """Each hunt's live clips that the teacher owns, by hunt id; after a class is reassigned,
    the previous teacher's clips still play but aren't shown."""
    rows = connection.execute(
        """SELECT choice.hunt_id, choice.location_id, locations.building, locations.room_number,
            choice.clip_id, clip.label
        FROM hunt_clips AS choice
        JOIN location_clips AS clip ON clip.id = choice.clip_id
        JOIN locations ON locations.id = choice.location_id
        WHERE choice.hunt_id = ANY(%s) AND clip.retired_at IS NULL AND clip.created_by = %s
        ORDER BY locations.building, locations.room_number""", (hunt_ids, teacher_id),
    ).fetchall()
    clips = {hunt_id: [] for hunt_id in hunt_ids}
    for row in rows:
        clips[row.pop("hunt_id")].append(row)
    return clips


@router.post("/{class_id}/hunts", status_code=201, summary="Assign a hunt to a class; it uses the class's language")
def assign_hunt(class_id: UUID, info: HuntAssignmentRequest, user=Depends(require_teacher)):
    try:
        with get_connection() as connection:
            classroom = connection.execute(
                "SELECT teacher_id, language_code FROM classes WHERE id = %s", (class_id,),
            ).fetchone()
            if not classroom:
                raise HTTPException(status_code=404, detail="Class not found")
            if classroom["teacher_id"] != user["id"]:
                raise HTTPException(status_code=403, detail="You can only assign hunts to your own classes")
            check_clip_choices(connection, info.clips, user["id"], classroom["language_code"], info.difficulty)
            hunt = connection.execute(
                """INSERT INTO assigned_hunts (class_id, language_code, difficulty, due_date)
                VALUES (%s, %s, %s, %s)
                RETURNING id, class_id, language_code, difficulty, due_date""",
                (class_id, classroom["language_code"], info.difficulty.value, info.due_date),
            ).fetchone()
            save_clip_choices(connection, hunt["id"], info.clips)
            return hunt
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None


@router.get("/{class_id}/hunts", summary="List the hunts assigned to a class you own, newest first")
def list_hunts(class_id: UUID, access=Depends(teacher_connection)):
    connection, teacher_id = access
    if not owned_class(connection, class_id, teacher_id):
        raise HTTPException(status_code=404, detail="Class not found")
    hunts = connection.execute(
        """SELECT id, difficulty, due_date, assigned_at FROM assigned_hunts
        WHERE class_id = %s ORDER BY assigned_at DESC, id""", (class_id,),
    ).fetchall()
    clips = hunt_clips(connection, [hunt["id"] for hunt in hunts], teacher_id)
    return [{**hunt, "clips": clips[hunt["id"]]} for hunt in hunts]


@router.delete("/{class_id}/hunts/{hunt_id}", status_code=204, summary="Delete a hunt from a class you own")
def delete_hunt(class_id: UUID, hunt_id: UUID, user=Depends(require_teacher)):
    try:
        with get_connection() as connection:
            if not owned_class(connection, class_id, user["id"]):
                raise HTTPException(status_code=404, detail="Class not found")
            deleted = connection.execute(
                "DELETE FROM assigned_hunts WHERE id = %s AND class_id = %s", (hunt_id, class_id),
            ).rowcount
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
    if not deleted:
        raise HTTPException(status_code=404, detail="Hunt not found")
    return Response(status_code=204)

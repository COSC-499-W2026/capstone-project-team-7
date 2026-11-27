"""Leaderboard of a class owned by the signed-in teacher."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from student_leaderboard import class_rankings
from teacher_access import owned_class, teacher_connection

router = APIRouter(prefix="/api/teacher/classes", tags=["teacher"])


@router.get("/{class_id}/leaderboard", summary="Read the leaderboard of a class you teach")
def leaderboard(class_id: UUID, access=Depends(teacher_connection)):
    connection, teacher_id = access
    classroom = owned_class(connection, class_id, teacher_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Class not found")
    return class_rankings(connection, class_id, classroom["language_code"])

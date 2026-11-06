"""Admin: delete a teacher account once none of their classes remain."""

from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Response

from admin import database_unavailable, require_admin
from database import get_connection

router = APIRouter(prefix="/api/admin/teachers", tags=["admin"])


@router.delete("/{teacher_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_teacher(teacher_id: UUID):
    """Delete a teacher; refused while they still have classes, since classes cascade to student enrollments."""
    try:
        with get_connection() as connection:
            # Lock the teacher so no class can be assigned to them between the check and the delete.
            teacher = connection.execute(
                "SELECT user_id FROM teachers WHERE user_id = %s FOR UPDATE", (teacher_id,),
            ).fetchone()
            if teacher is None:
                raise HTTPException(status_code=404, detail="Teacher not found")
            assigned = connection.execute(
                "SELECT count(*) AS classes FROM classes WHERE teacher_id = %s", (teacher_id,),
            ).fetchone()
            if assigned["classes"]:
                raise HTTPException(status_code=409, detail="Reassign this teacher's classes before deleting them")
            connection.execute("DELETE FROM users WHERE id = %s", (teacher_id,))
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
    return Response(status_code=204)

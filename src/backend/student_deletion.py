"""Admin: delete a student account."""

from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Response

from admin import database_unavailable, require_admin
from database import get_connection

router = APIRouter(prefix="/api/admin/students", tags=["admin"])


@router.delete("/{student_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_student(student_id: UUID):
    """Delete a student with their enrollments, languages and sessions."""
    try:
        with get_connection() as connection:
            # The role check stops this route from deleting teacher or admin accounts.
            student = connection.execute(
                "DELETE FROM users WHERE id = %s AND role = 'student' RETURNING id", (student_id,),
            ).fetchone()
            if student is None:
                raise HTTPException(status_code=404, detail="Student not found")
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
    return Response(status_code=204)

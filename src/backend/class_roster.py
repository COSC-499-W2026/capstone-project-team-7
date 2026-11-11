"""Roster of a class owned by the signed-in teacher, with removed students kept for review."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from teacher_access import owned_class, teacher_connection

router = APIRouter(prefix="/api/teacher/classes", tags=["teacher"])


@router.get("/{class_id}/students", summary="List a class's students, including those removed from it")
def list_students(class_id: UUID, access=Depends(teacher_connection)):
    connection, teacher_id = access
    if not owned_class(connection, class_id, teacher_id):
        raise HTTPException(status_code=404, detail="Class not found")
    return connection.execute(
        """SELECT users.id AS student_id, users.username, users.first_name, users.last_name,
        students.student_number, class_enrollments.status, class_enrollments.unenrolled_at
        FROM class_enrollments
        JOIN students ON students.user_id = class_enrollments.student_id
        JOIN users ON users.id = students.user_id
        WHERE class_enrollments.class_id = %s
        ORDER BY lower(users.last_name)""",
        (class_id,),
    ).fetchall()

"""Roster of students enrolled in a class owned by the signed-in teacher."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from teacher_access import owned_class, teacher_connection

router = APIRouter(prefix="/api/teacher/classes", tags=["teacher"])


@router.get("/{class_id}/students", summary="List the students enrolled in a class")
def list_students(class_id: UUID, access=Depends(teacher_connection)):
    connection, teacher_id = access
    if not owned_class(connection, class_id, teacher_id):
        raise HTTPException(status_code=404, detail="Class not found")
    return connection.execute(
        """SELECT users.id AS student_id, users.username, users.first_name, users.last_name,
        students.student_number
        FROM class_enrollments
        JOIN students ON students.user_id = class_enrollments.student_id
        JOIN users ON users.id = students.user_id
        WHERE class_enrollments.class_id = %s
        ORDER BY lower(users.last_name)""",
        (class_id,),
    ).fetchall()

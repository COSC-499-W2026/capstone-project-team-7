from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import get_connection 

router = APIRouter()


class ReassignRequest(BaseModel):
    new_teacher_id: UUID


def require_admin():
    """Placeholder: login isn't built yet, so for now this lets everyone through."""
    return True


@router.patch("/api/classes/{class_id}/teacher")
def reassign_class(class_id: UUID, body: ReassignRequest):
    require_admin()

    with get_connection() as conn:
        class_row = conn.execute(
            "SELECT id FROM classes WHERE id = %s", (class_id,)
        ).fetchone()
        if class_row is None:
            raise HTTPException(status_code=404, detail="Class not found")

        teacher_row = conn.execute(
            "SELECT user_id FROM teachers WHERE user_id = %s", (body.new_teacher_id,)
        ).fetchone()
        if teacher_row is None:
            raise HTTPException(status_code=404, detail="Teacher not found")

        conn.execute(
            "UPDATE classes SET teacher_id = %s WHERE id = %s",
            (body.new_teacher_id, class_id),
        )

    return {"class_id": str(class_id), "teacher_id": str(body.new_teacher_id)}
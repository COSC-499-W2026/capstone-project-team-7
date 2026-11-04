"""The signed-in student's profile icons: list them and equip an owned one."""

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from database import get_connection
from profile_icons import PROFILE_ICONS, equip_icon, list_icons
from student_enrollment import require_student
from teacher_access import database_unavailable

router = APIRouter(prefix="/api/student", tags=["student"])


class EquipIconRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    icon_id: str = Field(max_length=50, description="Id of an icon you own, e.g. 'croissant_cutie'")


@router.get("/icons", summary="List every profile icon, marking the ones you own and have equipped")
def icons(user=Depends(require_student)):
    try:
        with get_connection() as connection:
            return list_icons(connection, user["id"])
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None


@router.put("/profile/icon", summary="Equip a profile icon you own")
def equip(info: EquipIconRequest, user=Depends(require_student)):
    if info.icon_id not in PROFILE_ICONS:
        raise HTTPException(status_code=404, detail="Profile icon not found")
    try:
        with get_connection() as connection:
            if not equip_icon(connection, user["id"], info.icon_id):
                raise HTTPException(status_code=403, detail="You don't own this profile icon")
            return {"profile_icon": info.icon_id}
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None

"""Admin: create another admin account."""

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import ConfigDict

from admin import database_unavailable, require_admin
from database import get_connection
from teacher_signup import TeacherSignup
from utils.passwords import hash_password

router = APIRouter(prefix="/api/admin/admins", tags=["admin"])


class NewAdmin(TeacherSignup):
    """Same fields and validation as teacher signup."""

    model_config = ConfigDict(json_schema_extra={"examples": [{
        "email": "new.admin@example.com",
        "username": "newadmin",
        "password": "changeme123",
        "first_name": "Jane",
        "last_name": "Doe",
    }]})


@router.post("", status_code=201, dependencies=[Depends(require_admin)])
def create_admin(info: NewAdmin):
    """Create an admin account; the new admin logs in with the given email and password."""
    try:
        with get_connection() as connection:
            user = connection.execute(
                """INSERT INTO users (email, username, password, first_name, last_name, role)
                VALUES (%s, %s, %s, %s, %s, 'admin') RETURNING id, email, username, role""",
                (info.email, info.username, hash_password(info.password),
                 info.first_name, info.last_name),
            ).fetchone()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Email or username already in use") from None
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
    return {**user, "id": str(user["id"])}

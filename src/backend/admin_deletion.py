"""Admin account lookup and deletion."""

from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Response

from admin import database_unavailable, require_admin
from database import get_connection

router = APIRouter(prefix="/api/admin/admins", tags=["admin"])


@router.get("", summary="List other admin accounts")
def list_admins(user=Depends(require_admin)):
    try:
        with get_connection() as connection:
            return connection.execute(
                """SELECT id, email, username FROM users
                WHERE role = 'admin' AND id <> %s ORDER BY username, id""",
                (user["id"],),
            ).fetchall()
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None


def lock_admins(connection):
    # A consistent lock order serializes concurrent admin deletions.
    rows = connection.execute("SELECT id FROM users WHERE role = 'admin' ORDER BY id FOR UPDATE").fetchall()
    return {row["id"] for row in rows}


@router.delete("/{admin_id}", status_code=204, summary="Delete another admin account")
def delete_admin(admin_id: UUID, user=Depends(require_admin)):
    try:
        with get_connection() as connection:
            admin_ids = lock_admins(connection)
            if user["id"] not in admin_ids:
                raise HTTPException(status_code=401, detail="Login required")
            if admin_id not in admin_ids:
                raise HTTPException(status_code=404, detail="Admin not found")
            if len(admin_ids) == 1:
                raise HTTPException(status_code=409, detail="The last admin account cannot be deleted")
            if admin_id == user["id"]:
                raise HTTPException(status_code=409, detail="You cannot delete your own admin account")
            connection.execute("DELETE FROM users WHERE id = %s AND role = 'admin'", (admin_id,))
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
    return Response(status_code=204)

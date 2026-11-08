"""The icon store: students spend the points they earned in games on profile icons."""

import psycopg
from fastapi import APIRouter, Depends, HTTPException

from database import get_connection
from profile_icons import PROFILE_ICONS, list_icons
from student_enrollment import require_student
from teacher_access import database_unavailable

router = APIRouter(prefix="/api/student/store", tags=["student"])

# Prices in points. An icon with no price here isn't for sale.
ICON_PRICES = {"croissant_cutie": 50, "mac_the_macaron": 100, "speedy_escargot": 150}


def points_balance(connection, student_id):
    """Points earned in every game, minus points already spent on icons."""
    return connection.execute(
        """SELECT (SELECT COALESCE(SUM(points), 0) FROM game_sessions WHERE student_id = %s)
            - (SELECT COALESCE(SUM(points_spent), 0) FROM student_icons WHERE student_id = %s) AS balance""",
        (student_id, student_id),
    ).fetchone()["balance"]


@router.get("", summary="Your points balance and every icon with its price")
def store(user=Depends(require_student)):
    try:
        with get_connection() as connection:
            icons = [dict(icon, price=ICON_PRICES.get(icon["id"])) for icon in list_icons(connection, user["id"])]
            return {"balance": points_balance(connection, user["id"]), "icons": icons}
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None


@router.post("/{icon_id}/redeem", status_code=201, summary="Spend points on a profile icon (it isn't equipped)")
def redeem(icon_id: str, user=Depends(require_student)):
    price = ICON_PRICES.get(icon_id)
    if icon_id not in PROFILE_ICONS or price is None:
        raise HTTPException(status_code=404, detail="Profile icon not found")
    try:
        with get_connection() as connection:
            # Locks this student until the purchase is saved, so two quick redeems can't spend the same points.
            connection.execute("SELECT user_id FROM students WHERE user_id = %s FOR UPDATE", (user["id"],))
            owned = connection.execute(
                "SELECT 1 FROM student_icons WHERE student_id = %s AND icon_id = %s", (user["id"], icon_id),
            ).fetchone()
            if owned:
                raise HTTPException(status_code=409, detail="You already own this icon")
            balance = points_balance(connection, user["id"])
            if balance < price:
                raise HTTPException(status_code=400, detail="Not enough points")
            connection.execute(
                "INSERT INTO student_icons (student_id, icon_id, points_spent) VALUES (%s, %s, %s)",
                (user["id"], icon_id, price),
            )
            return {"icon_id": icon_id, "balance": balance - price}
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None

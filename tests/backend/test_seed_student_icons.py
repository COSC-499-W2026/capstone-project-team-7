from database import get_connection
from test_student_enrollment import enrollment_db
from utils.seed_student_icons import DEMO_ICONS, seed_student_icons


def owned_icons():
    with get_connection() as db:
        rows = db.execute("SELECT icon_id FROM student_icons ORDER BY icon_id").fetchall()
    return tuple(row["icon_id"] for row in rows)


def seed(email):
    with get_connection() as db:
        return seed_student_icons(db, email)


def test_seed_gives_the_demo_icons_and_is_safe_to_repeat(enrollment_db):
    assert seed(" Student@Example.com ") is True
    assert seed("student@example.com") is True
    assert owned_icons() == DEMO_ICONS


def test_seed_changes_nothing_for_an_unknown_student(enrollment_db):
    assert seed("nobody@example.com") is False
    assert owned_icons() == ()


def test_seed_rejects_a_teacher_email(enrollment_db):
    assert seed("teacher@example.com") is False
    assert owned_icons() == ()

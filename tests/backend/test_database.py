"""Integration checks on PostgreSQL; each test rolls back its own data."""

import os
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from psycopg.rows import dict_row

from migrate import apply_migrations


@pytest.fixture(scope="module")
def database():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run PostgreSQL integration tests")
    schema = "test_" + uuid4().hex
    with psycopg.connect(url, autocommit=True, row_factory=dict_row) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        try:
            connection.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
            apply_migrations(connection)
            yield connection
        finally:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


@pytest.fixture
def db(database):
    with database.transaction(force_rollback=True):
        yield database


def create_user(db, role="student"):
    token = uuid4().hex
    user_id = db.execute(
        """INSERT INTO users (firebase_uid, email, username, first_name, last_name, role)
           VALUES (%s, %s, %s, 'Test', 'User', %s) RETURNING id""",
        (token, token + "@example.com", token, role),
    ).fetchone()["id"]
    if role == "student":
        db.execute("INSERT INTO students (user_id, student_number) VALUES (%s, %s)", (user_id, token[:20]))
    elif role == "teacher":
        db.execute("INSERT INTO teachers (user_id) VALUES (%s)", (user_id,))
    return user_id


def create_class(db, teacher):
    return db.execute(
        "INSERT INTO classes (teacher_id, name, language_code) VALUES (%s, 'French 101', 'fr') RETURNING id",
        (teacher,),
    ).fetchone()["id"]


def create_session(db, student, class_id=None):
    return db.execute(
        """INSERT INTO game_sessions (student_id, class_id, language_code, difficulty_code,
                time_limit_seconds, max_photo_attempts, points_per_location)
           VALUES (%s, %s, 'fr', 'basic', 1800, 3, 10) RETURNING id""",
        (student, class_id),
    ).fetchone()["id"]


def create_objective(db, session, position=1):
    location = db.execute(
        """INSERT INTO locations (name, building, room_number, latitude, longitude)
           VALUES ('Test room', 'Test building', %s, 49.94, -119.4) RETURNING id""",
        (uuid4().hex,),
    ).fetchone()["id"]
    db.execute(
        """INSERT INTO location_clues (location_id, language_code, difficulty_code, clue_text, audio_url)
           VALUES (%s, 'fr', 'basic', 'Cent', 'https://example.com/audio.mp3')""", (location,),
    )
    return db.execute(
        """INSERT INTO session_locations (session_id, location_id, language_code, difficulty_code, position)
           VALUES (%s, %s, 'fr', 'basic', %s) RETURNING id""", (session, location, position),
    ).fetchone()["id"]


def complete_hunt(db, session):
    for position in range(1, 6):
        objective = create_objective(db, session, position)
        db.execute(
            """UPDATE session_locations SET status = 'completed', points_awarded = 10,
               started_at = now(), finished_at = now() WHERE id = %s""", (objective,),
        )
    db.execute("UPDATE game_sessions SET status = 'completed', ended_at = now() WHERE id = %s", (session,))


def create_icon(db, cost):
    return db.execute(
        "INSERT INTO profile_icons (name, image_url, point_cost) VALUES (%s, '/icons/test.png', %s) RETURNING id",
        (uuid4().hex, cost),
    ).fetchone()["id"]


def test_catalogs_and_migrations_are_repeatable(db):
    assert db.execute("SELECT count(*) AS n FROM languages").fetchone()["n"] == 6
    levels = db.execute("SELECT * FROM difficulty_levels ORDER BY points_per_location").fetchall()
    assert [level["max_photo_attempts"] for level in levels] == [3, 2, 1]
    assert [level["time_limit_seconds"] for level in levels] == [1800, 1200, 600]
    assert levels[0]["max_audio_replays"] is None
    assert db.execute("SELECT to_regclass('global_leaderboard') AS relation").fetchone()["relation"] is None
    assert apply_migrations(db) == []


def test_email_is_unique_case_insensitively(db):
    student = create_user(db)
    email = db.execute("SELECT email FROM users WHERE id = %s", (student,)).fetchone()["email"]
    with pytest.raises(psycopg.errors.UniqueViolation), db.transaction():
        db.execute(
            """INSERT INTO users (firebase_uid, email, username, first_name, last_name, role)
               VALUES (%s, %s, %s, 'Another', 'User', 'student')""", (uuid4().hex, email.upper(), uuid4().hex),
        )


def test_student_cannot_be_a_teacher_or_own_a_class(db):
    student = create_user(db)
    with pytest.raises(psycopg.errors.ForeignKeyViolation), db.transaction():
        db.execute("INSERT INTO teachers (user_id) VALUES (%s)", (student,))
    with pytest.raises(psycopg.errors.ForeignKeyViolation), db.transaction():
        create_class(db, student)


def test_enrollment_rejects_duplicate_and_nonstudent(db):
    student, teacher = create_user(db), create_user(db, "teacher")
    class_id = create_class(db, teacher)
    db.execute("INSERT INTO class_enrollments (class_id, student_id) VALUES (%s, %s)", (class_id, student))
    with pytest.raises(psycopg.errors.UniqueViolation), db.transaction():
        db.execute("INSERT INTO class_enrollments (class_id, student_id) VALUES (%s, %s)", (class_id, student))
    with pytest.raises(psycopg.errors.ForeignKeyViolation), db.transaction():
        db.execute("INSERT INTO class_enrollments (class_id, student_id) VALUES (%s, %s)", (class_id, teacher))


def test_class_session_requires_enrollment_and_matching_language(db):
    student = create_user(db)
    class_id = create_class(db, create_user(db, "teacher"))
    with pytest.raises(psycopg.errors.ForeignKeyViolation), db.transaction():
        create_session(db, student, class_id)
    db.execute("INSERT INTO class_enrollments (class_id, student_id) VALUES (%s, %s)", (class_id, student))
    session = create_session(db, student, class_id)
    with pytest.raises(psycopg.errors.ForeignKeyViolation), db.transaction():
        db.execute("UPDATE game_sessions SET language_code = 'de' WHERE id = %s", (session,))


def test_objectives_require_correct_clue_and_unique_location(db):
    session = create_session(db, create_user(db))
    objective = create_objective(db, session)
    with pytest.raises(psycopg.errors.UniqueViolation), db.transaction():
        db.execute(
            """INSERT INTO session_locations (session_id, location_id, language_code, difficulty_code, position)
               SELECT session_id, location_id, language_code, difficulty_code, 2
               FROM session_locations WHERE id = %s""", (objective,),
        )
    with pytest.raises(psycopg.errors.ForeignKeyViolation), db.transaction():
        db.execute("UPDATE session_locations SET language_code = 'de' WHERE id = %s", (objective,))
    with pytest.raises(psycopg.errors.CheckViolation), db.transaction():
        db.execute("UPDATE session_locations SET position = 6 WHERE id = %s", (objective,))


def test_attempt_needs_gps_and_image_to_succeed(db):
    objective = create_objective(db, create_session(db, create_user(db)))
    attempt = db.execute(
        """INSERT INTO location_attempts (session_location_id, attempt_number, image_url,
               latitude, longitude, gps_passed, image_passed)
           VALUES (%s, 1, '/photos/test.jpg', 49.94, -119.4, false, true) RETURNING id, succeeded""",
        (objective,),
    ).fetchone()
    assert attempt["succeeded"] is False
    assert db.execute(
        "UPDATE location_attempts SET gps_passed = true WHERE id = %s RETURNING succeeded", (attempt["id"],),
    ).fetchone()["succeeded"] is True
    with pytest.raises(psycopg.errors.CheckViolation), db.transaction():
        db.execute("UPDATE location_attempts SET latitude = 91 WHERE id = %s", (attempt["id"],))


def test_incomplete_hunts_do_not_contribute_to_score(db):
    student = create_user(db)
    objective = create_objective(db, create_session(db, student))
    db.execute(
        """UPDATE session_locations SET status = 'completed', points_awarded = 10,
           started_at = now(), finished_at = now() WHERE id = %s""", (objective,),
    )
    totals = db.execute("SELECT * FROM student_point_totals WHERE student_id = %s", (student,)).fetchone()
    assert totals["total_points"] == totals["available_points"] == 0


def test_redemption_and_equipping_owned_icons(db):
    student = create_user(db)
    complete_hunt(db, create_session(db, student))
    affordable, expensive = create_icon(db, 30), create_icon(db, 100)
    with pytest.raises(psycopg.errors.ForeignKeyViolation), db.transaction():
        db.execute("UPDATE students SET equipped_icon_id = %s WHERE user_id = %s", (affordable, student))
    with pytest.raises(psycopg.errors.CheckViolation), db.transaction():
        db.execute("SELECT redeem_profile_icon(%s, %s)", (student, expensive))
    db.execute("SELECT redeem_profile_icon(%s, %s)", (student, affordable))
    db.execute("UPDATE students SET equipped_icon_id = %s WHERE user_id = %s", (affordable, student))
    with pytest.raises(psycopg.errors.UniqueViolation), db.transaction():
        db.execute("SELECT redeem_profile_icon(%s, %s)", (student, affordable))
    totals = db.execute("SELECT * FROM student_point_totals WHERE student_id = %s", (student,)).fetchone()
    assert (totals["total_points"], totals["spent_points"], totals["available_points"]) == (50, 30, 20)


def test_removing_enrollment_clears_class_progress_keeps_personal_history(db):
    student = create_user(db)
    class_id = create_class(db, create_user(db, "teacher"))
    db.execute("INSERT INTO class_enrollments (class_id, student_id) VALUES (%s, %s)", (class_id, student))
    session = create_session(db, student, class_id)
    complete_hunt(db, session)
    assert db.execute("SELECT total_points FROM class_leaderboard WHERE class_id = %s", (class_id,)).fetchone()["total_points"] == 50
    db.execute("DELETE FROM class_enrollments WHERE class_id = %s AND student_id = %s", (class_id, student))
    assert db.execute("SELECT * FROM class_student_progress WHERE class_id = %s", (class_id,)).fetchall() == []
    assert db.execute("SELECT class_id FROM game_sessions WHERE id = %s", (session,)).fetchone()["class_id"] is None
    assert db.execute("SELECT total_points FROM student_point_totals WHERE student_id = %s", (student,)).fetchone()["total_points"] == 50


def test_deleting_student_cascades_history_and_equipped_icon(db):
    student = create_user(db)
    session = create_session(db, student)
    complete_hunt(db, session)
    icon = create_icon(db, 10)
    db.execute("SELECT redeem_profile_icon(%s, %s)", (student, icon))
    db.execute("UPDATE students SET equipped_icon_id = %s WHERE user_id = %s", (icon, student))
    db.execute("DELETE FROM users WHERE id = %s", (student,))
    assert db.execute("SELECT * FROM game_sessions WHERE id = %s", (session,)).fetchone() is None
    assert db.execute("SELECT * FROM student_icons WHERE student_id = %s", (student,)).fetchall() == []


def test_failed_migration_rolls_back_and_changed_migration_is_rejected(db, tmp_path):
    migration = tmp_path / "003_invalid.sql"
    migration.write_text("CREATE TABLE should_rollback (id integer); SELECT * FROM missing_table;")
    with pytest.raises(psycopg.errors.UndefinedTable):
        apply_migrations(db, tmp_path)
    assert db.execute("SELECT to_regclass('should_rollback') AS relation").fetchone()["relation"] is None
    migration.unlink()
    (tmp_path / "001_initial_schema.sql").write_text("SELECT 1;")
    with pytest.raises(RuntimeError, match="changed"):
        apply_migrations(db, tmp_path)

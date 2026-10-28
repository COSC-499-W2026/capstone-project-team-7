import os
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

from badges import award_badges
from database import get_connection
from migrate import apply_migrations


@pytest.fixture
def student(monkeypatch):
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run badge integration tests")
    schema = "badges_test_" + uuid4().hex
    with psycopg.connect(url, autocommit=True, connect_timeout=5) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        try:
            connection.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
            apply_migrations(connection)
            monkeypatch.setenv("DATABASE_URL", make_conninfo(url, options=f"-c search_path={schema}"))
            with get_connection() as db:
                student_id = db.execute("""INSERT INTO users (email, username, password, first_name, last_name, role)
                    VALUES ('student@example.com', 'student', 'hash', 'Test', 'User', 'student') RETURNING id""",
                    ).fetchone()["id"]
                db.execute("INSERT INTO students (user_id, student_number) VALUES (%s, '12345678')", (student_id,))
            yield student_id
        finally:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def add_locations(count, language):
    """Create locations that only have a clue in one language; return their ids."""
    with get_connection() as db:
        ids = []
        for _ in range(count):
            location_id = db.execute("INSERT INTO locations (building, room_number) VALUES ('EME', %s) RETURNING id",
                                     (uuid4().hex,)).fetchone()["id"]
            db.execute("""INSERT INTO location_clues (location_id, language_code, number_text, description_text)
                VALUES (%s, %s, 'cent', 'une salle')""", (location_id, language))
            ids.append(location_id)
        return ids


def play_game(student_id, language, difficulty, location_ids, found_count):
    """Save a game where the first found_count locations were found; it's finished if all were."""
    finished = found_count == len(location_ids)
    with get_connection() as db:
        game_id = db.execute("""INSERT INTO game_sessions (student_id, language_code, difficulty, finished_at)
            VALUES (%s, %s, %s, CASE WHEN %s THEN now() END) RETURNING id""",
            (student_id, language, difficulty, finished)).fetchone()["id"]
        for position, location_id in enumerate(location_ids, start=1):
            db.execute("""INSERT INTO game_session_locations (game_session_id, position, location_id, found_at)
                VALUES (%s, %s, %s, CASE WHEN %s THEN now() END)""",
                (game_id, position, location_id, position <= found_count))


def check_badges(student_id):
    with get_connection() as db:
        return [badge.id for badge in award_badges(db, student_id)]


def saved_badges(student_id):
    with get_connection() as db:
        rows = db.execute("SELECT badge_id FROM student_badges WHERE student_id = %s", (student_id,)).fetchall()
    return sorted(row["badge_id"] for row in rows)


def test_finishing_every_basic_french_location_earns_french_basic(student):
    play_game(student, "fr", "basic", add_locations(5, "fr"), found_count=5)

    assert sorted(check_badges(student)) == ["fr_basic", "fr_first_hunt"]
    assert saved_badges(student) == ["fr_basic", "fr_first_hunt"]


def test_finding_only_some_basic_french_locations_earns_no_badge(student):
    play_game(student, "fr", "basic", add_locations(5, "fr"), found_count=3)

    assert check_badges(student) == []
    assert saved_badges(student) == []


def test_checking_twice_does_not_award_a_badge_twice(student):
    play_game(student, "fr", "basic", add_locations(5, "fr"), found_count=5)
    check_badges(student)

    assert check_badges(student) == []
    assert saved_badges(student) == ["fr_basic", "fr_first_hunt"]


def test_french_progress_does_not_earn_spanish_badges(student):
    add_locations(5, "es")
    play_game(student, "fr", "basic", add_locations(5, "fr"), found_count=5)

    assert not any(badge.startswith("es_") for badge in check_badges(student))
    assert not any(badge.startswith("es_") for badge in saved_badges(student))


def test_basic_and_advanced_only_does_not_earn_french_master(student):
    locations = add_locations(5, "fr")
    play_game(student, "fr", "basic", locations, found_count=5)
    play_game(student, "fr", "advanced", locations, found_count=5)

    assert "fr_master" not in check_badges(student)
    assert "fr_master" not in saved_badges(student)


def test_finishing_every_difficulty_earns_french_master(student):
    locations = add_locations(5, "fr")
    for difficulty in ("basic", "advanced", "expert"):
        play_game(student, "fr", difficulty, locations, found_count=5)

    assert "fr_master" in check_badges(student)
    assert "fr_master" in saved_badges(student)

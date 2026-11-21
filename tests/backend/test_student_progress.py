"""The "My progress" details: finished games, totals, fastest/slowest and hardest locations."""

import os
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg import sql
from psycopg.conninfo import make_conninfo

from database import get_connection
from main import app
from migrate import apply_migrations
from utils.passwords import hash_password

URL = "/api/student/progress/details"
PASSWORD = "test-password"


@pytest.fixture
def users(monkeypatch):
    """A fresh database with two students and a teacher. Returns their ids."""
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run progress integration tests")
    schema = "progress_test_" + uuid4().hex
    with psycopg.connect(url, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        try:
            connection.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
            apply_migrations(connection)
            monkeypatch.setenv("DATABASE_URL", make_conninfo(url, options=f"-c search_path={schema}"))
            with get_connection() as db:
                ids = {}
                for name, role in (("student", "student"), ("other", "student"), ("teacher", "teacher")):
                    ids[name] = db.execute("""INSERT INTO users (email, username, password, first_name, last_name, role)
                        VALUES (%s, %s, %s, 'Test', 'User', %s) RETURNING id""",
                        (name + "@example.com", name, hash_password(PASSWORD), role)).fetchone()["id"]
                for number, name in (("12345678", "student"), ("87654321", "other")):
                    db.execute("INSERT INTO students (user_id, student_number) VALUES (%s, %s)", (ids[name], number))
            yield ids
        finally:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


@pytest.fixture
def client():
    # HTTPS lets the test client send the login endpoint's Secure cookie.
    with TestClient(app, base_url="https://testserver") as client:
        yield client
    app.dependency_overrides.clear()


def login(client, name="student"):
    response = client.post("/api/auth/login", json={"email": name + "@example.com", "password": PASSWORD})
    assert response.status_code == 200, response.text


def add_game(student, finished_at, language="fr", difficulty="basic", points=10, seconds=600, spots=()):
    """Save a game that took `seconds`; finished_at=None means unfinished. spots are (building, listens, attempts)."""
    with get_connection() as db:
        game = db.execute("""INSERT INTO game_sessions (student_id, language_code, difficulty, points, started_at, finished_at)
            VALUES (%s, %s, %s, %s, COALESCE(%s::timestamptz, now()) - make_interval(secs => %s), %s) RETURNING id""",
            (student, language, difficulty, points, finished_at, seconds, finished_at)).fetchone()["id"]
        for position, (building, listens, attempts) in enumerate(spots, start=1):
            location = db.execute("INSERT INTO locations (building, room_number) VALUES (%s, '101') RETURNING id",
                                  (building,)).fetchone()["id"]
            db.execute("""INSERT INTO game_session_locations (game_session_id, position, location_id, listens, attempts)
                VALUES (%s, %s, %s, %s, %s)""", (game, position, location, listens, attempts))


def details(client):
    login(client)
    response = client.get(URL)
    assert response.status_code == 200, response.text
    return response.json()


def test_games_are_newest_first(users, client):
    add_game(users["student"], "2026-11-01", points=1)
    add_game(users["student"], "2026-11-03", points=3)
    add_game(users["student"], "2026-11-02", points=2)
    games = details(client)["games"]
    assert [game["points"] for game in games] == [3, 2, 1]
    assert set(games[0]) == {"finished_at", "language_code", "difficulty", "points", "time_seconds"}


def test_only_my_own_finished_games(users, client):
    add_game(users["student"], "2026-11-01", points=10)
    add_game(users["student"], None, points=99)
    add_game(users["other"], "2026-11-01", points=77, spots=[("OTHER", 5, 1)])
    data = details(client)
    assert [game["points"] for game in data["games"]] == [10]
    assert data["hardest_locations"] == []


def test_fastest_and_slowest_game(users, client):
    add_game(users["student"], "2026-11-01", points=1, seconds=900)
    add_game(users["student"], "2026-11-02", points=2, seconds=300)
    add_game(users["student"], "2026-11-03", points=3, seconds=600)
    data = details(client)
    assert (data["fastest_game"]["points"], data["fastest_game"]["time_seconds"]) == (2, 300)
    assert (data["slowest_game"]["points"], data["slowest_game"]["time_seconds"]) == (1, 900)


def test_top_3_hardest_locations_leave_out_0_listens(users, client):
    add_game(users["student"], "2026-11-01", spots=[("A", 2, 1), ("B", 7, 1), ("C", 0, 3), ("D", 4, 1), ("E", 1, 1)])
    hardest = details(client)["hardest_locations"]
    assert [location["building"] for location in hardest] == ["B", "D", "A"]
    assert hardest[0] == {"building": "B", "room_number": "101", "language_code": "fr", "difficulty": "basic", "listens": 7}


def test_hardest_location_tie_goes_to_more_attempts(users, client):
    add_game(users["student"], "2026-11-01", spots=[("FEW", 3, 1), ("MANY", 3, 4)])
    assert [location["building"] for location in details(client)["hardest_locations"]] == ["MANY", "FEW"]


def test_totals_and_per_language_totals(users, client):
    add_game(users["student"], "2026-11-01", language="fr", points=10)
    add_game(users["student"], "2026-11-02", language="fr", points=15)
    add_game(users["student"], "2026-11-03", language="es", points=20)
    data = details(client)
    assert (data["total_points"], data["games_finished"]) == (45, 3)
    per_language = {row["language_code"]: row for row in data["per_language"]}
    assert per_language["fr"] == {"language_code": "fr", "games_finished": 2, "points": 25}
    assert per_language["es"] == {"language_code": "es", "games_finished": 1, "points": 20}


def test_student_with_no_finished_games_gets_zeros_empty_lists_and_nulls(users, client):
    add_game(users["student"], None, points=50, spots=[("A", 4, 1)])
    assert details(client) == {"total_points": 0, "games_finished": 0, "games": [], "fastest_game": None,
                               "slowest_game": None, "hardest_locations": [], "per_language": []}


def test_must_be_logged_in_as_a_student(users, client):
    assert client.get(URL).status_code == 401
    login(client, "teacher")
    assert client.get(URL).status_code == 403


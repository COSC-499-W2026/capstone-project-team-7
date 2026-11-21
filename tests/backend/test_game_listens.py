"""Counting how many times a student plays each clue's audio."""

import os
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg import sql
from psycopg.conninfo import make_conninfo

import game_session
from database import get_connection
from main import app
from migrate import apply_migrations
from student_enrollment import require_student
from utils.passwords import hash_password

PASSWORD = "test-password"


@pytest.fixture
def users(monkeypatch):
    """A fresh database with two students and a teacher, and 5 French locations. Returns their ids."""
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run listen count integration tests")
    schema = "listens_test_" + uuid4().hex
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
                for _ in range(5):
                    location = db.execute("""INSERT INTO locations (building, room_number, latitude, longitude, radius_metres)
                        VALUES ('EME', %s, 49.94, -119.4, 50) RETURNING id""", (uuid4().hex,)).fetchone()["id"]
                    db.execute("""INSERT INTO location_clues (location_id, language_code, number_text, description_text)
                        VALUES (%s, 'fr', 'cent', 'une salle')""", (location,))
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


def start(client, name="student"):
    """Log in, start a French game and return its id."""
    login(client, name)
    response = client.post("/api/game/start")
    assert response.status_code == 201, response.text
    return response.json()["game_id"]


def listens(game_id):
    """The listen count at each position of the game, e.g. {1: 3, 2: 0, ...}."""
    with get_connection() as db:
        rows = db.execute("SELECT position, listens FROM game_session_locations WHERE game_session_id = %s",
                          (game_id,)).fetchall()
    return {row["position"]: row["listens"] for row in rows}


def test_new_locations_start_at_0_listens(users, client):
    game_id = start(client)
    assert listens(game_id) == {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}


def test_three_plays_count_as_3(users, client):
    game_id = start(client)
    for count in (1, 2, 3):
        response = client.post(f"/api/game/{game_id}/listen")
        assert response.status_code == 200
        assert response.json() == {"position": 1, "listens": count}
    assert listens(game_id)[1] == 3


def test_only_the_current_location_goes_up(users, client):
    game_id = start(client)
    with get_connection() as db:
        db.execute("UPDATE game_sessions SET current_position = 2 WHERE id = %s", (game_id,))
    client.post(f"/api/game/{game_id}/listen")
    assert listens(game_id) == {1: 0, 2: 1, 3: 0, 4: 0, 5: 0}


def test_play_for_the_wrong_clue_is_not_counted(users, client):
    game_id = start(client)
    clue = client.get(f"/api/game/{game_id}/clue").json()
    url = f"/api/game/{game_id}/listen"
    assert client.post(url, params={"position": 1, "clue_id": uuid4()}).status_code == 409
    assert client.post(url, params={"position": 2, "clue_id": clue["clue_id"]}).status_code == 409
    assert listens(game_id)[1] == 0
    assert client.post(url, params={"position": 1, "clue_id": clue["clue_id"]}).json()["listens"] == 1


def test_someone_elses_game_is_refused(users, client):
    other_game = start(client, "other")
    client.cookies.clear()
    login(client)
    response = client.post(f"/api/game/{other_game}/listen")
    assert response.status_code == 404
    assert response.json() == {"detail": "Game not found"}
    assert listens(other_game)[1] == 0


def test_a_finished_game_is_refused(users, client):
    game_id = start(client)
    with get_connection() as db:
        db.execute("UPDATE game_sessions SET finished_at = now() WHERE id = %s", (game_id,))
    assert client.post(f"/api/game/{game_id}/listen").status_code == 409
    assert listens(game_id)[1] == 0


def test_not_logged_in_gets_401(users, client):
    game_id = start(client)
    client.cookies.clear()
    assert client.post(f"/api/game/{game_id}/listen").status_code == 401
    assert listens(game_id)[1] == 0


def test_a_teacher_gets_403(users, client):
    game_id = start(client)
    client.cookies.clear()
    login(client, "teacher")
    assert client.post(f"/api/game/{game_id}/listen").status_code == 403
    assert listens(game_id)[1] == 0


def test_database_down_gives_503(client, monkeypatch):
    def unavailable():
        raise psycopg.OperationalError("secret details")
    app.dependency_overrides[require_student] = lambda: {"id": uuid4(), "role": "student"}
    monkeypatch.setattr(game_session, "get_connection", unavailable)
    response = client.post(f"/api/game/{uuid4()}/listen")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}

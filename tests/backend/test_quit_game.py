"""Quitting a game: it's kept but ends for good, and its points go back to 0."""

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

PASSWORD = "test-password"


@pytest.fixture
def users(monkeypatch):
    """A fresh database with two students and a teacher, and 5 French locations. Returns their ids."""
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run quit game integration tests")
    schema = "quit_game_test_" + uuid4().hex
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


def login(client, name="student"):
    response = client.post("/api/auth/login", json={"email": name + "@example.com", "password": PASSWORD})
    assert response.status_code == 200, response.text


def start(client):
    """Log in as the student, start a French game and return its id."""
    login(client)
    response = client.post("/api/game/start")
    assert response.status_code == 201, response.text
    return response.json()["game_id"]


def saved_game(game_id):
    with get_connection() as db:
        return db.execute("SELECT points, finished_at, quit_at FROM game_sessions WHERE id = %s", (game_id,)).fetchone()


def test_quitting_removes_the_game_from_ongoing(users, client):
    game_id = start(client)
    assert client.post(f"/api/game/{game_id}/quit").status_code == 200
    assert client.get("/api/game/ongoing").json() == []


def test_a_quit_game_has_no_clue(users, client):
    game_id = start(client)
    client.post(f"/api/game/{game_id}/quit")
    response = client.get(f"/api/game/{game_id}/clue")
    assert response.status_code == 409
    assert response.json() == {"detail": "This game was quit"}


def test_quitting_sets_the_points_to_0_and_does_not_finish_the_game(users, client):
    game_id = start(client)
    with get_connection() as db:
        db.execute("UPDATE game_sessions SET points = 40 WHERE id = %s", (game_id,))
    client.post(f"/api/game/{game_id}/quit")
    game = saved_game(game_id)
    assert game["points"] == 0
    assert game["quit_at"] is not None
    assert game["finished_at"] is None


def test_a_game_cannot_be_quit_twice(users, client):
    game_id = start(client)
    client.post(f"/api/game/{game_id}/quit")
    assert client.post(f"/api/game/{game_id}/quit").status_code == 409


def test_another_students_game_cannot_be_quit(users, client):
    with get_connection() as db:
        other_game = db.execute("""INSERT INTO game_sessions (student_id, language_code, difficulty, points)
            VALUES (%s, 'fr', 'basic', 40) RETURNING id""", (users["other"],)).fetchone()["id"]
    login(client)
    response = client.post(f"/api/game/{other_game}/quit")
    assert response.status_code == 404
    assert response.json() == {"detail": "Game not found"}
    assert saved_game(other_game)["points"] == 40
    assert client.post(f"/api/game/{uuid4()}/quit").status_code == 404


def test_must_be_logged_in_as_a_student(users, client):
    game_id = start(client)
    client.cookies.clear()
    assert client.post(f"/api/game/{game_id}/quit").status_code == 401
    login(client, "teacher")
    assert client.post(f"/api/game/{game_id}/quit").status_code == 403
    assert saved_game(game_id)["quit_at"] is None

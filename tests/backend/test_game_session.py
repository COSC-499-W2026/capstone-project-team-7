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
from utils.passwords import hash_password

URL = "/api/game/start"
PASSWORD = "test-password"


@pytest.fixture
def game_db(monkeypatch):
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run game session integration tests")
    schema = "game_test_" + uuid4().hex
    with psycopg.connect(url, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        try:
            connection.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
            apply_migrations(connection)
            monkeypatch.setenv("DATABASE_URL", make_conninfo(url, options=f"-c search_path={schema}"))
            with get_connection() as db:
                users = {}
                for role in ("student", "teacher", "admin"):
                    users[role] = db.execute("""INSERT INTO users
                        (email, username, password, first_name, last_name, role)
                        VALUES (%s, %s, %s, 'Test', 'User', %s) RETURNING id""",
                        (role + "@example.com", role, hash_password(PASSWORD), role)).fetchone()["id"]
                db.execute("INSERT INTO students (user_id, student_number) VALUES (%s, '12345678')",
                           (users["student"],))
            yield users["student"]
        finally:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


@pytest.fixture
def client():
    # HTTPS allows TestClient to send the login endpoint's Secure cookie.
    with TestClient(app, base_url="https://testserver") as client:
        yield client


def login(client, role="student"):
    response = client.post("/api/auth/login", json={"email": role + "@example.com", "password": PASSWORD})
    assert response.status_code == 200, response.text


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


def game_locations(game_id):
    with get_connection() as db:
        return db.execute("""SELECT position, location_id FROM game_session_locations
            WHERE game_session_id = %s ORDER BY position""", (game_id,)).fetchall()


def game_count():
    with get_connection() as db:
        return db.execute("SELECT count(*) AS n FROM game_sessions").fetchone()["n"]


def test_student_starts_game(game_db, client):
    french = add_locations(6, "fr")
    login(client)
    response = client.post(URL)
    assert response.status_code == 201
    body = response.json()
    assert body == {"game_id": body["game_id"], "language_code": "fr", "difficulty": "basic",
                    "current_position": 1, "total_locations": 5}
    rows = game_locations(body["game_id"])
    assert [row["position"] for row in rows] == [1, 2, 3, 4, 5]
    picked = {row["location_id"] for row in rows}
    assert len(picked) == 5 and picked <= set(french)
    with get_connection() as db:
        game = db.execute("SELECT student_id FROM game_sessions WHERE id = %s", (body["game_id"],)).fetchone()
    assert game["student_id"] == game_db


def test_locations_without_french_clue_are_never_picked(game_db, client):
    french = add_locations(5, "fr")
    add_locations(5, "es")
    login(client)
    response = client.post(URL)
    assert response.status_code == 201
    assert {row["location_id"] for row in game_locations(response.json()["game_id"])} == set(french)


def test_too_few_locations_returns_conflict(game_db, client):
    add_locations(4, "fr")
    add_locations(5, "es")
    login(client)
    response = client.post(URL)
    assert response.status_code == 409
    assert response.json() == {"detail": "Not enough locations for this language yet"}
    assert game_count() == 0


@pytest.mark.parametrize("role,status", [(None, 401), ("teacher", 403), ("admin", 403)])
def test_start_requires_student(game_db, client, role, status):
    add_locations(5, "fr")
    if role:
        login(client, role)
    assert client.post(URL).status_code == status
    assert game_count() == 0


def test_deleting_student_keeps_game(game_db, client):
    add_locations(5, "fr")
    login(client)
    game_id = client.post(URL).json()["game_id"]
    with get_connection() as db:
        db.execute("DELETE FROM users WHERE id = %s", (game_db,))
        game = db.execute("SELECT student_id FROM game_sessions WHERE id = %s", (game_id,)).fetchone()
    assert game["student_id"] is None
    assert len(game_locations(game_id)) == 5


def test_start_database_failure_is_safe(client, monkeypatch):
    def unavailable():
        raise psycopg.OperationalError("private database details")
    app.dependency_overrides[game_session.require_student] = lambda: {"id": uuid4(), "role": "student"}
    monkeypatch.setattr(game_session, "get_connection", unavailable)
    try:
        response = client.post(URL)
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}

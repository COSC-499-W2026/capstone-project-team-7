"""The building in a clue only shows on Basic; Advanced and Expert don't get it."""

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
def client(monkeypatch):
    """A logged-in student in a fresh database, with 5 French locations in building EME."""
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run clue building integration tests")
    schema = "clue_building_test_" + uuid4().hex
    with psycopg.connect(url, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        try:
            connection.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
            apply_migrations(connection)
            monkeypatch.setenv("DATABASE_URL", make_conninfo(url, options=f"-c search_path={schema}"))
            with get_connection() as db:
                student = db.execute("""INSERT INTO users (email, username, password, first_name, last_name, role)
                    VALUES ('student@example.com', 'student', %s, 'Test', 'User', 'student') RETURNING id""",
                    (hash_password(PASSWORD),)).fetchone()["id"]
                db.execute("INSERT INTO students (user_id, student_number) VALUES (%s, '12345678')", (student,))
                for _ in range(5):
                    location = db.execute("""INSERT INTO locations (building, room_number, latitude, longitude, radius_metres)
                        VALUES ('EME', %s, 49.94, -119.4, 50) RETURNING id""", (uuid4().hex,)).fetchone()["id"]
                    db.execute("""INSERT INTO location_clues (location_id, language_code, number_text, description_text)
                        VALUES (%s, 'fr', 'cent', 'une salle')""", (location,))
            # HTTPS lets the test client send the login endpoint's Secure cookie.
            with TestClient(app, base_url="https://testserver") as client:
                login = client.post("/api/auth/login", json={"email": "student@example.com", "password": PASSWORD})
                assert login.status_code == 200, login.text
                yield client
        finally:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def first_clue(client, difficulty):
    """Start a French game at this difficulty and return its first clue."""
    game = client.post("/api/game/start", json={"language_code": "fr", "difficulty": difficulty})
    assert game.status_code == 201, game.text
    clue = client.get(f"/api/game/{game.json()['game_id']}/clue")
    assert clue.status_code == 200, clue.text
    return clue.json()


def test_basic_clue_includes_the_building(client):
    assert first_clue(client, "basic")["building"] == "EME"


def test_advanced_clue_has_no_building(client):
    assert first_clue(client, "advanced")["building"] is None


def test_expert_clue_has_no_building(client):
    assert first_clue(client, "expert")["building"] is None

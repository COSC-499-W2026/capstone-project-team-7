"""Starting a game from an assigned hunt, and teachers seeing who completed it."""

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
from test_game_session import add_clips
from utils.passwords import hash_password

PASSWORD = "test-password"
TEACHERS = ("teacher", "teacher2")
STUDENTS = ("student", "classmate", "third", "outsider")


@pytest.fixture
def db(monkeypatch, tmp_path):
    """A fresh database: a teacher's French class (student, classmate, third), an Expert hunt and 5 locations."""
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run hunt progress integration tests")
    schema = "hunt_progress_test_" + uuid4().hex
    with psycopg.connect(url, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        try:
            connection.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
            apply_migrations(connection)
            monkeypatch.setenv("DATABASE_URL", make_conninfo(url, options=f"-c search_path={schema}"))
            monkeypatch.setenv("AUDIO_DIR", str(tmp_path))
            with get_connection() as conn:
                ids = {}
                for number, name in enumerate(TEACHERS + STUDENTS):
                    role = "teacher" if name in TEACHERS else "student"
                    ids[name] = conn.execute("""INSERT INTO users (email, username, password, first_name, last_name, role)
                        VALUES (%s, %s, %s, 'Test', 'User', %s) RETURNING id""",
                        (name + "@example.com", name, hash_password(PASSWORD), role)).fetchone()["id"]
                    if role == "teacher":
                        conn.execute("INSERT INTO teachers (user_id) VALUES (%s)", (ids[name],))
                    else:
                        conn.execute("INSERT INTO students (user_id, student_number) VALUES (%s, %s)",
                                     (ids[name], f"1000000{number}"))
                class_id = conn.execute("""INSERT INTO classes (teacher_id, name, language_code)
                    VALUES (%s, 'French 101', 'fr') RETURNING id""", (ids["teacher"],)).fetchone()["id"]
                for name in ("student", "classmate", "third"):
                    conn.execute("INSERT INTO class_enrollments (class_id, student_id) VALUES (%s, %s)",
                                 (class_id, ids[name]))
                ids["hunt"] = conn.execute("""INSERT INTO assigned_hunts (class_id, language_code, difficulty)
                    VALUES (%s, 'fr', 'expert') RETURNING id""", (class_id,)).fetchone()["id"]
                for _ in range(5):
                    location = conn.execute("""INSERT INTO locations (building, room_number, latitude, longitude, radius_metres)
                        VALUES ('EME', %s, 49.94, -119.4, 50) RETURNING id""", (uuid4().hex,)).fetchone()["id"]
                    conn.execute("""INSERT INTO location_clues (location_id, language_code, number_text, description_text)
                        VALUES (%s, 'fr', 'cent', 'une salle')""", (location,))
            add_clips()
            yield ids
        finally:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


@pytest.fixture
def client():
    # HTTPS lets the test client send the login endpoint's Secure cookie.
    with TestClient(app, base_url="https://testserver") as client:
        yield client


def login(client, name):
    client.cookies.clear()
    response = client.post("/api/auth/login", json={"email": name + "@example.com", "password": PASSWORD})
    assert response.status_code == 200, response.text


def add_hunt_game(db, name, finished=False, quit=False, points=0, seconds=600):
    """Save a game for this hunt that took `seconds`: finished, quit, or (by default) still in progress."""
    with get_connection() as conn:
        conn.execute("""INSERT INTO game_sessions
            (student_id, language_code, difficulty, hunt_id, points, started_at, finished_at, quit_at)
            VALUES (%s, 'fr', 'expert', %s, %s, now() - make_interval(secs => %s),
                CASE WHEN %s THEN now() END, CASE WHEN %s THEN now() END)""",
            (db[name], db["hunt"], points, seconds, finished, quit))


def saved_hunt_id(game_id):
    with get_connection() as conn:
        return conn.execute("SELECT hunt_id FROM game_sessions WHERE id = %s", (game_id,)).fetchone()["hunt_id"]


def completion(client, db):
    login(client, "teacher")
    response = client.get(f"/api/teacher/hunts/{db['hunt']}/completion")
    assert response.status_code == 200, response.text
    return {row["username"]: row for row in response.json()}


def my_hunt_completed(client, db, name="student"):
    login(client, name)
    return client.get("/api/student/hunts").json()[0]["completed"]


def test_starting_a_hunt_saves_hunt_id_and_the_hunts_settings(db, client):
    login(client, "student")
    response = client.post(f"/api/student/hunts/{db['hunt']}/start")
    assert response.status_code == 201
    assert (response.json()["language_code"], response.json()["difficulty"]) == ("fr", "expert")
    assert saved_hunt_id(response.json()["game_id"]) == db["hunt"]


def test_normal_start_game_has_no_hunt_id(db, client):
    login(client, "student")
    assert saved_hunt_id(client.post("/api/game/start").json()["game_id"]) is None


def test_student_not_in_the_class_gets_404(db, client):
    login(client, "outsider")
    response = client.post(f"/api/student/hunts/{db['hunt']}/start")
    assert (response.status_code, response.json()) == (404, {"detail": "Hunt not found"})
    assert client.post(f"/api/student/hunts/{uuid4()}/start").status_code == 404


def test_teacher_sees_completed_in_progress_and_not_started(db, client):
    add_hunt_game(db, "student", finished=True, points=50)
    add_hunt_game(db, "classmate")
    rows = completion(client, db)
    assert {name: row["status"] for name, row in rows.items()} == {
        "classmate": "in_progress", "student": "completed", "third": "not_started"}
    assert (rows["classmate"]["best_points"], rows["classmate"]["fastest_time"]) == (None, None)


def test_best_points_and_fastest_time_across_replays(db, client):
    add_hunt_game(db, "student", finished=True, points=50, seconds=900)
    add_hunt_game(db, "student", finished=True, points=80, seconds=1200)
    add_hunt_game(db, "student", points=99, seconds=60)
    row = completion(client, db)["student"]
    assert (row["status"], row["best_points"], row["fastest_time"]) == ("completed", 80, 900)


def test_a_quit_game_does_not_count(db, client):
    add_hunt_game(db, "classmate", quit=True, points=40)
    assert completion(client, db)["classmate"]["status"] == "not_started"
    assert my_hunt_completed(client, db, "classmate") is False


def test_another_teachers_hunt_gets_404(db, client):
    login(client, "teacher2")
    response = client.get(f"/api/teacher/hunts/{db['hunt']}/completion")
    assert (response.status_code, response.json()) == (404, {"detail": "Hunt not found"})


def test_student_completed_flag(db, client):
    add_hunt_game(db, "student")
    assert my_hunt_completed(client, db) is False
    add_hunt_game(db, "student", finished=True)
    assert my_hunt_completed(client, db) is True


def test_another_students_finish_does_not_count_for_me(db, client):
    add_hunt_game(db, "classmate", finished=True)
    assert my_hunt_completed(client, db) is False
    assert my_hunt_completed(client, db, "classmate") is True


def test_must_be_logged_in_with_the_right_role(db, client):
    start, completion_url = f"/api/student/hunts/{db['hunt']}/start", f"/api/teacher/hunts/{db['hunt']}/completion"
    assert client.post(start).status_code == 401
    assert client.get(completion_url).status_code == 401
    login(client, "teacher")
    assert client.post(start).status_code == 403
    login(client, "student")
    assert client.get(completion_url).status_code == 403


@pytest.mark.parametrize("building, expected", [("EME", 201), ("LIB", 409)])
def test_basic_hunt_uses_only_its_building(db, client, building, expected):
    with get_connection() as conn:
        conn.execute("UPDATE assigned_hunts SET difficulty = 'basic', building = %s WHERE id = %s",
                     (building, db["hunt"]))
        location = conn.execute("""INSERT INTO locations (building, room_number, latitude, longitude, radius_metres)
            VALUES ('LIB', '123', 49.94, -119.4, 50) RETURNING id""").fetchone()
        conn.execute("""INSERT INTO location_clues (location_id, language_code, number_text, description_text)
            VALUES (%s, 'fr', 'cent', 'une salle')""", (location["id"],))
    add_clips()
    login(client, "student")
    response = client.post(f"/api/student/hunts/{db['hunt']}/start")
    assert response.status_code == expected, response.text
    with get_connection() as conn:
        spots = conn.execute("""SELECT building FROM game_session_locations
            JOIN locations ON locations.id = game_session_locations.location_id""").fetchall()
        if expected == 409:
            assert not spots
            assert conn.execute("SELECT id FROM game_sessions").fetchone() is None
            return
        assert spots == [{"building": "EME"}] * 5
        conn.execute("DELETE FROM assigned_hunts WHERE id = %s", (db["hunt"],))
    game_id = response.json()["game_id"]
    assert client.post(f"/api/game/{game_id}/skip?position=1&revision=0").status_code == 409

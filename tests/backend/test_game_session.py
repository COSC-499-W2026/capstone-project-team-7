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
    monkeypatch.setattr(game_session, "check_answer", lambda photo, location: True)
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


def test_student_with_game_cannot_be_deleted(game_db, client):
    add_locations(5, "fr")
    login(client)
    game_id = client.post(URL).json()["game_id"]
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        with get_connection() as db:
            db.execute("DELETE FROM users WHERE id = %s", (game_db,))
    with get_connection() as db:
        game = db.execute("SELECT student_id FROM game_sessions WHERE id = %s", (game_id,)).fetchone()
    assert game["student_id"] == game_db
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


def clue_url(game_id):
    return f"/api/game/{game_id}/clue"


def start(client):
    add_locations(5, "fr")
    login(client)
    return client.post(URL).json()["game_id"]


ONGOING_URL = "/api/game/ongoing"


def other_students_game():
    """An unfinished game that belongs to a second student."""
    with get_connection() as db:
        other = db.execute("""INSERT INTO users (email, username, password, first_name, last_name, role)
            VALUES ('other@example.com', 'other', 'x', 'Other', 'Student', 'student') RETURNING id""").fetchone()["id"]
        db.execute("INSERT INTO students (user_id, student_number) VALUES (%s, '87654321')", (other,))
        return db.execute("""INSERT INTO game_sessions (student_id, language_code, difficulty)
            VALUES (%s, 'fr', 'basic') RETURNING id""", (other,)).fetchone()["id"]


def test_ongoing_lists_own_unfinished_games_newest_first(game_db, client):
    first = start(client)
    second = client.post(URL).json()["game_id"]
    with get_connection() as db:
        db.execute("UPDATE game_sessions SET current_position = 3 WHERE id = %s", (first,))
    response = client.get(ONGOING_URL)
    assert response.status_code == 200
    games = response.json()
    assert [game["game_id"] for game in games] == [second, first]
    assert games[1] == {"game_id": first, "language_code": "fr", "difficulty": "basic", "current_position": 3,
                        "total_locations": 5, "started_at": games[1]["started_at"]}


def test_ongoing_hides_finished_and_other_students_games(game_db, client):
    finished = start(client)
    with get_connection() as db:
        db.execute("UPDATE game_sessions SET finished_at = now() WHERE id = %s", (finished,))
    other_students_game()
    response = client.get(ONGOING_URL)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("role,status", [(None, 401), ("teacher", 403), ("admin", 403)])
def test_ongoing_requires_student(game_db, client, role, status):
    if role:
        login(client, role)
    assert client.get(ONGOING_URL).status_code == status


def test_ongoing_database_failure_is_safe(client, monkeypatch):
    def unavailable():
        raise psycopg.OperationalError("private database details")
    app.dependency_overrides[game_session.require_student] = lambda: {"id": uuid4(), "role": "student"}
    monkeypatch.setattr(game_session, "get_connection", unavailable)
    try:
        response = client.get(ONGOING_URL)
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_student_gets_first_clue_without_the_room_number(game_db, client):
    game_id = start(client)
    response = client.get(clue_url(game_id))
    assert response.status_code == 200
    assert response.json() == {"position": 1, "total_locations": 5, "building": "EME",
                               "audio_url": f"/api/game/{game_id}/clue/audio?position=1"}


def test_clue_audio_plays_the_current_rooms_file(game_db, client, tmp_path, monkeypatch):
    game_id = start(client)
    with get_connection() as db:
        room = db.execute("""SELECT locations.room_number FROM game_session_locations
            JOIN locations ON locations.id = game_session_locations.location_id
            WHERE game_session_id = %s AND position = 1""", (game_id,)).fetchone()["room_number"]
    (tmp_path / "fr").mkdir()
    (tmp_path / "fr" / f"EME-{room}.mp3").write_bytes(b"fake mp3")
    monkeypatch.setattr(game_session, "AUDIO_FOLDER", tmp_path / "fr")
    response = client.get(clue_url(game_id) + "/audio")
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.content == b"fake mp3"


def test_missing_audio_file_is_not_found(game_db, client, tmp_path, monkeypatch):
    game_id = start(client)
    monkeypatch.setattr(game_session, "AUDIO_FOLDER", tmp_path / "fr")
    response = client.get(clue_url(game_id) + "/audio")
    assert response.status_code == 404
    assert response.json() == {"detail": "Audio not found for this clue"}


def test_other_students_game_audio_is_not_found(game_db, client):
    login(client)
    assert client.get(clue_url(uuid4()) + "/audio").status_code == 404


def test_clue_follows_current_position(game_db, client):
    game_id = start(client)
    with get_connection() as db:
        db.execute("UPDATE game_sessions SET current_position = 3 WHERE id = %s", (game_id,))
    assert client.get(clue_url(game_id)).json()["position"] == 3


def test_other_students_game_is_not_found(game_db, client):
    game_id = start(client)
    with get_connection() as db:
        other = db.execute("""INSERT INTO users (email, username, password, first_name, last_name, role)
            VALUES ('other@example.com', 'other', 'hash', 'O', 'S', 'student') RETURNING id""").fetchone()["id"]
        db.execute("INSERT INTO students (user_id, student_number) VALUES (%s, '87654321')", (other,))
        db.execute("UPDATE game_sessions SET student_id = %s WHERE id = %s", (other, game_id))
    for missing in [game_id, uuid4()]:
        response = client.get(clue_url(missing))
        assert response.status_code == 404
        assert response.json() == {"detail": "Game not found"}


def test_finished_game_has_no_clue(game_db, client):
    game_id = start(client)
    with get_connection() as db:
        db.execute("UPDATE game_sessions SET finished_at = now() WHERE id = %s", (game_id,))
    response = client.get(clue_url(game_id))
    assert response.status_code == 409
    assert response.json() == {"detail": "This game is already finished"}


@pytest.mark.parametrize("role,status", [(None, 401), ("teacher", 403), ("admin", 403)])
def test_clue_requires_student(game_db, client, role, status):
    if role:
        login(client, role)
    assert client.get(clue_url(uuid4())).status_code == status


def test_invalid_game_id_is_rejected(client):
    app.dependency_overrides[game_session.require_student] = lambda: {"id": uuid4(), "role": "student"}
    try:
        assert client.get(clue_url("not-a-uuid")).status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_clue_database_failure_is_safe(client, monkeypatch):
    def unavailable():
        raise psycopg.OperationalError("private database details")
    app.dependency_overrides[game_session.require_student] = lambda: {"id": uuid4(), "role": "student"}
    monkeypatch.setattr(game_session, "get_connection", unavailable)
    try:
        response = client.get(clue_url(uuid4()))
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def answer(client, game_id, photo=b"fake jpeg"):
    return client.post(clue_url(game_id).replace("/clue", "/answer"), content=photo,
                       headers={"Content-Type": "image/jpeg"})


def spot(game_id, position):
    with get_connection() as db:
        return db.execute("""SELECT attempts, found_at FROM game_session_locations
            WHERE game_session_id = %s AND position = %s""", (game_id, position)).fetchone()


def test_correct_answer_moves_to_next_spot(game_db, client):
    game_id = start(client)
    response = answer(client, game_id)
    assert response.status_code == 200
    assert response.json() == {"correct": True, "attempts": 1, "finished": False, "next_position": 2,
                               "points_awarded": 10, "total_points": 10, "message": "Correct room!"}
    assert spot(game_id, 1)["found_at"] is not None
    assert client.get(clue_url(game_id)).json()["position"] == 2


def test_wrong_answer_stays_on_spot_and_counts_attempts(game_db, client, monkeypatch):
    game_id = start(client)
    monkeypatch.setattr(game_session, "check_answer", lambda photo, location: False)
    answer(client, game_id)
    response = answer(client, game_id)
    assert response.json() == {"correct": False, "attempts": 2, "finished": False, "next_position": None,
                               "points_awarded": 0, "total_points": 0,
                               "message": "The room number is incorrect or unreadable. Please retake the photo."}
    assert spot(game_id, 1) == {"attempts": 2, "found_at": None}
    assert client.get(clue_url(game_id)).json()["position"] == 1


def test_fifth_correct_answer_finishes_game(game_db, client):
    game_id = start(client)
    for _ in range(4):
        answer(client, game_id)
    response = answer(client, game_id)
    assert response.json() == {"correct": True, "attempts": 1, "finished": True, "next_position": None,
                               "points_awarded": 10, "total_points": 50, "message": "Correct room!"}
    assert client.get(clue_url(game_id)).status_code == 409
    assert answer(client, game_id).status_code == 409


def test_answer_needs_a_photo(game_db, client):
    game_id = start(client)
    response = answer(client, game_id, photo=b"")
    assert response.status_code == 422
    assert response.json() == {"detail": "Please take a photo of the room number"}
    assert spot(game_id, 1)["attempts"] == 0


def test_photo_too_large_is_rejected(game_db, client, monkeypatch):
    game_id = start(client)
    monkeypatch.setattr(game_session, "MAX_PHOTO_BYTES", 5)
    assert answer(client, game_id, photo=b"123456").status_code == 413


def test_cannot_answer_other_students_game(game_db, client):
    login(client)
    assert answer(client, uuid4()).status_code == 404


@pytest.mark.parametrize("role,status", [(None, 401), ("teacher", 403), ("admin", 403)])
def test_answer_requires_student(game_db, client, role, status):
    if role:
        login(client, role)
    assert answer(client, uuid4()).status_code == status


def test_answer_database_failure_is_safe(client, monkeypatch):
    def unavailable():
        raise psycopg.OperationalError("private database details")
    app.dependency_overrides[game_session.require_student] = lambda: {"id": uuid4(), "role": "student"}
    monkeypatch.setattr(game_session, "get_connection", unavailable)
    try:
        response = answer(client, uuid4())
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_concurrent_correct_photos_award_points_only_once(game_db, client, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    game_id = start(client)
    barrier = Barrier(2)

    def recognize(photo, location):
        barrier.wait(timeout=10)
        return True

    monkeypatch.setattr(game_session, "check_answer", recognize)

    def submit():
        with TestClient(app, base_url="https://testserver") as other:
            other.cookies.update(client.cookies)
            return answer(other, game_id)

    with ThreadPoolExecutor(max_workers=2) as workers:
        responses = list(workers.map(lambda _: submit(), range(2)))
    assert sorted(response.status_code for response in responses) == [200, 409]
    with get_connection() as db:
        game = db.execute("SELECT points, current_position FROM game_sessions WHERE id = %s", (game_id,)).fetchone()
    assert game == {"points": 10, "current_position": 2}
    assert spot(game_id, 1)["attempts"] == 1


def test_failed_spot_update_rolls_back_award_and_progress(game_db, client):
    game_id = start(client)
    with get_connection() as db:
        db.execute("UPDATE game_session_locations SET found_at = now() WHERE game_session_id = %s AND position = 1",
                   (game_id,))
    assert answer(client, game_id).status_code == 409
    with get_connection() as db:
        game = db.execute("SELECT points, current_position FROM game_sessions WHERE id = %s", (game_id,)).fetchone()
    assert game == {"points": 0, "current_position": 1}
    assert spot(game_id, 1)["attempts"] == 0

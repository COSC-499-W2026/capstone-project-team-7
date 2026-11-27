from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from database import get_connection
from test_class_roster import add_student
from test_game_session import URL as START_URL, add_locations, game_db, game_locations, login as student_login
from test_teacher_access import access_db, client, login

URL = "/api/teacher/classes/{}/report"
START = datetime(2026, 3, 1, 10, tzinfo=timezone.utc)


def add_game(db, student, difficulty, minutes, points, spots, language="fr", quit=False):
    """spots: (location_id, listens, skipped_location_ids, skipped_location_listens) per clue."""
    end = START + timedelta(minutes=minutes)
    game = db.execute("""INSERT INTO game_sessions
        (student_id, language_code, difficulty, started_at, finished_at, quit_at, points)
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
        (student, language, difficulty, START, None if quit else end, end if quit else None, points)).fetchone()["id"]
    for position, spot in enumerate(spots, start=1):
        db.execute("""INSERT INTO game_session_locations (game_session_id, position, location_id, listens,
            skipped_location_ids, skipped_location_listens, found_at) VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (game, position, *spot, None if quit else end))


@pytest.fixture
def report_db(access_db):
    with get_connection() as db:
        amir = add_student(db, "amir", "Young", "20000002", "teacher")
        add_student(db, "zoe", "Adams", "20000001", "teacher")
        add_student(db, "other", "Learner", "20000003", "teacher2")
        rooms = [db.execute("INSERT INTO locations (building, room_number) VALUES ('EME', %s) RETURNING id",
                            (room,)).fetchone()["id"] for room in ("101", "102", "103", "104")]
        a, b, c, d = rooms
        add_game(db, amir, "basic", 10, 100, [(a, 2, [c], [4]), (b, 1, [], [])])
        add_game(db, amir, "expert", 6, 200, [(a, 3, [d], [])])  # a skip saved before migration 019
        add_game(db, amir, "advanced", 3, 50, [(b, 5, [c], [7])], quit=True)
        add_game(db, amir, "advanced", 2, 400, [(b, 9, [c], [7])], language="es")
    return access_db, rooms


def get_report(client, class_id, role="teacher"):
    login(client, role)
    return client.get(URL.format(class_id))


def test_report_counts_only_finished_games_in_the_class_language(report_db, client):
    class_id, rooms = report_db
    response = get_report(client, class_id)
    assert response.status_code == 200
    zoe, amir = response.json()
    assert (amir["first_name"], amir["last_name"], amir["username"]) == ("Amir", "Young", "amir")
    assert (amir["total_points"], amir["games_finished"]) == (300, 2)
    assert amir["difficulties_completed"] == ["basic", "expert"]
    assert (amir["total_game_seconds"], amir["fastest_game_seconds"]) == (960, 360)
    assert (amir["locations_completed"], amir["locations_skipped"]) == (3, 2)
    assert [(play["location_id"], play["room_number"], play["plays"]) for play in amir["clue_plays"]] == [
        (str(rooms[0]), "101", 5), (str(rooms[1]), "102", 1), (str(rooms[2]), "103", 4), (str(rooms[3]), "104", 0)]
    assert zoe == {"student_id": zoe["student_id"], "first_name": "Zoe", "last_name": "Adams", "username": "zoe",
                   "total_points": 0, "difficulties_completed": [], "games_finished": 0, "total_game_seconds": 0,
                   "fastest_game_seconds": "No games completed yet", "locations_completed": 0,
                   "locations_skipped": 0, "clue_plays": []}


def test_skip_saves_the_skipped_clue_plays(game_db, client):
    add_locations(6, "fr")
    student_login(client)
    game_id = client.post(START_URL).json()["game_id"]
    for _ in range(2):
        assert client.post(f"/api/game/{game_id}/listen").status_code == 200
    assert client.post(f"/api/game/{game_id}/skip?position=1&revision=0").status_code == 200
    with get_connection() as db:
        spot = db.execute("""SELECT listens, skipped_location_listens FROM game_session_locations
            WHERE game_session_id = %s AND position = 1""", (game_id,)).fetchone()
    assert spot == {"listens": 0, "skipped_location_listens": [2]}
    assert len(game_locations(game_id)) == 5


def test_removed_students_are_left_out(report_db, client):
    class_id, _ = report_db
    with get_connection() as db:
        db.execute("UPDATE class_enrollments SET status = 'unenrolled', unenrolled_at = now() "
                   "WHERE student_id = (SELECT id FROM users WHERE username = 'zoe')")
    assert [row["username"] for row in get_report(client, class_id).json()] == ["amir"]


@pytest.mark.parametrize("role,status", [(None, 401), ("student", 403), ("admin", 403)])
def test_requires_teacher(report_db, client, role, status):
    class_id, _ = report_db
    if role:
        login(client, role)
    assert client.get(URL.format(class_id)).status_code == status


def test_other_teacher_and_missing_class_are_refused(report_db, client):
    class_id, _ = report_db
    for target in (class_id, uuid4()):
        response = get_report(client, target, "teacher2")
        assert response.status_code == 404
        assert response.json() == {"detail": "Class not found"}

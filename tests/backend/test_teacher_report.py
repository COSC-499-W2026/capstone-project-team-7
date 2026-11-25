import csv
import io
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

import game_session
from database import get_connection
from test_class_roster import add_student
from test_game_session import URL as START_URL, add_locations, answer, game_db, game_locations, login as student_login
from teacher_report import safe_cell
from test_teacher_access import access_db, client, login

URL = "/api/teacher/classes/{}/report"
CSV_URL = URL + ".csv"
START = datetime(2026, 3, 1, 10, tzinfo=timezone.utc)


def add_game(db, student, difficulty, minutes, points, spots, language="fr", quit=False):
    """spots: (location_id, listens, attempts, skipped ids, skipped listens, skipped attempts) per clue."""
    end = START + timedelta(minutes=minutes)
    game = db.execute("""INSERT INTO game_sessions
        (student_id, language_code, difficulty, started_at, finished_at, quit_at, points)
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
        (student, language, difficulty, START, None if quit else end, end if quit else None, points)).fetchone()["id"]
    for position, spot in enumerate(spots, start=1):
        db.execute("""INSERT INTO game_session_locations (game_session_id, position, location_id, listens, attempts,
            skipped_location_ids, skipped_location_listens, skipped_location_attempts, found_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
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
        add_game(db, amir, "basic", 10, 100, [(a, 2, 3, [c], [4], [5]), (b, 1, 1, [], [], [])])
        add_game(db, amir, "expert", 6, 200, [(a, 3, 2, [d], [], [])])  # a skip saved before migration 019
        add_game(db, amir, "advanced", 3, 50, [(b, 5, 9, [c], [7], [7])], quit=True)
        add_game(db, amir, "advanced", 2, 400, [(b, 9, 9, [c], [7], [7])], language="es")
    return access_db, rooms


def get_report(client, class_id, role="teacher"):
    login(client, role)
    return client.get(URL.format(class_id))


def test_report_counts_only_finished_games_in_the_class_language(report_db, client):
    class_id, rooms = report_db
    response = get_report(client, class_id)
    assert response.status_code == 200
    zoe, amir = response.json()["students"]
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


def test_skip_saves_the_skipped_clue_plays_and_attempts(game_db, client, monkeypatch):
    add_locations(6, "fr")
    student_login(client)
    game_id = client.post(START_URL).json()["game_id"]
    for _ in range(2):
        assert client.post(f"/api/game/{game_id}/listen").status_code == 200
    monkeypatch.setattr(game_session, "check_answer", lambda photo, location: False)
    assert answer(client, game_id).status_code == 200
    assert client.post(f"/api/game/{game_id}/skip?position=1&revision=0").status_code == 200
    with get_connection() as db:
        spot = db.execute("""SELECT listens, attempts, skipped_location_listens, skipped_location_attempts FROM game_session_locations
            WHERE game_session_id = %s AND position = 1""", (game_id,)).fetchone()
    assert spot == {"listens": 0, "attempts": 0, "skipped_location_listens": [2], "skipped_location_attempts": [1]}
    assert len(game_locations(game_id)) == 5


def test_removed_students_are_left_out(report_db, client):
    class_id, _ = report_db
    with get_connection() as db:
        db.execute("UPDATE class_enrollments SET status = 'unenrolled', unenrolled_at = now() "
                   "WHERE student_id = (SELECT id FROM users WHERE username = 'zoe')")
    assert [row["username"] for row in get_report(client, class_id).json()["students"]] == ["amir"]


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


def test_hardest_levels_rank_each_location_and_difficulty_separately(report_db, client):
    class_id, _ = report_db
    levels = get_report(client, class_id).json()["hardest_levels"]
    ranked = {name: [(item["room_number"], item["difficulty"], item["count"]) for item in items]
              for name, items in levels.items()}
    # The quit game and the Spanish game have the biggest counts, so they would top every list if counted.
    assert ranked == {
        "most_skipped": [("103", "basic", 1), ("104", "expert", 1)],
        "most_replayed": [("103", "basic", 4), ("101", "expert", 3), ("101", "basic", 2), ("102", "basic", 1)],
        "most_attempts": [("103", "basic", 5), ("101", "basic", 3), ("101", "expert", 2), ("102", "basic", 1)],
    }
    assert set(levels["most_skipped"][0]) == {"building", "room_number", "difficulty", "count"}


def test_class_without_games_has_empty_hardest_levels(access_db, client):
    response = get_report(client, access_db)
    assert response.status_code == 200
    assert response.json() == {"students": [], "hardest_levels": {
        "most_skipped": [], "most_replayed": [], "most_attempts": []}}


def test_csv_download_has_students_and_hardest_levels(report_db, client):
    class_id, _ = report_db
    with get_connection() as db:
        db.execute("UPDATE classes SET name = 'French 101 - Section A' WHERE id = %s", (class_id,))
    login(client)
    response = client.get(CSV_URL.format(class_id))
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == \
        f'attachment; filename="French-101-Section-A-report-{datetime.now(ZoneInfo("America/Vancouver")).date()}.csv"'
    rows = list(csv.reader(io.StringIO(response.text)))
    assert rows[0][:3] == ["Full name", "Username", "Total points"]
    assert rows[1] == ["Zoe Adams", "zoe", "0", "", "0", "0m 0s", "No games completed yet", "0", "0", ""]
    assert rows[2] == ["Amir Young", "amir", "300", "Basic, Expert", "2", "16m 0s", "6m 0s", "3", "2",
                       "EME 101: 5; EME 102: 1; EME 103: 4; EME 104: 0"]
    assert rows[3:9] == [[], ["Most skipped levels"], ["Building", "Room", "Difficulty", "Skips"],
                         ["EME", "103", "Basic", "1"], ["EME", "104", "Expert", "1"], []]
    assert ["Most replayed levels"] in rows and ["Most attempts levels"] in rows
    assert rows[-1] == ["EME", "102", "Basic", "1"]


def test_csv_makes_formula_text_safe(report_db, client):
    class_id, _ = report_db
    with get_connection() as db:
        db.execute("UPDATE users SET first_name = '=HYPERLINK(1)', last_name = 'x', username = '@zoe' "
                   "WHERE username = 'zoe'")
        db.execute("UPDATE locations SET building = '+EME'")
    login(client)
    rows = list(csv.reader(io.StringIO(client.get(CSV_URL.format(class_id)).text)))
    assert rows[1][:2] == ["'=HYPERLINK(1) x", "'@zoe"]
    assert rows[2][-1].startswith("'+EME 101: 5")
    assert rows[6][0] == "'+EME"
    assert safe_cell("-1") == "'-1" and safe_cell(5) == 5 and safe_cell("EME") == "EME"


@pytest.mark.parametrize("role,status", [(None, 401), ("student", 403), ("admin", 403)])
def test_csv_requires_teacher(report_db, client, role, status):
    class_id, _ = report_db
    if role:
        login(client, role)
    assert client.get(CSV_URL.format(class_id)).status_code == status


def test_csv_refuses_other_teacher_and_missing_class(report_db, client):
    class_id, _ = report_db
    login(client, "teacher2")
    for target in (class_id, uuid4()):
        response = client.get(CSV_URL.format(target))
        assert response.status_code == 404
        assert response.json() == {"detail": "Class not found"}

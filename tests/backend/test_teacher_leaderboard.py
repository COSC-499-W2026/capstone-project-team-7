from uuid import uuid4

import psycopg
import pytest

import teacher_access
from database import get_connection
from test_class_roster import add_student
from test_teacher_access import access_db, client, login

URL = "/api/teacher/classes/{}/leaderboard"


def add_game(db, student_id, language, points, finished=True):
    db.execute("""INSERT INTO game_sessions (student_id, language_code, difficulty, points, finished_at)
        VALUES (%s, %s, 'basic', %s, CASE WHEN %s THEN now() END)""", (student_id, language, points, finished))


@pytest.fixture
def leaderboard_db(access_db):
    with get_connection() as db:
        amir = add_student(db, "amir", "Young", "20000001", "teacher")
        zoe = add_student(db, "zoe", "Adams", "20000002", "teacher")
        other = add_student(db, "other", "Learner", "20000003", "teacher2")
        add_game(db, amir, "fr", 100)
        add_game(db, zoe, "fr", 150)
        add_game(db, zoe, "fr", 999, finished=False)
        add_game(db, amir, "es", 999)
        add_game(db, other, "fr", 1000)
    return access_db


def test_teacher_sees_their_class_ranked_by_points(leaderboard_db, client):
    login(client)
    response = client.get(URL.format(leaderboard_db))
    assert response.status_code == 200
    # Unfinished games, games in another language, and other classes' students don't count.
    assert response.json() == [
        {"rank": 1, "username": "zoe", "total_points": 150, "profile_icon": None},
        {"rank": 2, "username": "amir", "total_points": 100, "profile_icon": None},
    ]


def test_class_without_students_returns_empty_list(access_db, client):
    login(client)
    response = client.get(URL.format(access_db))
    assert response.status_code == 200
    assert response.json() == []


def test_missing_or_unowned_class_is_hidden(leaderboard_db, client):
    login(client, "teacher2")
    for class_id in [str(uuid4()), leaderboard_db]:
        response = client.get(URL.format(class_id))
        assert response.status_code == 404
        assert response.json() == {"detail": "Class not found"}


def test_invalid_class_id_is_rejected(access_db, client):
    login(client)
    assert client.get(URL.format("not-a-uuid")).status_code == 422


@pytest.mark.parametrize("role,status,detail", [
    (None, 401, "Unauthorized"),
    ("student", 403, "Teacher access required"),
    ("admin", 403, "Teacher access required"),
])
def test_requires_teacher(leaderboard_db, client, role, status, detail):
    if role:
        login(client, role)
    response = client.get(URL.format(leaderboard_db))
    assert response.status_code == status
    assert response.json() == {"detail": detail}


def test_leaderboard_database_failure_is_safe(leaderboard_db, client, monkeypatch):
    login(client)
    def unavailable():
        raise psycopg.OperationalError("private database details")
    monkeypatch.setattr(teacher_access, "get_connection", unavailable)
    response = client.get(URL.format(leaderboard_db))
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}

import psycopg
import pytest

import student_hunts
from database import get_connection
from test_teacher_access import access_db, client, login

URL = "/api/student/hunts"


@pytest.fixture
def hunts_db(access_db):
    """Student is in the 'teacher' class only; each class has one hunt assigned."""
    with get_connection() as db:
        student = db.execute("""INSERT INTO students (user_id, student_number)
            SELECT id, '12345678' FROM users WHERE email = 'student@example.com'
            RETURNING user_id""").fetchone()["user_id"]
        db.execute("INSERT INTO class_enrollments (class_id, student_id) VALUES (%s, %s)", (access_db, student))
        db.execute("""INSERT INTO assigned_hunts (class_id, language_code, difficulty, due_date)
            SELECT id, language_code, CASE name WHEN 'teacher' THEN 'basic' ELSE 'expert' END,
                CASE name WHEN 'teacher' THEN '2099-01-01'::date END
            FROM classes""")
    return student


def other_class_id():
    with get_connection() as db:
        return db.execute("SELECT id FROM classes WHERE name = 'teacher2'").fetchone()["id"]


def test_student_sees_hunt_assigned_to_their_class(hunts_db, access_db, client):
    login(client, "student")
    response = client.get(URL)
    assert response.status_code == 200
    body = response.json()
    assert body == [{"id": body[0]["id"], "class_id": access_db, "class_name": "teacher",
                     "language_code": "fr", "difficulty": "basic", "due_date": "2099-01-01"}]


def test_student_in_two_classes_sees_hunts_from_both(hunts_db, client):
    with get_connection() as db:
        db.execute("INSERT INTO class_enrollments (class_id, student_id) VALUES (%s, %s)",
                   (other_class_id(), hunts_db))
    login(client, "student")
    response = client.get(URL)
    assert response.status_code == 200
    assert [(hunt["class_name"], hunt["difficulty"], hunt["due_date"]) for hunt in response.json()] == [
        ("teacher", "basic", "2099-01-01"), ("teacher2", "expert", None)]


def test_hunts_from_other_classes_are_hidden(hunts_db, client):
    login(client, "student")
    assert "teacher2" not in [hunt["class_name"] for hunt in client.get(URL).json()]


def test_student_with_no_classes_gets_empty_list(access_db, client):
    with get_connection() as db:
        db.execute("""INSERT INTO students (user_id, student_number)
            SELECT id, '12345678' FROM users WHERE email = 'student@example.com'""")
        db.execute("""INSERT INTO assigned_hunts (class_id, language_code, difficulty)
            SELECT id, language_code, 'basic' FROM classes""")
    login(client, "student")
    response = client.get(URL)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("role,status", [(None, 401), ("teacher", 403), ("admin", 403)])
def test_requires_student(hunts_db, client, role, status):
    if role:
        login(client, role)
    assert client.get(URL).status_code == status


def test_database_failure_is_safe(hunts_db, client, monkeypatch):
    login(client, "student")
    def unavailable():
        raise psycopg.OperationalError("private database details")
    monkeypatch.setattr(student_hunts, "get_connection", unavailable)
    response = client.get(URL)
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}

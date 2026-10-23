from uuid import uuid4

import psycopg
import pytest

import auth
import teacher_access
from database import get_connection
from test_teacher_access import access_db, client, login

URL = "/api/teacher/classes/{}/students"


def add_student(db, username, last_name, student_number, class_name):
    """Create a student and enroll them in the class named class_name; returns the student id."""
    student_id = db.execute("""INSERT INTO users (email, username, password, first_name, last_name, role)
        VALUES (%s, %s, 'hash', %s, %s, 'student') RETURNING id""",
        (username + "@example.com", username, username.title(), last_name)).fetchone()["id"]
    db.execute("INSERT INTO students (user_id, student_number) VALUES (%s, %s)", (student_id, student_number))
    db.execute("""INSERT INTO class_enrollments (class_id, student_id)
        SELECT id, %s FROM classes WHERE name = %s""", (student_id, class_name))
    return str(student_id)


@pytest.fixture
def roster_db(access_db):
    with get_connection() as db:
        students = {name: add_student(db, name, last_name, number, "teacher")
                    for name, last_name, number in [("amir", "young", "20000002"), ("Zoe", "Adams", "20000001")]}
        add_student(db, "other", "Learner", "20000003", "teacher2")
    return access_db, students


def test_teacher_lists_enrolled_students(roster_db, client):
    class_id, students = roster_db
    login(client)
    response = client.get(URL.format(class_id))
    assert response.status_code == 200
    assert response.json() == [
        {"student_id": students["Zoe"], "username": "Zoe", "first_name": "Zoe",
         "last_name": "Adams", "student_number": "20000001"},
        {"student_id": students["amir"], "username": "amir", "first_name": "Amir",
         "last_name": "young", "student_number": "20000002"},
    ]


def test_class_without_students_returns_empty_list(access_db, client):
    login(client)
    response = client.get(URL.format(access_db))
    assert response.status_code == 200
    assert response.json() == []


def test_missing_or_unowned_class_is_hidden(roster_db, client):
    class_id, _ = roster_db
    login(client, "teacher2")
    for missing in [str(uuid4()), class_id]:
        response = client.get(URL.format(missing))
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
def test_requires_teacher(roster_db, client, role, status, detail):
    class_id, _ = roster_db
    if role:
        login(client, role)
    response = client.get(URL.format(class_id))
    assert response.status_code == status
    assert response.json() == {"detail": detail}


def test_session_check_database_failure_is_safe(client, monkeypatch):
    def unavailable():
        raise psycopg.OperationalError("private database details")
    # The session check runs through auth.current_user.
    monkeypatch.setattr(auth, "get_connection", unavailable)
    client.cookies.set("session", "test-token")
    response = client.get(URL.format(uuid4()))
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_roster_database_failure_is_safe(roster_db, client, monkeypatch):
    class_id, _ = roster_db
    login(client)
    def unavailable():
        raise psycopg.OperationalError("private database details")
    monkeypatch.setattr(teacher_access, "get_connection", unavailable)
    response = client.get(URL.format(class_id))
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}

from uuid import uuid4

import psycopg
import pytest

import auth
import class_enrollment
from database import get_connection
from test_teacher_access import access_db, client, login

URL = "/api/teacher/classes/{}/students"
STUDENT_NUMBER = "12345678"


@pytest.fixture
def enroll_db(access_db):
    with get_connection() as db:
        db.execute("""INSERT INTO students (user_id, student_number)
            SELECT id, %s FROM users WHERE email = 'student@example.com'""", (STUDENT_NUMBER,))
    return access_db


def enrollments():
    with get_connection() as db:
        return db.execute("SELECT class_id, student_id FROM class_enrollments").fetchall()


def enroll(client, class_id, student_number=STUDENT_NUMBER):
    return client.post(URL.format(class_id), json={"student_number": student_number})


def test_teacher_enrolls_student_in_owned_class(enroll_db, client):
    login(client)
    response = enroll(client, enroll_db, " 12345678 ")
    assert response.status_code == 201
    body = response.json()
    assert body == {"class_id": enroll_db, "student_id": body["student_id"],
                    "student_number": STUDENT_NUMBER}
    assert [(str(row["class_id"]), str(row["student_id"])) for row in enrollments()] == [
        (enroll_db, body["student_id"])]


def test_already_enrolled_student_is_rejected(enroll_db, client):
    login(client)
    assert enroll(client, enroll_db).status_code == 201
    response = enroll(client, enroll_db)
    assert response.status_code == 409
    assert response.json() == {"detail": "Student already enrolled"}
    assert len(enrollments()) == 1


def test_missing_or_unowned_class_is_hidden(enroll_db, client):
    login(client, "teacher2")
    for class_id in [str(uuid4()), enroll_db]:
        response = enroll(client, class_id)
        assert response.status_code == 404
        assert response.json() == {"detail": "Class not found"}
    assert enrollments() == []


def test_unknown_student_number_is_not_found(enroll_db, client):
    login(client)
    response = enroll(client, enroll_db, "99999999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Student not found"}
    assert enrollments() == []


@pytest.mark.parametrize("body", [{}, {"student_number": "   "}, {"student_number": "1" * 31},
                                  {"student_number": 12345678},
                                  {"student_number": STUDENT_NUMBER, "role": "admin"}])
def test_invalid_body_is_rejected(enroll_db, client, body):
    login(client)
    assert client.post(URL.format(enroll_db), json=body).status_code == 422
    assert enrollments() == []


@pytest.mark.parametrize("role,status", [(None, 401), ("student", 403), ("admin", 403)])
def test_requires_teacher(enroll_db, client, role, status):
    if role:
        login(client, role)
    assert enroll(client, enroll_db).status_code == status
    assert enrollments() == []


def test_session_check_database_failure_is_safe(client, monkeypatch):
    def unavailable():
        raise psycopg.OperationalError("private database details")
    # The session check runs through auth.current_user.
    monkeypatch.setattr(auth, "get_connection", unavailable)
    client.cookies.set("session", "test-token")
    response = enroll(client, uuid4())
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_enrollment_database_failure_is_safe(enroll_db, client, monkeypatch):
    login(client)
    def unavailable():
        raise psycopg.OperationalError("private database details")
    monkeypatch.setattr(class_enrollment, "get_connection", unavailable)
    response = enroll(client, enroll_db)
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}

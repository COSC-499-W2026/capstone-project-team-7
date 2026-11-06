import os
from hashlib import sha256
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import admin
import auth
from database import get_connection

app = FastAPI()
app.include_router(admin.router)
client = TestClient(app)


class FakeConnection:
    """Stands in for get_connection(); answers each fetchone() with the next queued row."""

    def __init__(self, *rows):
        self.rows = list(rows)
        self.queries = []

    def __call__(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def execute(self, query, params):
        self.queries.append(query)
        return self

    def fetchone(self):
        return self.rows.pop(0)


def use_connection(monkeypatch, connection):
    # The session check runs through auth.current_user, the reassignment through admin.
    monkeypatch.setattr(auth, "get_connection", connection)
    monkeypatch.setattr(admin, "get_connection", connection)


def reassign(email="teacher@example.com", token="admin-token"):
    client.cookies.set("session", token)
    return client.patch(f"/api/admin/classes/{uuid4()}/teacher", json={"teacher_email": email})


def test_admin_reassigns_class_to_approved_teacher(monkeypatch):
    teacher_id = uuid4()
    # Rows: admin session, approved teacher, updated class.
    connection = FakeConnection({"role": "admin"}, {"user_id": teacher_id}, {"id": uuid4(), "teacher_id": teacher_id})
    use_connection(monkeypatch, connection)

    response = reassign()

    assert response.status_code == 200
    assert response.json()["teacher_id"] == str(teacher_id)


def test_unapproved_teacher_is_rejected_and_class_unchanged(monkeypatch):
    connection = FakeConnection({"role": "admin"}, None)
    use_connection(monkeypatch, connection)

    response = reassign(email="not-approved@example.com")

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid teacher"}
    assert not any(query.startswith("UPDATE") for query in connection.queries)


@pytest.mark.parametrize("session,status", [(None, 401), ({"role": "teacher"}, 403)])
def test_only_logged_in_admins_can_reassign(monkeypatch, session, status):
    use_connection(monkeypatch, FakeConnection(session))
    assert reassign().status_code == status


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL is not configured")
def test_reassign_against_database():
    def user(role):
        email = uuid4().hex + "@example.com"
        user_id = connection.execute('''
            INSERT INTO users (email, username, password, first_name, last_name, role)
            VALUES (%s, %s, 'test-only-encoded-hash', 'Test', 'User', %s) RETURNING id
        ''', (email, uuid4().hex, role)).fetchone()["id"]
        return user_id, email

    with get_connection() as connection:
        admin_id, _ = user("admin")
        (old_teacher, _), (new_teacher, new_email), (unapproved, bad_email) = user("teacher"), user("teacher"), user("teacher")
        student_id, _ = user("student")
        for teacher in (old_teacher, new_teacher, unapproved):
            connection.execute("INSERT INTO teachers (user_id) VALUES (%s)", (teacher,))
        connection.execute("INSERT INTO authorized_teacher_emails (email) VALUES (%s)", (new_email,))
        connection.execute("INSERT INTO students (user_id, student_number) VALUES (%s, %s)", (student_id, uuid4().hex[:20]))
        class_id = connection.execute(
            "INSERT INTO classes (teacher_id, name, language_code) VALUES (%s, 'French 101', 'fr') RETURNING id",
            (old_teacher,),
        ).fetchone()["id"]
        connection.execute("INSERT INTO class_enrollments (class_id, student_id) VALUES (%s, %s)", (class_id, student_id))
        token = uuid4().hex
        connection.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (%s, %s, now() + interval '1 hour')",
            (sha256(token.encode()).hexdigest(), admin_id),
        )

    def assigned_teacher():
        with get_connection() as connection:
            return connection.execute("SELECT teacher_id FROM classes WHERE id = %s", (class_id,)).fetchone()["teacher_id"]

    url = f"/api/admin/classes/{class_id}/teacher"
    client.cookies.set("session", token)
    try:
        assert client.patch(url, json={"teacher_email": bad_email}).status_code == 400
        assert assigned_teacher() == old_teacher
        assert client.patch(url, json={"teacher_email": new_email.upper()}).status_code == 200
        assert assigned_teacher() == new_teacher
        with get_connection() as connection:
            enrollments = connection.execute(
                "SELECT student_id FROM class_enrollments WHERE class_id = %s", (class_id,)
            ).fetchall()
        assert enrollments == [{"student_id": student_id}]
    finally:
        with get_connection() as connection:
            connection.execute("DELETE FROM authorized_teacher_emails WHERE email = %s", (new_email,))
            connection.execute(
                "DELETE FROM users WHERE id = ANY(%s)", ([admin_id, old_teacher, new_teacher, unapproved, student_id],)
            )

import psycopg
import pytest
from fastapi.testclient import TestClient

import teacher_signup
from main import app

client = TestClient(app)
INFO = dict(email="teacher@example.com", username="teacher", password="password123",
            first_name="Test", last_name="Teacher")
URL = "/api/auth/teacher/signup"


@pytest.mark.parametrize("changes", [
    {"email": "invalid"}, {"username": " "}, {"username": "x" * 51},
    {"first_name": " "}, {"last_name": ""}, {"password": "short"},
    {"password": "é" * 37}, {"role": "admin"},
])
def test_invalid_signup_does_not_open_database(monkeypatch, changes):
    def unexpected_connection():
        pytest.fail("Invalid signup should not reach the database")

    monkeypatch.setattr(teacher_signup, "get_connection", unexpected_connection)
    assert client.post(URL, json={**INFO, **changes}).status_code == 422


def test_database_failure_returns_safe_error(monkeypatch):
    def unavailable():
        raise psycopg.OperationalError("private connection details")

    monkeypatch.setattr(teacher_signup, "get_connection", unavailable)
    response = client.post(URL, json=INFO)
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}

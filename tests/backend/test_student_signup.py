from uuid import UUID

import psycopg
import pytest
from fastapi.testclient import TestClient

import student_signup
from main import app
from test_registration import accounts, signup
from utils.passwords import verify_password

client = TestClient(app)
URL = "/api/auth/student/signup"


def test_signup_commits_validated_account_and_returns_safe_response(accounts, signup):
    signup.update(email=" ADA@EXAMPLE.COM ", first_name=" Ada ")
    response = client.post(URL, json=signup)
    assert response.status_code == 201
    user_id = UUID(response.json()["id"])
    assert response.json() == {"id": str(user_id), "role": "student"}
    assert "set-cookie" not in response.headers
    saved = accounts.execute(
        """SELECT u.*, s.student_number FROM users u
           JOIN students s ON s.user_id = u.id WHERE u.id = %s""", (user_id,)
    ).fetchone()
    assert saved["email"] == "ada@example.com" and saved["first_name"] == "Ada"
    assert saved["student_number"] == signup["student_number"]
    assert saved["role"] == "student" and verify_password(signup["password"], saved["password"])


@pytest.mark.parametrize("field", ["email", "username", "student_number"])
def test_duplicate_details_return_conflict_without_partial_account(accounts, signup, field):
    assert client.post(URL, json=signup).status_code == 201
    second = {**signup, "email": "new@example.com", "username": "new", "student_number": "87654321"}
    second[field] = signup[field].upper()
    response = client.post(URL, json=second)
    assert response.status_code == 409
    assert response.json() == {"detail": "Account details already in use"}
    assert accounts.execute("SELECT count(*) AS total FROM users").fetchone()["total"] == 1
    assert accounts.execute("SELECT count(*) AS total FROM students").fetchone()["total"] == 1


@pytest.mark.parametrize("field", [
    "email", "password", "first_name", "last_name", "student_number", "username",
])
def test_missing_field_is_rejected_before_service(monkeypatch, signup, field):
    signup.pop(field)
    assert_invalid(monkeypatch, signup)


@pytest.mark.parametrize("changes", [
    {"email": "invalid"}, {"password": "short"}, {"password": "é" * 37},
    {"first_name": " "}, {"username": "u" * 51}, {"student_number": "1" * 31},
    {"role": "admin"},
])
def test_invalid_input_is_rejected_before_service(monkeypatch, signup, changes):
    assert_invalid(monkeypatch, {**signup, **changes})


def assert_invalid(monkeypatch, body):
    def unexpected_call(**kwargs):
        pytest.fail("Invalid signup reached the registration service")

    monkeypatch.setattr(student_signup, "create_student", unexpected_call)
    assert client.post(URL, json=body).status_code == 422


@pytest.mark.parametrize("error", [psycopg.OperationalError("private details"), RuntimeError("missing URL")])
def test_database_failure_returns_safe_error(monkeypatch, signup, error):
    def unavailable(**kwargs):
        raise error

    monkeypatch.setattr(student_signup, "create_student", unavailable)
    response = client.post(URL, json=signup)
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_openapi_documents_request_and_responses():
    operation = client.get("/openapi.json").json()["paths"][URL]["post"]
    assert {"201", "409", "422", "503"} <= operation["responses"].keys()
    assert operation["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith("StudentSignupRequest")

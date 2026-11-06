from unittest.mock import MagicMock

import psycopg
import pytest
from fastapi.testclient import TestClient

import auth
import password_change
import registration
from main import app
from test_auth import HASHED, PASSWORD
from test_registration import accounts, signup
from utils.passwords import verify_password

URL = "/api/auth/change-password"
BODY = {"current_password": PASSWORD, "new_password": "new-password"}


@pytest.fixture
def setup(monkeypatch):
    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.execute.return_value.fetchone.return_value = {"id": "user-id", "password": HASHED}
    monkeypatch.setattr(auth, "get_connection", lambda: connection)
    monkeypatch.setattr(password_change, "get_connection", lambda: connection)
    with TestClient(app, base_url="https://testserver") as client:
        client.cookies.set("session", "test-token")
        yield client, connection


@pytest.mark.parametrize("role,new_password", [
    ("student", " password with spaces "), ("teacher", "a" * 72), ("admin", "é" * 36),
])
def test_change_hashes_password_and_revokes_sessions(setup, role, new_password):
    client, connection = setup
    connection.execute.return_value.fetchone.return_value["role"] = role
    response = client.post(URL, json={**BODY, "new_password": new_password})
    assert response.status_code == 200
    assert response.json() == {"message": "Password changed. Please log in again."}
    saved_hash, user_id = connection.execute.call_args_list[-2].args[1]
    assert saved_hash != new_password and verify_password(new_password, saved_hash)
    connection.execute.assert_called_with("DELETE FROM sessions WHERE user_id = %s", (user_id,))
    cookie = response.headers["set-cookie"].lower()
    assert all(value in cookie for value in ("max-age=0", "secure", "httponly", "samesite=lax"))


@pytest.mark.parametrize("password", ["wrong-password", "a" * 73, "é" * 37])
def test_wrong_current_password_changes_nothing(setup, password):
    client, connection = setup
    response = client.post(URL, json={**BODY, "current_password": password})
    assert response.status_code == 403
    assert response.json() == {"detail": "Current password is incorrect"}
    assert connection.execute.call_count == 2 and "set-cookie" not in response.headers


@pytest.mark.parametrize("body", [
    {}, {"current_password": PASSWORD}, {"new_password": "new-password"},
    *[{**BODY, "new_password": value} for value in ("short", " " * 8, "a" * 73, "é" * 37, 123, None)],
    {**BODY, "current_password": 123}, {**BODY, "user_id": "someone-else"},
])
def test_invalid_input_is_rejected_without_writes(setup, body):
    client, connection = setup
    assert client.post(URL, json=body).status_code == 422
    assert connection.execute.call_count <= 1


@pytest.mark.parametrize("missing_cookie", [True, False])
def test_missing_or_invalid_session_is_rejected(setup, missing_cookie):
    client, connection = setup
    if missing_cookie:
        client.cookies.clear()
    connection.execute.return_value.fetchone.return_value = None
    assert client.post(URL, json=BODY).status_code == 401
    assert connection.execute.call_count <= 1


@pytest.mark.parametrize("stage", [1, 2, 3, 4])
def test_database_failure_returns_safe_error(setup, stage):
    client, connection = setup
    result = connection.execute.return_value
    connection.execute.side_effect = [result] * (stage - 1) + [psycopg.OperationalError("private details")]
    response = client.post(URL, json=BODY)
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
    assert "set-cookie" not in response.headers
    assert connection.__exit__.call_args.args[0] is psycopg.OperationalError


def test_change_against_postgresql(accounts, signup, monkeypatch):
    registration.create_student(**signup)
    monkeypatch.setattr(auth, "get_connection", registration.get_connection)
    monkeypatch.setattr(password_change, "get_connection", registration.get_connection)
    with TestClient(app, base_url="https://testserver") as first, TestClient(app, base_url="https://testserver") as second:
        login = {"email": signup["email"], "password": signup["password"]}
        for client in (first, second):
            assert client.post("/api/auth/login", json=login).status_code == 200
        assert first.post(URL, json=BODY).status_code == 403
        assert first.post(URL, json={**BODY, "current_password": signup["password"]}).status_code == 200
        assert first.get("/api/auth/me").status_code == second.get("/api/auth/me").status_code == 401
        assert accounts.execute("SELECT count(*) AS total FROM sessions").fetchone()["total"] == 0
        assert first.post("/api/auth/login", json=login).status_code == 401
        assert first.post("/api/auth/login", json={**login, "password": BODY["new_password"]}).status_code == 200


def test_session_delete_failure_rolls_back_password(accounts, signup, monkeypatch):
    registration.create_student(**signup)
    monkeypatch.setattr(auth, "get_connection", registration.get_connection)
    monkeypatch.setattr(password_change, "get_connection", registration.get_connection)
    accounts.execute("""CREATE FUNCTION reject_delete() RETURNS trigger LANGUAGE plpgsql AS
        $$ BEGIN RAISE EXCEPTION 'test failure'; END; $$""")
    accounts.execute("CREATE TRIGGER reject_delete BEFORE DELETE ON sessions FOR EACH ROW EXECUTE FUNCTION reject_delete()")
    accounts.commit()
    with TestClient(app, base_url="https://testserver") as client:
        assert client.post("/api/auth/login", json={"email": signup["email"], "password": signup["password"]}).status_code == 200
        response = client.post(URL, json={**BODY, "current_password": signup["password"]})
        assert response.status_code == 503 and "set-cookie" not in response.headers
        assert client.get("/api/auth/me").status_code == 200
        saved = accounts.execute("SELECT password FROM users").fetchone()["password"]
        assert verify_password(signup["password"], saved)

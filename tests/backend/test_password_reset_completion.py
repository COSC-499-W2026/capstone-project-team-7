"""Complete password resets against isolated PostgreSQL accounts."""
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock

import psycopg
import pytest
from fastapi.testclient import TestClient

import auth
import password_reset
import registration
from main import app
from test_registration import accounts, signup
from utils.passwords import verify_password

URL = "/api/auth/reset-password"
BODY = {"token": "reset-token", "new_password": " new-password123 "}
client = TestClient(app, base_url="https://testserver")


@pytest.fixture
def reset_account(accounts, signup, monkeypatch):
    user = registration.create_student(**signup)
    monkeypatch.setattr(password_reset, "get_connection", registration.get_connection)
    monkeypatch.setattr(auth, "get_connection", registration.get_connection)
    password_reset.issue_reset_token(signup["email"], BODY["token"])
    return user


@pytest.mark.parametrize("password", [" new-password123 ", "a" * 8, "a" * 72, "é" * 36])
def test_reset_revokes_sessions_and_requires_new_password(accounts, signup, reset_account, password):
    with TestClient(app, base_url="https://testserver") as browser:
        credentials = {"email": signup["email"], "password": signup["password"]}
        assert browser.post("/api/auth/login", json=credentials).status_code == 200
        assert browser.post("/api/auth/login", json=credentials).status_code == 200
        response = browser.post(URL, json={**BODY, "new_password": password})
        assert response.status_code == 200 and "Please log in" in response.json()["message"]
        assert browser.cookies.get("session") is None
        assert browser.get("/api/auth/me").status_code == 401
        assert browser.post("/api/auth/login", json=credentials).status_code == 401
        assert browser.post("/api/auth/login", json={**credentials, "password": password}).status_code == 200
    saved = accounts.execute("SELECT password FROM users WHERE id = %s", (reset_account["id"],)).fetchone()
    assert saved["password"] != password and verify_password(password, saved["password"])
    assert accounts.execute("SELECT * FROM password_reset_tokens").fetchall() == []
    assert accounts.execute("SELECT count(*) AS n FROM sessions").fetchone()["n"] == 1
    assert accounts.execute("SELECT * FROM password_reset_email_limits").fetchone()
    assert client.post(URL, json=BODY).status_code == 422


@pytest.mark.parametrize("state", ["unknown", "expired", "replaced"])
def test_invalid_links_leave_password_unchanged(accounts, signup, reset_account, state):
    if state == "expired":
        accounts.execute("UPDATE password_reset_tokens SET expires_at = now() - interval '1 second'")
    elif state == "replaced":
        accounts.execute("UPDATE password_reset_tokens SET token_hash = %s", (auth.hash_token("replacement"),))
    accounts.commit()
    response = client.post(URL, json={**BODY, "token": "unknown" if state == "unknown" else BODY["token"]})
    assert response.status_code == 422
    assert response.json() == {"detail": "Reset link is invalid or expired. Request a new link."}
    saved = accounts.execute("SELECT password FROM users").fetchone()
    assert verify_password(signup["password"], saved["password"])


@pytest.mark.parametrize("body", [{}, {"token": "x"}, {**BODY, "token": ""}, {**BODY, "token": 1},
    {**BODY, "token": "x" * 257}, {**BODY, "new_password": "short"}, {**BODY, "new_password": " " * 8},
    {**BODY, "new_password": "é" * 37}, {**BODY, "new_password": "a" * 73},
    {**BODY, "new_password": None}, {**BODY, "role": "admin"}])
def test_validation_precedes_database(monkeypatch, body):
    connect = MagicMock()
    monkeypatch.setattr(password_reset, "get_connection", connect)
    assert client.post(URL, json=body).status_code == 422
    connect.assert_not_called()


@pytest.mark.parametrize("stage", ["execute", "__exit__"])
def test_database_errors_are_safe(monkeypatch, stage):
    connection = MagicMock()
    connection.__enter__.return_value = connection
    getattr(connection, stage).side_effect = psycopg.OperationalError("private details")
    monkeypatch.setattr(password_reset, "get_connection", lambda: connection)
    response = client.post(URL, json=BODY)
    assert response.status_code == 503 and response.json() == {"detail": "Database unavailable"}


def test_concurrent_token_use_succeeds_once(accounts, reset_account):
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: client.post(URL, json=BODY), range(2)))
    assert sorted(response.status_code for response in responses) == [200, 422]


def test_failure_rolls_back_password_token_and_sessions(accounts, signup, reset_account):
    accounts.execute("INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (%s, %s, now() + interval '1 day')",
                     (auth.hash_token("existing-session"), reset_account["id"]))
    accounts.execute("""CREATE FUNCTION reject_session_delete() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'private details'; END $$""")
    accounts.execute("CREATE TRIGGER reject_delete BEFORE DELETE ON sessions FOR EACH ROW EXECUTE FUNCTION reject_session_delete()")
    accounts.commit()
    assert client.post(URL, json=BODY).status_code == 503
    assert verify_password(signup["password"], accounts.execute("SELECT password FROM users").fetchone()["password"])
    assert accounts.execute("SELECT * FROM password_reset_tokens").fetchone()
    assert accounts.execute("SELECT * FROM sessions").fetchone()
    accounts.execute("DROP TRIGGER reject_delete ON sessions")
    accounts.commit()
    assert client.post(URL, json=BODY).status_code == 200


def test_login_holds_password_lock_until_session_is_saved(reset_account, signup, monkeypatch):
    def check(password, hashed):
        with registration.get_connection() as connection:
            with pytest.raises(psycopg.errors.LockNotAvailable):
                connection.execute("SELECT id FROM users WHERE id = %s FOR NO KEY UPDATE NOWAIT",
                                   (reset_account["id"],))
        return verify_password(password, hashed)

    monkeypatch.setattr(auth, "verify_password", check)
    response = client.post("/api/auth/login", json={"email": signup["email"], "password": signup["password"]})
    assert response.status_code == 200


def test_reset_preserves_other_accounts_sessions(accounts, reset_account, signup):
    other = registration.create_student(**{**signup, "email": "other@example.com", "username": "other",
                                           "student_number": "2"})
    accounts.execute("INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (%s, %s, now() + interval '1 day')",
                     (auth.hash_token("other-session"), other["id"]))
    accounts.commit()
    assert client.post(URL, json=BODY).status_code == 200
    assert accounts.execute("SELECT user_id FROM sessions").fetchall() == [{"user_id": other["id"]}]

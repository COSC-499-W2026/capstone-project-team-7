from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock

import psycopg
import pytest
from fastapi.testclient import TestClient

import password_reset
import registration
from auth import hash_token
from main import app
from test_registration import accounts, signup
from utils import mail

client = TestClient(app)
URL = "/api/auth/forgot-password"
BODY = {"email": " REGISTERED@example.com "}


@pytest.fixture
def setup(monkeypatch):
    connection, smtp = MagicMock(), MagicMock()
    connection.__enter__.return_value = connection
    connection.execute.return_value.fetchone.return_value = {"email": "registered@example.com"}
    monkeypatch.setattr(password_reset, "get_connection", lambda: connection)
    monkeypatch.setattr(mail.smtplib, "SMTP_SSL", smtp)
    for key, value in {"SMTP_USERNAME": "project@gmail.com", "SMTP_APP_PASSWORD": "app-password",
                       "FRONTEND_URL": "https://game.example/"}.items():
        monkeypatch.setenv(key, value)
    return connection, smtp


@pytest.mark.parametrize("registered", [True, False])
def test_generic_response_and_secure_email(setup, registered):
    connection, smtp = setup
    if not registered:
        connection.execute.return_value.fetchone.return_value = None
    response = client.post(URL, json=BODY)
    assert response.status_code == 200
    assert response.json() == {"message": "If an account matches that email, we'll send a reset link."}
    if not registered:
        smtp.assert_not_called()
        return
    server = smtp.return_value.__enter__.return_value
    server.login.assert_called_once_with("project@gmail.com", "app-password")
    message = server.send_message.call_args.args[0]
    assert message["To"] == "registered@example.com" and message["From"] == "project@gmail.com"
    token = message.get_content().split("token=")[1].split()[0]
    assert connection.execute.call_args.args[1][0] == hash_token(token)
    assert token not in response.text and "https://game.example/reset-password?token=" in message.get_content()
    assert smtp.call_args.args == ("smtp.gmail.com", 465)
    assert smtp.call_args.kwargs["context"].check_hostname


@pytest.mark.parametrize("body", [{}, {"email": "invalid"}, {"email": None}, {"email": 123},
                                  {**BODY, "role": "admin"}])
def test_invalid_input_does_not_access_database_or_email(setup, body):
    connection, smtp = setup
    assert client.post(URL, json=body).status_code == 422
    connection.execute.assert_not_called()
    smtp.assert_not_called()


@pytest.mark.parametrize("stage", ["execute", "__exit__"])
@pytest.mark.parametrize("error", [psycopg.OperationalError("private details"), RuntimeError("private details")])
def test_database_failure_is_safe(setup, stage, error):
    connection, smtp = setup
    getattr(connection, stage).side_effect = error
    response = client.post(URL, json=BODY)
    assert response.status_code == 503 and response.json() == {"detail": "Database unavailable"}
    smtp.assert_not_called()


@pytest.mark.parametrize("error", [mail.smtplib.SMTPException("private details"), OSError("private details"), None])
def test_email_failure_keeps_generic_response(setup, error, caplog, monkeypatch):
    if error is None:
        monkeypatch.delenv("SMTP_USERNAME")
    else:
        setup[1].side_effect = error
    assert client.post(URL, json=BODY).status_code == 200
    assert "Password reset email could not be sent" in caplog.text and "private details" not in caplog.text


def test_tokens_cooldown_rotation_and_unknown_email(accounts, signup, setup, monkeypatch):
    registration.create_student(**signup)
    monkeypatch.setattr(password_reset, "get_connection", registration.get_connection)
    body = {"email": signup["email"].upper()}
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: client.post(URL, json=body), range(2)))
    assert all(response.status_code == 200 for response in responses)
    assert responses[0].json() == responses[1].json() and setup[1].call_count == 1
    row = accounts.execute("SELECT *, expires_at - created_at AS lifetime FROM password_reset_tokens").fetchone()
    assert row["lifetime"].total_seconds() == 1800
    message = setup[1].return_value.__enter__.return_value.send_message.call_args.args[0]
    assert row["token_hash"] == hash_token(message.get_content().split("token=")[1].split()[0])
    accounts.execute("UPDATE password_reset_tokens SET created_at = now() - interval '2 minutes'")
    accounts.commit()
    assert client.post(URL, json=body).json() == responses[0].json()
    rotated = accounts.execute("SELECT token_hash FROM password_reset_tokens").fetchone()["token_hash"]
    assert rotated != row["token_hash"] and setup[1].call_count == 2
    assert client.post(URL, json={"email": "unknown@example.com"}).json() == responses[0].json()
    assert setup[1].call_count == 2

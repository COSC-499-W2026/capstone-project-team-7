from fastapi.testclient import TestClient
import psycopg
import pytest

import main

from main import app

client = TestClient(app)


def test_hello_returns_message():
    response = client.get("/api/hello")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_unknown_route_returns_404():
    response = client.get("/api/does-not-exist")

    assert response.status_code == 404


@pytest.mark.parametrize("error", [RuntimeError("missing URL"), psycopg.OperationalError("connection failed")])
def test_database_health_returns_503_without_connection_details(monkeypatch, error):
    def unavailable():
        raise error

    monkeypatch.setattr(main, "get_connection", unavailable)
    response = client.get("/api/health/db")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}

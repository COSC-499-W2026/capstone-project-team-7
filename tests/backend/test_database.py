"""Connection integration checks; no application schema is needed."""

import os

import pytest
from fastapi.testclient import TestClient

from database import get_connection
from main import app


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL is not configured")
def test_postgresql_connection_and_health_route():
    with get_connection() as connection:
        row = connection.execute("SELECT 1 AS connected").fetchone()
        assert row == {"connected": 1}

    response = TestClient(app).get("/api/health/db")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

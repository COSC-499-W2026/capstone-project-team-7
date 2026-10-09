"""Seed script tests run in a temporary schema so they never touch real accounts."""

import os
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg import sql
from psycopg.rows import dict_row

import auth
from main import app
from migrate import apply_migrations
from utils.seed_admin import seed_admin

client = TestClient(app)

EMAIL = 'admin@example.com'
PASSWORD = 'admin-password'


@pytest.fixture
def connect():
    """Yield a function that opens connections to a freshly migrated temporary schema."""
    url = os.getenv('TEST_DATABASE_URL')
    if not url:
        pytest.skip('Set TEST_DATABASE_URL to run seed script integration tests')
    schema = 'test_' + uuid4().hex

    def connect():
        return psycopg.connect(url, row_factory=dict_row, connect_timeout=5,
                               options=f'-c search_path={schema}')

    with psycopg.connect(url, autocommit=True, connect_timeout=5) as setup:
        setup.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
        try:
            setup.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(schema)))
            apply_migrations(setup)
            yield connect
        finally:
            setup.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


def admins(connect):
    with connect() as connection:
        return connection.execute("SELECT email FROM users WHERE role = 'admin'").fetchall()


def test_creates_admin_that_can_log_in(connect, monkeypatch):
    with connect() as connection:
        assert seed_admin(connection, EMAIL, PASSWORD) is True
    assert admins(connect) == [{'email': EMAIL}]

    monkeypatch.setattr(auth, 'get_connection', connect)
    response = client.post('/api/auth/login', json={'email': EMAIL, 'password': PASSWORD})

    assert response.status_code == 200
    assert response.json() == {'role': 'admin', 'redirect_to': '/admin/dashboard'}


def test_second_run_does_not_create_duplicate_admin(connect):
    with connect() as connection:
        assert seed_admin(connection, EMAIL, PASSWORD) is True
    with connect() as connection:
        assert seed_admin(connection, 'other@example.com', PASSWORD, 'other') is False

    assert admins(connect) == [{'email': EMAIL}]


def test_password_over_bcrypt_limit_is_rejected():
    with pytest.raises(ValueError):
        seed_admin(None, EMAIL, 'a' * (auth.MAX_PASSWORD_BYTES + 1))

"""Exercise registration against PostgreSQL in an isolated, temporary schema."""

import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from psycopg.rows import dict_row

import registration
from migrate import apply_migrations
from utils.passwords import verify_password


@pytest.fixture
def accounts(monkeypatch):
    url = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run registration integration tests")
    schema = "registration_" + uuid4().hex
    with psycopg.connect(url, autocommit=True, connect_timeout=5) as admin:
        admin.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        try:
            admin.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
            apply_migrations(admin)

            def connect():
                return psycopg.connect(url, options=f"-c search_path={schema}",
                                       row_factory=dict_row, connect_timeout=5)

            monkeypatch.setattr(registration, "get_connection", connect)
            with connect() as connection:
                yield connection
        finally:
            admin.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


@pytest.fixture
def signup():
    return dict(email="Ada@example.com", password=" password123 ", first_name="Ada",
                last_name="Lovelace", student_number="00123456", username="Ada")


def test_student_and_profile_are_committed_with_hashed_password(accounts, signup):
    result = registration.create_student(**signup)
    # A separate connection proves the service committed before returning.
    with registration.get_connection() as connection:
        saved = connection.execute(
            """SELECT u.*, s.student_number FROM users u
               JOIN students s ON s.user_id = u.id WHERE u.id = %s""", (result["id"],)
        ).fetchone()
    assert result == {key: saved[key] for key in result}
    assert result["role"] == "student"
    assert result["email"] == "ada@example.com"
    assert result["first_name"] == signup["first_name"]
    assert result["last_name"] == signup["last_name"]
    assert result["username"] == signup["username"]
    assert result["student_number"] == "00123456"
    assert saved["password"] != signup["password"]
    assert verify_password(signup["password"], saved["password"])
    assert "password" not in result


@pytest.mark.parametrize("field, duplicate", [
    ("email", "ADA@EXAMPLE.COM"), ("username", "ada"), ("student_number", "00123456"),
])
def test_duplicates_are_rejected_without_partial_account(accounts, signup, field, duplicate):
    original = registration.create_student(**signup)
    second = {**signup, "email": "new@example.com", "username": "new", "student_number": "87654321"}
    second[field] = duplicate
    with pytest.raises(registration.DuplicateStudentAccount) as error:
        registration.create_student(**second)
    assert error.value.field == field
    assert accounts.execute("SELECT id FROM users").fetchall() == [{"id": original["id"]}]
    assert accounts.execute("SELECT user_id FROM students").fetchall() == [{"user_id": original["id"]}]


def test_concurrent_duplicate_signup_creates_only_one_account(accounts, signup):
    def attempt():
        try:
            return registration.create_student(**signup)["id"]
        except registration.DuplicateStudentAccount:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: attempt(), range(2)))
    assert sum(result is not None for result in results) == 1
    assert accounts.execute("SELECT count(*) AS total FROM users").fetchone()["total"] == 1
    assert accounts.execute("SELECT count(*) AS total FROM students").fetchone()["total"] == 1


def test_signup_cannot_accept_client_role(accounts, signup):
    with pytest.raises(TypeError):
        registration.create_student(**signup, role="admin")
    assert accounts.execute("SELECT count(*) AS total FROM users").fetchone()["total"] == 0


@pytest.mark.parametrize("password", [" password123 ", "a" * 72, "é" * 36])
def test_signup_schema_integrates_with_service(accounts, signup, password):
    schemas = pytest.importorskip("schemas", reason="Signup schema arrives with PR 1")
    request = schemas.StudentSignupRequest(**{
        **signup, "password": password, "email": " ADA@EXAMPLE.COM ", "first_name": " Ada ",
    })
    result = registration.create_student(**request.model_dump())
    assert result == {**request.model_dump(exclude={"password"}), "id": result["id"], "role": "student"}
    saved = accounts.execute("SELECT password FROM users WHERE id = %s", (result["id"],)).fetchone()
    assert verify_password(password, saved["password"])
    duplicate = schemas.StudentSignupRequest(**{
        **signup, "email": "ada@example.com", "username": "another", "student_number": "87654321",
    })
    with pytest.raises(registration.DuplicateStudentAccount) as error:
        registration.create_student(**duplicate.model_dump())
    assert error.value.field == "email"

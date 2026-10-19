"""Schema integration tests use a temporary schema and roll back each test."""

import os
from uuid import UUID, uuid4

import psycopg
import pytest
from psycopg import sql

from migrate import apply_migrations


@pytest.fixture(scope='module')
def database():
    url = os.getenv('TEST_DATABASE_URL')
    if not url:
        pytest.skip('Set TEST_DATABASE_URL to run schema integration tests')
    schema = 'test_' + uuid4().hex
    with psycopg.connect(url, autocommit=True, connect_timeout=5) as connection:
        connection.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
        try:
            connection.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(schema)))
            apply_migrations(connection)
            yield connection
        finally:
            connection.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


@pytest.fixture
def db(database):
    with database.transaction(force_rollback=True):
        yield database


def account(db, role='student', **changes):
    token = uuid4().hex
    values = dict(email=token + '@example.com', username=token,
                  password='test-only-encoded-hash', role=role)
    values.update(changes)
    return db.execute('''
        INSERT INTO users (email, username, password, first_name, last_name, role)
        VALUES (%(email)s, %(username)s, %(password)s, 'Test', 'User', %(role)s)
        RETURNING id
    ''', values).fetchone()[0]


def student(db):
    user = account(db)
    db.execute('INSERT INTO students (user_id, student_number) VALUES (%s, %s)',
               (user, uuid4().hex[:20]))
    return user


def classroom(db):
    teacher = account(db, 'teacher')
    db.execute('INSERT INTO teachers (user_id) VALUES (%s)', (teacher,))
    return db.execute('''INSERT INTO classes (teacher_id, name, language_code)
        VALUES (%s, 'French 101', 'fr') RETURNING id''', (teacher,)).fetchone()[0]


def test_migration_is_repeatable(db):
    languages = db.execute('SELECT code, name FROM languages ORDER BY code').fetchall()
    assert apply_migrations(db) == []
    assert db.execute('SELECT code, name FROM languages ORDER BY code').fetchall() == languages


def test_supported_languages_are_seeded(db):
    codes = {row[0] for row in db.execute('SELECT code FROM languages').fetchall()}
    assert {'zh', 'fr', 'de', 'ja', 'ko', 'es'} <= codes


@pytest.mark.parametrize('role', ['student', 'teacher', 'admin'])
@pytest.mark.parametrize('password,error', [
    (None, psycopg.errors.NotNullViolation), ('', psycopg.errors.CheckViolation),
    ('   ', psycopg.errors.CheckViolation),
])
def test_every_role_requires_password(db, role, password, error):
    with pytest.raises(error), db.transaction():
        account(db, role, password=password)


@pytest.mark.parametrize('role', ['student', 'teacher', 'admin'])
def test_every_role_stores_password_value(db, role):
    user = account(db, role)
    assert db.execute('SELECT password FROM users WHERE id = %s', (user,)).fetchone()[0] == 'test-only-encoded-hash'


@pytest.mark.parametrize('field', ['email', 'username'])
def test_identity_is_case_insensitively_unique(db, field):
    account(db, **{field: 'Unique@example.com'})
    with pytest.raises(psycopg.errors.UniqueViolation), db.transaction():
        account(db, **{field: 'UNIQUE@example.com'})


def test_invalid_role_and_mismatched_subtype_are_rejected(db):
    with pytest.raises(psycopg.errors.CheckViolation), db.transaction():
        account(db, 'owner')
    user = student(db)
    with pytest.raises(psycopg.errors.ForeignKeyViolation), db.transaction():
        db.execute('INSERT INTO teachers (user_id) VALUES (%s)', (user,))
    with pytest.raises(psycopg.errors.ForeignKeyViolation), db.transaction():
        db.execute("INSERT INTO classes (teacher_id, name, language_code) VALUES (%s, 'Class', 'fr')", (user,))


def test_enrollment_constraints_and_account_deletion(db):
    user, course = student(db), classroom(db)
    query = 'INSERT INTO class_enrollments (class_id, student_id) VALUES (%s, %s)'
    db.execute(query, (course, user))
    with pytest.raises(psycopg.errors.UniqueViolation), db.transaction():
        db.execute(query, (course, user))
    with pytest.raises(psycopg.errors.ForeignKeyViolation), db.transaction():
        db.execute(query, (course, account(db, 'admin')))
    db.execute('DELETE FROM users WHERE id = %s', (user,))
    assert db.execute('SELECT * FROM students WHERE user_id = %s', (user,)).fetchall() == []
    assert db.execute('SELECT * FROM class_enrollments WHERE student_id = %s', (user,)).fetchall() == []


def test_unknown_language_is_rejected(db):
    course = classroom(db)
    with pytest.raises(psycopg.errors.ForeignKeyViolation), db.transaction():
        db.execute("UPDATE classes SET language_code = 'xx' WHERE id = %s", (course,))


def test_failed_migration_rolls_back_and_changed_file_is_rejected(db, tmp_path):
    invalid = tmp_path / '002_invalid.sql'
    invalid.write_text('CREATE TABLE should_rollback (id integer); SELECT * FROM missing_table;')
    with pytest.raises(psycopg.errors.UndefinedTable):
        apply_migrations(db, tmp_path)
    assert db.execute("SELECT to_regclass('should_rollback')").fetchone()[0] is None
    invalid.unlink()
    (tmp_path / '001_accounts_and_classes.sql').write_text('SELECT 1;')
    with pytest.raises(RuntimeError, match='changed'):
        apply_migrations(db, tmp_path)


def location(db, building='Test Building', room_number='101'):
    return db.execute('''INSERT INTO locations (building, room_number)
        VALUES (%s, %s) RETURNING id''', (building, room_number)).fetchone()[0]


def clue(db, location_id, language_code='fr', **changes):
    values = dict(location_id=location_id, language_code=language_code,
                  number_text='cent un', description_text='Près de la bibliothèque')
    values.update(changes)
    db.execute('''INSERT INTO location_clues
        (location_id, language_code, number_text, description_text)
        VALUES (%(location_id)s, %(language_code)s, %(number_text)s, %(description_text)s)
    ''', values)


def test_location_generates_uuid(db):
    place = location(db)
    assert isinstance(place, UUID)
    assert place.version == 4
    assert location(db, room_number='102') != place


def test_location_supports_multiple_language_clues(db):
    place = location(db)
    clue(db, place)
    clue(db, place, 'ja', number_text='百一', description_text='図書館の隣')
    assert db.execute('''SELECT language_code, number_text, description_text
        FROM location_clues WHERE location_id = %s ORDER BY language_code''',
        (place,)).fetchall() == [
            ('fr', 'cent un', 'Près de la bibliothèque'), ('ja', '百一', '図書館の隣')]


@pytest.mark.parametrize('field', ['building', 'room_number'])
@pytest.mark.parametrize('value,error', [
    (None, psycopg.errors.NotNullViolation), ('', psycopg.errors.CheckViolation),
    ('   ', psycopg.errors.CheckViolation), (' padded ', psycopg.errors.CheckViolation),
])
def test_location_requires_trimmed_nonempty_fields(db, field, value, error):
    with pytest.raises(error), db.transaction():
        location(db, **{field: value})


def test_room_number_is_unique_within_building(db):
    location(db)
    location(db, building='Other Building')
    location(db, room_number='102A')
    with pytest.raises(psycopg.errors.UniqueViolation), db.transaction():
        location(db)


@pytest.mark.parametrize('field', ['number_text', 'description_text'])
@pytest.mark.parametrize('value,error', [
    (None, psycopg.errors.NotNullViolation), ('', psycopg.errors.CheckViolation),
    ('   ', psycopg.errors.CheckViolation), (' padded ', psycopg.errors.CheckViolation),
])
def test_clue_requires_trimmed_nonempty_content(db, field, value, error):
    place = location(db)
    with pytest.raises(error), db.transaction():
        clue(db, place, **{field: value})


def test_clue_is_unique_per_location_and_language(db):
    place = location(db)
    clue(db, place)
    clue(db, location(db, room_number='102'))
    with pytest.raises(psycopg.errors.UniqueViolation), db.transaction():
        clue(db, place)


@pytest.mark.parametrize('missing', ['location', 'language'])
def test_clue_rejects_unknown_references(db, missing):
    place = uuid4() if missing == 'location' else location(db)
    with pytest.raises(psycopg.errors.ForeignKeyViolation), db.transaction():
        clue(db, place, 'xx' if missing == 'language' else 'fr')


@pytest.mark.parametrize('field', ['location_id', 'language_code'])
def test_clue_requires_references(db, field):
    place = location(db)
    values = dict(location_id=place, language_code='fr')
    values[field] = None
    with pytest.raises(psycopg.errors.NotNullViolation), db.transaction():
        clue(db, **values)


def test_deleting_location_removes_its_clues_only(db):
    languages = db.execute('SELECT code, name FROM languages ORDER BY code').fetchall()
    place, other = location(db), location(db, room_number='102')
    clue(db, place)
    clue(db, other)
    db.execute('DELETE FROM locations WHERE id = %s', (place,))
    assert db.execute('SELECT location_id FROM location_clues').fetchall() == [(other,)]
    assert db.execute('SELECT code, name FROM languages ORDER BY code').fetchall() == languages


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

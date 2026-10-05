"""Schema integration tests use a temporary schema and roll back each test."""

import os
from uuid import uuid4

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
    assert apply_migrations(db) == []
    assert db.execute('SELECT count(*) FROM languages').fetchone()[0] == 6


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

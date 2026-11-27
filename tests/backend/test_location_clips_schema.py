"""Schema tests for teachers' own clips, hunt clip choices and the clip a round plays."""

from uuid import UUID

import psycopg
import pytest

from test_database import account, database, db, location, student


def teacher(db):
    user = account(db, 'teacher')
    db.execute('INSERT INTO teachers (user_id) VALUES (%s)', (user,))
    return user


def clip(db, location_id, created_by=None, **changes):
    values = dict(location_id=location_id, language_code='fr', difficulty='basic',
                  label='Café clue', description=None, created_by=created_by)
    values.update(changes)
    return db.execute('''INSERT INTO location_clips
        (location_id, language_code, difficulty, label, description, created_by)
        VALUES (%(location_id)s, %(language_code)s, %(difficulty)s, %(label)s, %(description)s, %(created_by)s)
        RETURNING id''', values).fetchone()[0]


def hunt(db, owner):
    course = db.execute('''INSERT INTO classes (teacher_id, name, language_code)
        VALUES (%s, 'French 101', 'fr') RETURNING id''', (owner,)).fetchone()[0]
    return db.execute('''INSERT INTO assigned_hunts (class_id, language_code, difficulty)
        VALUES (%s, 'fr', 'basic') RETURNING id''', (course,)).fetchone()[0]


def choose(db, hunt_id, location_id, clip_id):
    db.execute('INSERT INTO hunt_clips (hunt_id, location_id, clip_id) VALUES (%s, %s, %s)',
               (hunt_id, location_id, clip_id))


def round_with(db, location_id, clip_id=None):
    game = db.execute('''INSERT INTO game_sessions (student_id, language_code, difficulty)
        VALUES (%s, 'fr', 'basic') RETURNING id''', (student(db),)).fetchone()[0]
    db.execute('''INSERT INTO game_session_locations (game_session_id, position, location_id, clip_id)
        VALUES (%s, 1, %s, %s)''', (game, location_id, clip_id))
    return game


def round_clip(db, game):
    return db.execute('SELECT clip_id FROM game_session_locations WHERE game_session_id = %s',
                      (game,)).fetchone()[0]


def test_new_clip_gets_an_id_and_time_and_is_not_retired(db):
    owner = teacher(db)
    identifier = clip(db, location(db), owner, description='Next to the café')
    row = db.execute('''SELECT created_by, label, description, created_at, retired_at
        FROM location_clips WHERE id = %s''', (identifier,)).fetchone()
    assert isinstance(identifier, UUID)
    assert row[:3] == (owner, 'Café clue', 'Next to the café')
    assert row[3] is not None and row[4] is None


@pytest.mark.parametrize('field,value,error', [
    ('label', None, psycopg.errors.NotNullViolation),
    ('label', '', psycopg.errors.CheckViolation),
    ('label', '   ', psycopg.errors.CheckViolation),
    ('label', ' padded ', psycopg.errors.CheckViolation),
    ('description', '', psycopg.errors.CheckViolation),
    ('description', ' padded ', psycopg.errors.CheckViolation),
    ('difficulty', 'hard', psycopg.errors.CheckViolation),
    ('language_code', 'xx', psycopg.errors.ForeignKeyViolation),
])
def test_invalid_clip_is_rejected(db, field, value, error):
    with pytest.raises(error), db.transaction():
        clip(db, location(db), **{field: value})


def test_deleted_teacher_keeps_their_clip_without_an_owner(db):
    owner = teacher(db)
    identifier = clip(db, location(db), owner)
    db.execute('DELETE FROM users WHERE id = %s', (owner,))
    assert db.execute('SELECT created_by FROM location_clips WHERE id = %s',
                      (identifier,)).fetchone() == (None,)


def test_hunt_saves_one_clip_choice_per_room(db):
    room = location(db)
    first, second = clip(db, room), clip(db, room, label='Second clue')
    assigned = hunt(db, teacher(db))
    choose(db, assigned, room, first)
    assert db.execute('SELECT location_id, clip_id FROM hunt_clips WHERE hunt_id = %s',
                      (assigned,)).fetchall() == [(room, first)]
    with pytest.raises(psycopg.errors.UniqueViolation), db.transaction():
        choose(db, assigned, room, second)


def test_hunt_cannot_choose_another_rooms_clip(db):
    other_room_clip = clip(db, location(db, room_number='316'))
    with pytest.raises(psycopg.errors.ForeignKeyViolation), db.transaction():
        choose(db, hunt(db, teacher(db)), location(db, room_number='317'), other_room_clip)


@pytest.mark.parametrize('delete', [
    'DELETE FROM assigned_hunts WHERE id = %(hunt)s',
    'DELETE FROM location_clips WHERE id = %(clip)s',
])
def test_deleting_the_hunt_or_clip_removes_the_choice(db, delete):
    room = location(db)
    identifier = clip(db, room)
    assigned = hunt(db, teacher(db))
    choose(db, assigned, room, identifier)
    db.execute(delete, dict(hunt=assigned, clip=identifier))
    assert db.execute('SELECT * FROM hunt_clips').fetchall() == []


def test_round_without_a_clip_plays_the_default(db):
    assert round_clip(db, round_with(db, location(db))) is None


def test_round_keeps_its_clip_and_falls_back_when_the_clip_is_deleted(db):
    room = location(db)
    identifier = clip(db, room)
    game = round_with(db, room, identifier)
    assert round_clip(db, game) == identifier
    db.execute('DELETE FROM location_clips WHERE id = %s', (identifier,))
    assert round_clip(db, game) is None

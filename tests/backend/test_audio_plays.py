from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import psycopg
import pytest
from fastapi import HTTPException

import game_session
from database import get_connection
from main import app
from test_game_session import game_db, client, start, clue_url, login
from utils import audio_plays


@pytest.fixture
def audio_game(game_db, client, tmp_path, monkeypatch):
    game_id = start(client)
    with get_connection() as db:
        rooms = db.execute("""SELECT room_number FROM locations JOIN game_session_locations
            ON locations.id = game_session_locations.location_id
            WHERE game_session_id = %s""", (game_id,)).fetchall()
    (tmp_path / 'fr').mkdir()
    for room in rooms:
        (tmp_path / 'fr' / f"EME-{room['room_number']}.mp3").write_bytes(b'fake mp3')
    monkeypatch.setenv('AUDIO_DIR', str(tmp_path))
    return game_id


@pytest.mark.parametrize('difficulty,limit', [('basic', None), ('advanced', 5), ('expert', 3)])
def test_total_plays_persist_and_new_clue_has_full_allowance(audio_game, client, difficulty, limit):
    with get_connection() as db:
        db.execute('UPDATE game_sessions SET difficulty = %s WHERE id = %s', (difficulty, audio_game))
    url = clue_url(audio_game)
    assert client.get(url).json()['audio_plays_remaining'] == limit
    for used in range(1, (limit or 8) + 1):
        response = client.get(url + '/audio?position=1')
        assert response.status_code == 200
        assert response.headers['cache-control'] == 'no-store'
        expected = None if limit is None else limit - used
        assert response.headers['x-audio-plays-remaining'] == ('unlimited' if expected is None else str(expected))
        assert client.get(url).json()['audio_plays_remaining'] == expected
    if limit is not None:
        assert client.get(url + '/audio').status_code == 409
        assert client.get(url).json()['audio_plays_remaining'] == 0
    with get_connection() as db:
        db.execute('UPDATE game_sessions SET current_position = 2 WHERE id = %s', (audio_game,))
    assert client.get(url).json()['audio_plays_remaining'] == limit
    assert client.get(url + '/audio?position=1').status_code == 409
    assert client.get(url).json()['audio_plays_remaining'] == limit
    assert client.get(url + '/audio?position=2').status_code == 200


def test_missing_audio_does_not_consume_play(audio_game, client, tmp_path, monkeypatch):
    monkeypatch.setenv('AUDIO_DIR', str(tmp_path / 'missing'))
    assert client.get(clue_url(audio_game) + '/audio').status_code == 404
    with get_connection() as db:
        assert db.execute('SELECT sum(audio_plays) AS n FROM game_session_locations WHERE game_session_id = %s',
                          (audio_game,)).fetchone()['n'] == 0


def test_simultaneous_requests_cannot_exceed_limit(audio_game, game_db):
    with get_connection() as db:
        db.execute("UPDATE game_sessions SET difficulty = 'expert' WHERE id = %s", (audio_game,))
    def consume(_):
        try:
            audio_plays.consume_play(audio_game, game_db, 1, 'expert')
            return 200
        except HTTPException as exc:
            return exc.status_code
    with ThreadPoolExecutor(max_workers=6) as pool:
        statuses = list(pool.map(consume, range(8)))
    assert statuses.count(200) == 3
    assert statuses.count(409) == 5


@pytest.mark.parametrize('role,status', [(None, 401), ('teacher', 403), ('admin', 403)])
def test_audio_requires_student(game_db, client, role, status):
    if role:
        login(client, role)
    assert client.get(clue_url(uuid4()) + '/audio').status_code == status


def test_audio_database_failure_is_safe(client, monkeypatch):
    def unavailable():
        raise psycopg.OperationalError('private details')
    app.dependency_overrides[game_session.require_student] = lambda: {'id': uuid4()}
    monkeypatch.setattr(game_session, 'get_connection', unavailable)
    try:
        response = client.get(clue_url(uuid4()) + '/audio')
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503
    assert response.json() == {'detail': 'Database unavailable'}


def test_consuming_play_database_failure_is_safe(monkeypatch):
    def unavailable():
        raise psycopg.OperationalError('private details')
    monkeypatch.setattr(audio_plays, 'get_connection', unavailable)
    with pytest.raises(HTTPException) as error:
        audio_plays.consume_play(uuid4(), uuid4(), 1, 'expert')
    assert error.value.status_code == 503


@pytest.mark.parametrize('difficulty,used,expected', [('basic', 100, None), ('advanced', 4, 1),
                                                    ('advanced', 5, 0), ('expert', 3, 0)])
def test_remaining_allowance(difficulty, used, expected):
    assert audio_plays.remaining_plays(difficulty, used) == expected

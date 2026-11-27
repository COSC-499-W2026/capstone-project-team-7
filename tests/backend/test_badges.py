import os
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

from badges import all_badges, award_badges, load_languages, load_progress
from database import get_connection
from migrate import apply_migrations
from test_game_session import add_locations


@pytest.fixture
def student(monkeypatch):
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run badge integration tests")
    schema = "badges_test_" + uuid4().hex
    with psycopg.connect(url, autocommit=True, connect_timeout=5) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        try:
            connection.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
            apply_migrations(connection)
            monkeypatch.setenv("DATABASE_URL", make_conninfo(url, options=f"-c search_path={schema}"))
            with get_connection() as db:
                student_id = db.execute("""INSERT INTO users (email, username, password, first_name, last_name, role)
                    VALUES ('student@example.com', 'student', 'hash', 'Test', 'User', 'student') RETURNING id""",
                    ).fetchone()["id"]
                db.execute("INSERT INTO students (user_id, student_number) VALUES (%s, '12345678')", (student_id,))
            yield student_id
        finally:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def play_game(student_id, language, difficulty, location_ids, found_count):
    """Save a game where the first found_count locations were found; it's finished if all were."""
    finished = found_count == len(location_ids)
    with get_connection() as db:
        game_id = db.execute("""INSERT INTO game_sessions (student_id, language_code, difficulty, finished_at)
            VALUES (%s, %s, %s, CASE WHEN %s THEN now() END) RETURNING id""",
            (student_id, language, difficulty, finished)).fetchone()["id"]
        for position, location_id in enumerate(location_ids, start=1):
            db.execute("""INSERT INTO game_session_locations (game_session_id, position, location_id, found_at)
                VALUES (%s, %s, %s, CASE WHEN %s THEN now() END)""",
                (game_id, position, location_id, position <= found_count))


def check_badges(student_id):
    with get_connection() as db:
        return [badge.id for badge in award_badges(db, student_id)]


def saved_badges(student_id):
    with get_connection() as db:
        rows = db.execute("SELECT badge_id FROM student_badges WHERE student_id = %s", (student_id,)).fetchall()
    return sorted(row["badge_id"] for row in rows)


def test_finishing_every_basic_french_location_earns_french_basic(student):
    play_game(student, "fr", "basic", add_locations(5, "fr"), found_count=5)

    assert sorted(check_badges(student)) == ["fr_basic", "fr_first_hunt"]
    assert saved_badges(student) == ["fr_basic", "fr_first_hunt"]


def test_finding_only_some_basic_french_locations_earns_no_badge(student):
    play_game(student, "fr", "basic", add_locations(5, "fr"), found_count=3)

    assert check_badges(student) == []
    assert saved_badges(student) == []


def test_checking_twice_does_not_award_a_badge_twice(student):
    play_game(student, "fr", "basic", add_locations(5, "fr"), found_count=5)
    check_badges(student)

    assert check_badges(student) == []
    assert saved_badges(student) == ["fr_basic", "fr_first_hunt"]


def test_french_progress_does_not_earn_spanish_badges(student):
    add_locations(5, "es")
    play_game(student, "fr", "basic", add_locations(5, "fr"), found_count=5)

    assert not any(badge.startswith("es_") for badge in check_badges(student))
    assert not any(badge.startswith("es_") for badge in saved_badges(student))


def mark_teacher_added(location_ids):
    with get_connection() as db:
        db.execute("UPDATE location_clues SET base_game = FALSE WHERE location_id = ANY(%s)", (location_ids,))


def progress(student_id):
    with get_connection() as db:
        return load_progress(db, student_id, load_languages(db))


def test_adding_a_teacher_clue_leaves_badge_progress_unchanged(student):
    play_game(student, "fr", "basic", add_locations(5, "fr"), found_count=5)
    before = progress(student)
    mark_teacher_added(add_locations(1, "fr"))

    assert progress(student) == before
    assert sorted(check_badges(student)) == ["fr_basic", "fr_first_hunt"]


def test_finding_a_teacher_added_room_does_not_count_towards_a_badge(student):
    base = add_locations(5, "fr")
    teacher_room = add_locations(1, "fr")
    mark_teacher_added(teacher_room)
    play_game(student, "fr", "basic", base[:4] + teacher_room, found_count=5)

    assert progress(student)["fr"].found == {"basic": 4}
    assert check_badges(student) == ["fr_first_hunt"]


def test_basic_and_advanced_only_does_not_earn_french_master(student):
    locations = add_locations(5, "fr")
    play_game(student, "fr", "basic", locations, found_count=5)
    play_game(student, "fr", "advanced", locations, found_count=5)

    assert "fr_master" not in check_badges(student)
    assert "fr_master" not in saved_badges(student)


def test_finishing_every_difficulty_earns_french_master(student):
    locations = add_locations(5, "fr")
    for difficulty in ("basic", "advanced", "expert"):
        play_game(student, "fr", difficulty, locations, found_count=5)

    assert "fr_master" in check_badges(student)
    assert "fr_master" in saved_badges(student)


def test_finishing_games_in_five_languages_does_not_earn_polyglot(student):
    for language in ("zh", "fr", "de", "ja", "ko"):
        play_game(student, language, "basic", add_locations(1, language), found_count=1)

    assert "polyglot" not in check_badges(student)
    assert "polyglot" not in saved_badges(student)


LANGUAGES = ("zh", "fr", "de", "ja", "ko", "es")


def finish_every_difficulty(student_id, language, difficulties=("basic", "advanced", "expert")):
    for difficulty in difficulties:
        play_game(student_id, language, difficulty, add_locations(1, language), found_count=1)


def test_finishing_every_difficulty_in_every_language_earns_polyglot(student):
    for language in LANGUAGES:
        finish_every_difficulty(student, language)

    assert "polyglot" in check_badges(student)
    assert "polyglot" in saved_badges(student)


def test_finishing_basic_only_in_every_language_does_not_earn_polyglot(student):
    for language in LANGUAGES:
        play_game(student, language, "basic", add_locations(1, language), found_count=1)

    assert "polyglot" not in check_badges(student)


def test_one_language_missing_expert_does_not_earn_polyglot(student):
    for language in ("zh", "fr", "de", "ja", "ko"):
        finish_every_difficulty(student, language)
    finish_every_difficulty(student, "es", ("basic", "advanced"))

    assert "polyglot" not in check_badges(student)
    assert "polyglot" not in saved_badges(student)


def test_a_quit_game_does_not_count_towards_polyglot(student):
    for language in ("zh", "fr", "de", "ja", "ko"):
        finish_every_difficulty(student, language)
    finish_every_difficulty(student, "es", ("basic", "advanced"))
    with get_connection() as db:
        db.execute("""INSERT INTO game_sessions (student_id, language_code, difficulty, quit_at)
            VALUES (%s, 'es', 'expert', now())""", (student,))

    assert "polyglot" not in check_badges(student)
    assert "polyglot" not in saved_badges(student)


def test_polyglot_is_named_polyglot_legend_and_keeps_its_saved_id():
    # Earned badges are saved by id, so renaming must keep the id "polyglot".
    names = {badge.id: badge.name for badge in all_badges({"fr": "French"})}

    assert names["polyglot"] == "Polyglot Legend"
    assert "Polyglot" not in names.values()


def test_badges_are_grouped_by_language_with_polyglot_first():
    ids = [badge.id for badge in all_badges({"de": "German", "fr": "French"})]

    assert ids == [
        "polyglot",
        "de_first_hunt", "de_basic", "de_advanced", "de_expert", "de_master",
        "fr_first_hunt", "fr_basic", "fr_advanced", "fr_expert", "fr_master",
    ]


def test_every_language_has_its_badges_together_in_the_same_order(student):
    with get_connection() as db:
        badges = all_badges(load_languages(db))
    languages = [badge.language for badge in badges[1:]]
    kinds = [badge.id.split("_", 1)[1] for badge in badges[1:]]

    assert badges[0].language is None
    assert languages == sorted(languages)  # each language appears in one block
    assert kinds == ["first_hunt", "basic", "advanced", "expert", "master"] * len(LANGUAGES)


def add_language(code, name):
    with get_connection() as db:
        db.execute("INSERT INTO languages (code, name) VALUES (%s, %s)", (code, name))


def test_a_new_language_gets_badges_with_plain_names(student):
    add_language("it", "Italian")
    play_game(student, "it", "basic", add_locations(5, "it"), found_count=5)

    with get_connection() as db:
        names = {badge.id: badge.name for badge in award_badges(db, student)}
    assert names == {"it_first_hunt": "Italian First Hunt", "it_basic": "Italian Basic"}


def test_a_new_language_is_needed_for_polyglot(student):
    add_language("it", "Italian")
    for language in LANGUAGES:
        finish_every_difficulty(student, language)

    assert "polyglot" not in check_badges(student)
    assert "polyglot" not in saved_badges(student)

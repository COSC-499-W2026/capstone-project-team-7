"""Language badges: the rule for each badge, and saving the ones a student has earned."""

from dataclasses import dataclass
from typing import Callable

from difficulties import Difficulty


@dataclass(frozen=True)
class Progress:
    """One student's progress in one language."""
    games_finished: int
    found: dict[str, int]  # distinct locations found at each difficulty
    total_locations: int  # locations that have a clue in this language


@dataclass(frozen=True)
class Badge:
    id: str
    name: str
    language: str
    rule: Callable[[Progress], bool]


def finished_games(count):
    return lambda progress: progress.games_finished >= count


def found_every_location(difficulty):
    return lambda progress: 0 < progress.total_locations <= progress.found.get(difficulty.value, 0)


def all_of(*rules):
    return lambda progress: all(rule(progress) for rule in rules)


LANGUAGES = {"zh": "Chinese", "fr": "French", "de": "German", "ja": "Japanese", "ko": "Korean", "es": "Spanish"}

# Add a badge by adding one line; earned badges are saved by id, so ids must never change.
BADGES = [
    *(Badge(f"{code}_first_hunt", "First hunt", code, finished_games(1)) for code in LANGUAGES),
    *(Badge(f"{code}_{difficulty.value}", f"{name} {difficulty.value.title()}", code, found_every_location(difficulty))
      for code, name in LANGUAGES.items() for difficulty in Difficulty),
    *(Badge(f"{code}_master", f"{name} Master", code, all_of(finished_games(1), *map(found_every_location, Difficulty)))
      for code, name in LANGUAGES.items()),
]


def load_progress(connection, student_id):
    """The student's progress in every language, keyed by language code."""
    totals = connection.execute(
        "SELECT language_code, count(*) AS n FROM location_clues GROUP BY language_code",
    ).fetchall()
    finished = connection.execute(
        """SELECT language_code, count(*) AS n FROM game_sessions
        WHERE student_id = %s AND finished_at IS NOT NULL GROUP BY language_code""",
        (student_id,),
    ).fetchall()
    # Only locations that still have a clue in the game's language count towards finishing it.
    found = connection.execute(
        """SELECT game_sessions.language_code, game_sessions.difficulty,
            count(DISTINCT game_session_locations.location_id) AS n
        FROM game_sessions
        JOIN game_session_locations ON game_session_locations.game_session_id = game_sessions.id
        JOIN location_clues ON location_clues.location_id = game_session_locations.location_id
            AND location_clues.language_code = game_sessions.language_code
        WHERE game_sessions.student_id = %s AND game_session_locations.found_at IS NOT NULL
        GROUP BY game_sessions.language_code, game_sessions.difficulty""",
        (student_id,),
    ).fetchall()
    return {
        code: Progress(
            games_finished=next((row["n"] for row in finished if row["language_code"] == code), 0),
            found={row["difficulty"]: row["n"] for row in found if row["language_code"] == code},
            total_locations=next((row["n"] for row in totals if row["language_code"] == code), 0),
        )
        for code in LANGUAGES
    }


def earned_badges(progress):
    """Every badge whose rule the progress meets."""
    return [badge for badge in BADGES if badge.rule(progress[badge.language])]


def list_badges(connection, student_id):
    """Every badge, with whether and when the student earned it."""
    rows = connection.execute(
        "SELECT badge_id, earned_at FROM student_badges WHERE student_id = %s", (student_id,),
    ).fetchall()
    earned = {row["badge_id"]: row["earned_at"] for row in rows}
    return [
        {"id": badge.id, "name": badge.name, "language": badge.language,
         "earned": badge.id in earned, "earned_at": earned.get(badge.id)}
        for badge in BADGES
    ]


def award_badges(connection, student_id):
    """Save badges the student has earned but doesn't have yet; return the new ones."""
    new = []
    for badge in earned_badges(load_progress(connection, student_id)):
        saved = connection.execute(
            """INSERT INTO student_badges (student_id, badge_id) VALUES (%s, %s)
            ON CONFLICT DO NOTHING RETURNING badge_id""",
            (student_id, badge.id),
        ).fetchone()
        if saved:
            new.append(badge)
    return new

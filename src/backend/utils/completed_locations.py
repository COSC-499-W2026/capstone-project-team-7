"""Shared location activity for a student's completed games."""


def completed_location_activity(connection, student_id, *, include_quit=False):
    return connection.execute(
        """SELECT locations.building, locations.room_number, game_sessions.language_code,
            game_sessions.difficulty, location_clues.number_text, location_clues.description_text,
            count(*)::int AS hunts,
            SUM(game_session_locations.listens)::int AS listens,
            SUM(game_session_locations.attempts)::int AS attempts,
            SUM(GREATEST(game_session_locations.attempts - 1, 0))::int AS extra_attempts,
            bool_or(game_session_locations.listens > 1 OR game_session_locations.attempts > 1) AS struggled
        FROM game_session_locations
        JOIN game_sessions ON game_sessions.id = game_session_locations.game_session_id
        JOIN locations ON locations.id = game_session_locations.location_id
        LEFT JOIN location_clues ON location_clues.location_id = locations.id
            AND location_clues.language_code = game_sessions.language_code
        WHERE game_sessions.student_id = %s AND game_sessions.finished_at IS NOT NULL
            AND (%s OR game_sessions.quit_at IS NULL)
        GROUP BY locations.id, game_sessions.language_code, game_sessions.difficulty,
            location_clues.number_text, location_clues.description_text""",
        (student_id, include_quit),
    ).fetchall()


def progress_locations(activity):
    qualifying = (row for row in activity if row["listens"] > 0)
    ranked = sorted(qualifying, key=lambda row: (-row["listens"], -row["attempts"],
                                                 row["building"], row["room_number"]))[:3]
    fields = ("building", "room_number", "language_code", "difficulty", "listens")
    return [{field: row[field] for field in fields} for row in ranked]


def debrief_locations(activity):
    qualifying = (row for row in activity if row["struggled"])
    ranked = sorted(qualifying, key=lambda row: (-row["extra_attempts"], -row["listens"],
                                                 row["building"], row["room_number"],
                                                 row["language_code"], row["difficulty"]))[:3]
    fields = ("building", "room_number", "language_code", "difficulty", "hunts", "listens", "attempts", "extra_attempts",
              "number_text", "description_text")
    return [{field: row[field] for field in fields} for row in ranked]

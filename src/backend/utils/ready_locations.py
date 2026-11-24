"""Locations a game can use: a clue in its language, a GPS target, and a clip for its difficulty."""

from utils.audio_storage import audio_path


def ready_location_ids(connection, language_code, difficulty):
    """Ids of the locations a game in this language and difficulty can play from start to finish."""
    locations = connection.execute(
        """SELECT locations.id, locations.building, locations.room_number FROM locations
        JOIN location_clues ON location_clues.location_id = locations.id
        WHERE location_clues.language_code = %s AND locations.latitude IS NOT NULL""",
        (language_code,),
    ).fetchall()
    # Clips are files, not rows, so they are checked on disk.
    return [location["id"] for location in locations
            if audio_path(language_code, location, difficulty).is_file()]

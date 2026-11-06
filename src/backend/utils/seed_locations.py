"""Add the demo locations and their French clues with: cd src/backend && python -m utils.seed_locations.

Safe to run more than once: locations and clues that already exist are skipped.
"""

from database import get_connection

# Coordinates are not saved yet: the locations table has no latitude/longitude columns
# until the GPS work adds them. They're kept here so nobody has to look them up again.
LOCATIONS = [
    {"building": "COM", "room_number": "316", "coordinates": (49.94072817380431, -119.39550274685362),
     "fr": ("trois cent seize", "Au niveau 3 du bâtiment The Commons.")},
    {"building": "LIB", "room_number": "312", "coordinates": (49.94005839760478, -119.39557784870397),
     "fr": ("trois cent douze", "Au niveau 3 de la bibliothèque.")},
    {"building": "ASC", "room_number": "130", "coordinates": (49.94016962009575, -119.39785593505913),
     "fr": ("cent trente", "Au niveau 1 du Centre des arts et des sciences.")},
    {"building": "LIB", "room_number": "317", "coordinates": (49.940081734450644, -119.39558759172651),
     "fr": ("trois cent dix-sept", "Au niveau 3 de la bibliothèque.")},
    {"building": "ART", "room_number": "376", "coordinates": (49.939490943519395, -119.39702142747328),
     "fr": ("trois cent soixante-seize", "Au niveau 3 du bâtiment des arts.")},
]


def seed_locations(connection, locations=LOCATIONS):
    """Add any missing locations and French clues; return how many new locations were added."""
    added = 0
    with connection.transaction():
        for location in locations:
            new = connection.execute(
                """INSERT INTO locations (building, room_number) VALUES (%s, %s)
                ON CONFLICT (building, room_number) DO NOTHING RETURNING id""",
                (location["building"], location["room_number"]),
            ).fetchone()
            added += new is not None
            location_id = connection.execute(
                "SELECT id FROM locations WHERE building = %s AND room_number = %s",
                (location["building"], location["room_number"]),
            ).fetchone()["id"]
            number_text, description_text = location["fr"]
            connection.execute(
                """INSERT INTO location_clues (location_id, language_code, number_text, description_text)
                VALUES (%s, 'fr', %s, %s) ON CONFLICT (location_id, language_code) DO NOTHING""",
                (location_id, number_text, description_text),
            )
    return added


if __name__ == "__main__":
    with get_connection() as connection:
        added = seed_locations(connection)
    print(f"Added {added} new locations." if added else "All demo locations already exist; nothing added.")

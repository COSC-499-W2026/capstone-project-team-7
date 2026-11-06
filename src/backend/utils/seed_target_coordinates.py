"""Save the demo seed's coordinates with a 50-metre arrival radius."""

from database import get_connection

DEMO_RADIUS_METRES = 50


def seed_target_coordinates(connection, locations):
    """Configure existing demo targets atomically; reject missing target rows."""
    with connection.transaction():
        for location in locations:
            latitude, longitude = location["coordinates"]
            target = connection.execute(
                """UPDATE locations
                SET latitude = %s, longitude = %s, radius_metres = %s
                WHERE building = %s AND room_number = %s RETURNING id""",
                (latitude, longitude, DEMO_RADIUS_METRES,
                 location["building"], location["room_number"]),
            ).fetchone()
            if target is None:
                raise ValueError("Demo target missing. Run the demo location seed first.")


if __name__ == "__main__":
    from utils.seed_locations import LOCATIONS

    with get_connection() as connection:
        seed_target_coordinates(connection, LOCATIONS)
    print("Demo target coordinates configured with a 50-metre radius.")

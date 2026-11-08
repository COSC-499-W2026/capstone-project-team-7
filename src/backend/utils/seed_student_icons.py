"""Give a student two icons for local testing: cd src/backend && python -m utils.seed_student_icons <email>.

Speedy Escargot stays locked, so equipping it shows the rejection. Safe to run more than once.
Only needed until students can redeem icons with points.
"""

import sys

from database import get_connection

DEMO_ICONS = ("croissant_cutie", "mac_the_macaron")


def seed_student_icons(connection, email):
    """Return True if the student exists and owns the demo icons, False if there is no such student."""
    student = connection.execute(
        """SELECT students.user_id FROM students JOIN users ON users.id = students.user_id
        WHERE lower(users.email) = lower(%s)""",
        (email.strip(),),
    ).fetchone()
    if student is None:
        return False
    for icon_id in DEMO_ICONS:
        connection.execute(
            "INSERT INTO student_icons (student_id, icon_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (student["user_id"], icon_id),
        )
    return True


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python -m utils.seed_student_icons <student email>')
    with get_connection() as connection:
        found = seed_student_icons(connection, sys.argv[1])
    print('Gave the student the demo icons.' if found else 'No student has that email; nothing changed.')

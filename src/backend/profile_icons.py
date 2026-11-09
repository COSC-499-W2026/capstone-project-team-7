"""Profile icons: the icon list, and which ones a student owns and has equipped."""

# Add an icon with one line here; ids are saved, so must never change.
PROFILE_ICONS = {
    "croissant_cutie": "Croissant Cutie",
    "mac_the_macaron": "Mac the Macaron",
    "speedy_escargot": "Speedy Escargot",
}


def list_icons(connection, student_id):
    """Every icon, with whether the student owns it and has it equipped."""
    rows = connection.execute(
        "SELECT icon_id FROM student_icons WHERE student_id = %s", (student_id,),
    ).fetchall()
    owned = {row["icon_id"] for row in rows}
    student = connection.execute(
        "SELECT equipped_icon_id FROM students WHERE user_id = %s", (student_id,),
    ).fetchone()
    equipped = student["equipped_icon_id"] if student else None
    return [
        {"id": icon_id, "name": name, "owned": icon_id in owned, "equipped": icon_id == equipped}
        for icon_id, name in PROFILE_ICONS.items()
    ]


def equip_icon(connection, student_id, icon_id):
    """Equip the icon if the student owns it; return False and change nothing if they don't."""
    equipped = connection.execute(
        """UPDATE students SET equipped_icon_id = %s
        WHERE user_id = %s AND EXISTS (
            SELECT 1 FROM student_icons WHERE student_id = %s AND icon_id = %s
        ) RETURNING user_id""",
        (icon_id, student_id, student_id, icon_id),
    ).fetchone()
    return equipped is not None

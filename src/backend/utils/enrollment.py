"""Shared class enrollment writes for teachers, admins and students."""


def enroll(connection, class_id, student_id):
    """Enroll a student, or bring back one who was removed. Returns False if already enrolled."""
    # A returning student keeps their first enrolled_at, so their full history in the class stays together.
    return connection.execute(
        """INSERT INTO class_enrollments (class_id, student_id) VALUES (%s, %s)
        ON CONFLICT (class_id, student_id) DO UPDATE SET status = 'enrolled', unenrolled_at = NULL
        WHERE class_enrollments.status = 'unenrolled'
        RETURNING class_id""",
        (class_id, student_id),
    ).fetchone() is not None

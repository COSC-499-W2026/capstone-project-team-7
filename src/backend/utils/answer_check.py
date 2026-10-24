"""Decide whether a student's photo answers the current clue."""


def check_answer(photo, location):
    """Temporary: every photo counts as correct until the OCR (room number) and GPS checks are added.

    Later this will read the room number in the photo and compare it to location["room_number"],
    and check the student is near the building. The answer endpoint won't need to change.
    """
    return True

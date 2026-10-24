"""Compare recognized room identifiers with the server's current target."""

from utils.ocr import extract_room_numbers


def check_answer(photo, location):
    """Require the full building and room identifier, preserving leading zeros."""
    expected = f"{location['building'].strip().upper()} {location['room_number'].strip()}"
    return expected in extract_room_numbers(photo)

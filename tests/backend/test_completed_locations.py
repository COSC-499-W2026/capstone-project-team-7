from utils.completed_locations import debrief_locations, progress_locations


def location(building, listens, attempts, hunts=1, struggled=None):
    return {"building": building, "room_number": "101", "language_code": "fr", "difficulty": "basic",
            "hunts": hunts, "listens": listens, "attempts": attempts, "number_text": None, "description_text": None,
            "extra_attempts": max(attempts - hunts, 0),
            "struggled": (listens > 1 or attempts > 1) if struggled is None else struggled}


def test_progress_and_debrief_preserve_different_selection_and_ranking():
    activity = [location("A", 1, 1), location("B", 0, 4), location("C", 5, 1), location("D", 3, 2)]
    progress = progress_locations(activity)
    debrief = debrief_locations(activity)
    assert [row["building"] for row in progress] == ["C", "D", "A"]
    assert [row["building"] for row in debrief] == ["B", "D", "C"]
    assert set(progress[0]) == {"building", "room_number", "language_code", "difficulty", "listens"}
    assert debrief[0]["extra_attempts"] == 3


def test_debrief_uses_per_hunt_struggle_not_aggregate_counts():
    repeated_without_difficulty = location("A", 2, 2, hunts=2, struggled=False)
    assert debrief_locations([repeated_without_difficulty]) == []
    assert len(progress_locations([repeated_without_difficulty])) == 1

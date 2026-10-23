from utils.generate_audio import AUDIO_FOLDER, audio_filename
from utils.seed_locations import LOCATIONS


def test_audio_is_named_by_building_and_room():
    assert audio_filename({"building": "COM", "room_number": "316"}) == "COM-316.mp3"


def test_every_demo_location_gets_its_own_file():
    names = {audio_filename(location) for location in LOCATIONS}
    assert len(names) == 5


def test_audio_is_saved_where_the_website_serves_it():
    assert AUDIO_FOLDER.parts[-4:] == ("frontend", "public", "audio", "fr")

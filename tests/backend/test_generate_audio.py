from utils.audio_storage import audio_filename
from utils.seed_locations import LOCATIONS


def test_every_demo_location_gets_its_own_file():
    names = {audio_filename(location) for location in LOCATIONS}
    assert len(names) == 5

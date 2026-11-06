import random
from uuid import uuid4

import pytest

from utils.location_picker import LOCATIONS_PER_HUNT, NotEnoughLocations, pick_locations


def pool(size):
    return [uuid4() for _ in range(size)]


@pytest.mark.parametrize("size", [5, 20])
def test_picks_five_distinct_locations_from_pool(size):
    options = pool(size)
    original = list(options)
    picked = pick_locations(options, random.Random(499))
    assert len(picked) == LOCATIONS_PER_HUNT == 5
    assert len(set(picked)) == 5
    assert set(picked) <= set(options)
    assert options == original


def test_repeated_ids_in_pool_never_repeat_in_hunt():
    options = pool(5)
    assert sorted(pick_locations(options * 3)) == sorted(options)


def test_each_hunt_gets_a_new_random_pick():
    options = pool(20)
    rng = random.Random(499)
    assert pick_locations(options, rng) != pick_locations(options, rng)


def test_same_seed_gives_same_locations():
    options = pool(20)
    assert pick_locations(options, random.Random(499)) == pick_locations(options, random.Random(499))


@pytest.mark.parametrize("options", [[], pool(4), pool(2) * 3])
def test_pool_with_fewer_than_five_distinct_locations_is_rejected(options):
    with pytest.raises(NotEnoughLocations, match="at least 5 locations"):
        pick_locations(options)

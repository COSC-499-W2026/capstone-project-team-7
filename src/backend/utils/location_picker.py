"""Pick the locations for one hunt from the pool of options."""

import random

LOCATIONS_PER_HUNT = 5


class NotEnoughLocations(ValueError):
    """The pool has fewer distinct locations than a hunt needs."""


def pick_locations(pool, rng=random):
    """Return LOCATIONS_PER_HUNT distinct locations from pool in a random order."""
    # A repeated id in the pool must not become a repeated location in the hunt.
    distinct = list(dict.fromkeys(pool))
    if len(distinct) < LOCATIONS_PER_HUNT:
        raise NotEnoughLocations(f"A hunt needs at least {LOCATIONS_PER_HUNT} locations")
    return rng.sample(distinct, LOCATIONS_PER_HUNT)

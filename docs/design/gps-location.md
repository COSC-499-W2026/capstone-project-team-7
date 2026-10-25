# Backend proximity validation

This change provides backend validation and target coordinate storage only.
The backend cannot obtain a phone's GPS directly; a future browser client must
request location permission and send a location reading with an answer.
GPS collection, student UI, maps, and teacher tracking are outside this change.

Migration `006_location_coordinates.sql` adds nullable latitude, longitude and
radius_metres to locations. Set all three together using measured campus data;
existing rows remain unconfigured. No campus coordinates or radius are guessed.

`proximity.py` provides validated `LocationReading` and `ProximityTarget` models
and `check_proximity`. It returns `within_radius`, `outside_radius`,
`stale_location`, or `inaccurate_location`. Readings older than 30 seconds or
more than 5 seconds in the future are rejected. Reported accuracy must be no
worse than the configured radius. Distance uses the Haversine formula and an
inclusive radius; this is an estimated position check, not proof of presence.

There is no submission endpoint yet. Its future handler must authenticate the
student, verify hunt ownership and active state, load the current target from
the database, reject unconfigured targets, and pass a fresh browser reading to
the validator. Never accept target coordinates or a successful client-side
distance check as authoritative. Only `within_radius` permits continuing to
photo verification and scoring. Browser coordinates can be spoofed; photo
verification remains necessary. Client timestamps also are not trusted proof
of freshness. Do not log coordinates or retain movement history by default.

Tests: `python3 -m pytest tests/backend`. Schema integration tests require
`TEST_DATABASE_URL`.

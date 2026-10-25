# Location and translated clue storage

Migration `003_locations_and_clues.sql` adds two tables:

- `locations`: a UUID, building name, and room number. A building and room number
  pair is unique; different buildings may share room numbers. Room numbers are
  text to support identifiers such as `102A`.
- `location_clues`: one translation per location and existing language code.
  `number_text` holds the room number written for speech in that language;
  `description_text` holds the description for the same location. Both are required.

Text fields must be nonempty and have no leading or trailing spaces. Deleting a
location removes its translations. Unknown locations and languages are rejected.
The tables contain no seeded campus data or generated translations.

The target database is PostgreSQL 17, which provides `gen_random_uuid()` as a
built-in function; no `pgcrypto` extension is required. Schema tests verify that
inserting a location without an ID generates a version 4 UUID.

The primary key indexes clues by location and language. There are currently no
queries filtering clues by language alone. If those are added, add an index on
`location_clues(language_code)` in a new numbered migration.

This migration is independent of difficulty definitions. Clue selection, audio,
GPS coordinates are added by migration `006_location_coordinates.sql`; see
[GPS location validation](gps-location.md). Sessions and management endpoints
remain future work.

## Picking locations for a hunt

`pick_locations(pool)` in `src/backend/utils/location_picker.py` returns 5 distinct
locations from a pool (the proposal's pool is 15–20 options), in random order.
Repeated ids in the pool are counted once, so a hunt never repeats a location. A pool
with fewer than 5 distinct locations raises `NotEnoughLocations`. Pass a seeded
`random.Random` as `rng` for a repeatable result in tests. The function does not read
the database; the endpoint that starts a hunt chooses the pool.

Apply with `python src/backend/migrate.py` using `DATABASE_URL`. Run schema tests
with `TEST_DATABASE_URL` set and `python -m pytest tests/backend/test_database.py`;
tests create a temporary schema and roll back each case.

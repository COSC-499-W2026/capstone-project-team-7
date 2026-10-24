# Demo target coordinates

This updater depends on PR #123 (demo locations and `utils.seed_locations`)
and PR #134 (latitude, longitude and radius_metres columns). Integrate both
before running it. It does not add schema or create target locations.

After applying migrations and seeding demo locations, run from `src/backend`:

```sh
python -m utils.seed_locations
python -m utils.seed_target_coordinates
```

The updater reads the existing `LOCATIONS` list directly, keeping one source
for the five demo targets and their coordinates: COM 316, LIB 312, ASC 130,
LIB 317 and ART 376. Each receives a 50-metre arrival radius. Running again
sets the same values without adding rows. A missing target rolls back the
whole batch; unrelated targets and translated clues are unchanged.

These are provisional demo coordinates, not confirmed final hunt targets.
The radius is a starting value for on-site testing. GPS checks the general
area; photo recognition must distinguish rooms and floors. The proximity
validator also requires reported accuracy no worse than the target radius.

Tests use a temporary table matching the dependency schema and synthetic
target records. Run with `TEST_DATABASE_URL` set:
`python -m pytest tests/backend/test_seed_target_coordinates.py`.

-- How many photos were sent for each skipped clue, in the same order as skipped_location_ids.
ALTER TABLE game_session_locations
    ADD COLUMN skipped_location_attempts INTEGER[] NOT NULL DEFAULT '{}';

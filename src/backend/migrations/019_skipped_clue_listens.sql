-- How many times each skipped clue was played, in the same order as skipped_location_ids.
ALTER TABLE game_session_locations
    ADD COLUMN skipped_location_listens INTEGER[] NOT NULL DEFAULT '{}';

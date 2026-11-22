ALTER TABLE game_session_locations
    ADD COLUMN skipped_location_ids UUID[] NOT NULL DEFAULT '{}';

-- How many times the student pressed play on this spot's clue audio. Existing spots start at 0, never blank.
ALTER TABLE game_session_locations ADD COLUMN listens INTEGER NOT NULL DEFAULT 0 CHECK (listens >= 0);

ALTER TABLE game_session_locations
ADD COLUMN audio_plays INTEGER NOT NULL DEFAULT 0 CHECK (audio_plays >= 0);

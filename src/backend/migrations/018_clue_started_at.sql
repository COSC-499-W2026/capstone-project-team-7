-- Existing games start their current clue timer when this migration is applied.
ALTER TABLE game_sessions ADD COLUMN clue_started_at TIMESTAMPTZ NOT NULL DEFAULT now();

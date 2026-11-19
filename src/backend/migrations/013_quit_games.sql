-- When the student quit the game; null if they haven't. A quit game is kept (not deleted),
-- isn't finished, and its points are set to 0.
ALTER TABLE game_sessions ADD COLUMN quit_at TIMESTAMPTZ;

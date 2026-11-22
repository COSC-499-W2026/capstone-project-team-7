-- Which assigned hunt a game was started from; null for normal games.
-- SET NULL so a teacher can still delete a hunt: its games are kept, just no longer linked.
ALTER TABLE game_sessions ADD COLUMN hunt_id UUID REFERENCES assigned_hunts (id) ON DELETE SET NULL;

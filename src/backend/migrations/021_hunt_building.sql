ALTER TABLE assigned_hunts ADD COLUMN building TEXT CHECK (building IS NULL OR difficulty = 'basic');

-- Keep the restriction for ongoing games if the teacher removes the assignment.
ALTER TABLE game_sessions ADD COLUMN hunt_building TEXT;

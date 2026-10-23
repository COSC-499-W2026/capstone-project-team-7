-- Games outlive a deleted student account so teacher records are kept.
CREATE TABLE game_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students (user_id) ON DELETE SET NULL,
    language_code VARCHAR(5) NOT NULL REFERENCES languages (code),
    difficulty TEXT NOT NULL CHECK (difficulty IN ('basic', 'advanced', 'expert')),
    current_position SMALLINT NOT NULL DEFAULT 1 CHECK (current_position BETWEEN 1 AND 5),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ
);

-- Attempts are tracked now because points will later depend on them.
CREATE TABLE game_session_locations (
    game_session_id UUID NOT NULL REFERENCES game_sessions (id) ON DELETE CASCADE,
    position SMALLINT NOT NULL CHECK (position BETWEEN 1 AND 5),
    location_id UUID NOT NULL REFERENCES locations (id),
    attempts INTEGER NOT NULL DEFAULT 0,
    found_at TIMESTAMPTZ,
    PRIMARY KEY (game_session_id, position),
    UNIQUE (game_session_id, location_id)
);

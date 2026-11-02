-- badge_id is an id from badges.py, so adding a badge needs no migration.
CREATE TABLE student_badges (
    student_id UUID NOT NULL REFERENCES students (user_id) ON DELETE CASCADE,
    badge_id TEXT NOT NULL,
    earned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (student_id, badge_id)
);

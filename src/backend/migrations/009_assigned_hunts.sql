-- Language is copied from the class so an assigned hunt keeps it if the class changes.
-- RESTRICT keeps hunts for teacher reference: a class with hunts can't be deleted.
CREATE TABLE assigned_hunts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id UUID NOT NULL REFERENCES classes (id) ON DELETE RESTRICT,
    language_code VARCHAR(5) NOT NULL REFERENCES languages (code),
    difficulty TEXT NOT NULL CHECK (difficulty IN ('basic', 'advanced', 'expert')),
    due_date DATE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX assigned_hunts_class_idx ON assigned_hunts (class_id);

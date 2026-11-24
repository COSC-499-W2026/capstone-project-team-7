-- icon_id is an id from profile_icons.py, so adding an icon needs no migration.
CREATE TABLE student_icons (
    student_id UUID NOT NULL REFERENCES students (user_id) ON DELETE CASCADE,
    icon_id TEXT NOT NULL,
    redeemed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (student_id, icon_id)
);

-- The foreign key means a student can only have an icon equipped if they own it.
ALTER TABLE students
    ADD COLUMN equipped_icon_id TEXT,
    ADD CONSTRAINT students_equipped_icon_owned
        FOREIGN KEY (user_id, equipped_icon_id) REFERENCES student_icons (student_id, icon_id);

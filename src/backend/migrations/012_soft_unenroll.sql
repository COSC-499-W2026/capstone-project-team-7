-- Removing a student from a class keeps the row, so teachers can still review their time in the class.
ALTER TABLE class_enrollments
    ADD COLUMN status VARCHAR(10) NOT NULL DEFAULT 'enrolled' CHECK (status IN ('enrolled', 'unenrolled')),
    ADD COLUMN unenrolled_at TIMESTAMPTZ,
    ADD CHECK ((status = 'unenrolled') = (unenrolled_at IS NOT NULL));

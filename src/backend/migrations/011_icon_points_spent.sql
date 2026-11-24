-- Points paid for each icon; a balance is points earned in games minus points spent. Free icons cost 0.
ALTER TABLE student_icons ADD COLUMN points_spent INTEGER NOT NULL DEFAULT 0 CHECK (points_spent >= 0);

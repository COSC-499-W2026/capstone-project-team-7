-- Who added the location, so only they can change it later. Seeded locations have none.
-- SET NULL keeps the location for every class using it if that teacher is deleted.
ALTER TABLE locations ADD COLUMN created_by UUID REFERENCES teachers (user_id) ON DELETE SET NULL;

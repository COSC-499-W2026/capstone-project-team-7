-- Who added the location, so only they can change it later. Seeded locations have none.
-- SET NULL keeps the location for every class using it if that teacher is deleted.
ALTER TABLE locations ADD COLUMN created_by UUID REFERENCES teachers (user_id) ON DELETE SET NULL;

-- Teacher-added clues are kept out of the base game, so badges can ignore them.
ALTER TABLE location_clues ADD COLUMN base_game BOOLEAN NOT NULL DEFAULT TRUE;

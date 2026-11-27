-- A teacher's own extra clips; the default clip for each location stays a file with no row.
-- SET NULL keeps a deleted teacher's clips playing in hunts that chose them.
CREATE TABLE location_clips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id UUID NOT NULL REFERENCES locations (id) ON DELETE CASCADE,
    language_code VARCHAR(5) NOT NULL REFERENCES languages (code),
    difficulty TEXT NOT NULL CHECK (difficulty IN ('basic', 'advanced', 'expert')),
    label TEXT NOT NULL CHECK (label = btrim(label) AND label <> ''),
    description TEXT CHECK (description IS NULL OR (description = btrim(description) AND description <> '')),
    created_by UUID REFERENCES teachers (user_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    retired_at TIMESTAMPTZ,
    UNIQUE (id, location_id)
);
CREATE INDEX location_clips_owner_idx ON location_clips (created_by, language_code);

-- The composite key stops a hunt choosing a clip recorded for a different room.
CREATE TABLE hunt_clips (
    hunt_id UUID NOT NULL REFERENCES assigned_hunts (id) ON DELETE CASCADE,
    location_id UUID NOT NULL REFERENCES locations (id),
    clip_id UUID NOT NULL,
    PRIMARY KEY (hunt_id, location_id),
    FOREIGN KEY (clip_id, location_id) REFERENCES location_clips (id, location_id) ON DELETE CASCADE
);

-- Null plays the default clip, so existing games are unchanged.
ALTER TABLE game_session_locations
    ADD COLUMN clip_id UUID REFERENCES location_clips (id) ON DELETE SET NULL;

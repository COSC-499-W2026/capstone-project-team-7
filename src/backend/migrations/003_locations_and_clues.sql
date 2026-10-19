CREATE TABLE locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    building TEXT NOT NULL CHECK (building = btrim(building) AND building <> ''),
    room_number TEXT NOT NULL CHECK (room_number = btrim(room_number) AND room_number <> ''),
    UNIQUE (building, room_number)
);

CREATE TABLE location_clues (
    location_id UUID NOT NULL REFERENCES locations (id) ON DELETE CASCADE,
    language_code VARCHAR(5) NOT NULL REFERENCES languages (code),
    number_text TEXT NOT NULL CHECK (number_text = btrim(number_text) AND number_text <> ''),
    description_text TEXT NOT NULL CHECK (description_text = btrim(description_text) AND description_text <> ''),
    PRIMARY KEY (location_id, language_code)
);

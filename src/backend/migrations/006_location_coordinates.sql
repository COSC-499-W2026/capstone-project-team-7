-- Existing locations remain unconfigured until campus coordinates are measured.
ALTER TABLE locations
    ADD COLUMN latitude DOUBLE PRECISION,
    ADD COLUMN longitude DOUBLE PRECISION,
    ADD COLUMN radius_metres DOUBLE PRECISION,
    ADD CONSTRAINT locations_coordinates_valid CHECK (
        (latitude IS NULL AND longitude IS NULL AND radius_metres IS NULL)
        OR
        (latitude IS NOT NULL AND longitude IS NOT NULL AND radius_metres IS NOT NULL
         AND latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180
         AND radius_metres > 0 AND radius_metres < 'Infinity'::DOUBLE PRECISION)
    );

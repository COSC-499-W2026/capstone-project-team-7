INSERT INTO languages (code, name) VALUES
    ('zh', 'Chinese'), ('fr', 'French'), ('de', 'German'),
    ('ja', 'Japanese'), ('ko', 'Korean'), ('es', 'Spanish');

-- Replay, attempt and timer defaults come from the proposal's examples.
-- Point values were unspecified: 10/20/30 are editable development defaults.
INSERT INTO difficulty_levels
    (code, name, max_audio_replays, max_photo_attempts, time_limit_seconds, points_per_location, clue_style)
VALUES
    ('basic', 'Basic', NULL, 3, 1800, 10, 'numbers'),
    ('advanced', 'Advanced', 3, 2, 1200, 20, 'numbers_and_description'),
    ('expert', 'Expert', 2, 1, 600, 30, 'description');

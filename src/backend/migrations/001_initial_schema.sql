-- Based on the Team 7 proposal: Firebase Auth owns credentials; PostgreSQL owns app data.
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    firebase_uid VARCHAR(128) NOT NULL UNIQUE CHECK (btrim(firebase_uid) <> ''),
    email TEXT NOT NULL CHECK (btrim(email) <> ''),
    username VARCHAR(50) NOT NULL CHECK (btrim(username) <> ''),
    first_name TEXT NOT NULL CHECK (btrim(first_name) <> ''),
    last_name TEXT NOT NULL CHECK (btrim(last_name) <> ''),
    role TEXT NOT NULL CHECK (role IN ('student', 'teacher', 'admin')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (id, role)
);
CREATE UNIQUE INDEX users_email_unique ON users (lower(email));
CREATE UNIQUE INDEX users_username_unique ON users (lower(username));

CREATE TABLE students (
    user_id UUID PRIMARY KEY,
    role TEXT NOT NULL DEFAULT 'student' CHECK (role = 'student'),
    student_number VARCHAR(30) NOT NULL UNIQUE CHECK (btrim(student_number) <> ''),
    equipped_icon_id UUID,
    FOREIGN KEY (user_id, role) REFERENCES users (id, role) ON DELETE CASCADE
);

CREATE TABLE teachers (
    user_id UUID PRIMARY KEY,
    role TEXT NOT NULL DEFAULT 'teacher' CHECK (role = 'teacher'),
    FOREIGN KEY (user_id, role) REFERENCES users (id, role) ON DELETE CASCADE
);

-- The signup API must check this list before granting a teacher role.
CREATE TABLE authorized_teacher_emails (
    email TEXT PRIMARY KEY CHECK (email = lower(btrim(email)) AND email <> ''),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE languages (
    code VARCHAR(5) PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE difficulty_levels (
    code TEXT PRIMARY KEY CHECK (code IN ('basic', 'advanced', 'expert')),
    name TEXT NOT NULL UNIQUE,
    max_audio_replays INTEGER CHECK (max_audio_replays >= 0), -- NULL means unlimited.
    max_photo_attempts INTEGER NOT NULL CHECK (max_photo_attempts BETWEEN 1 AND 3),
    time_limit_seconds INTEGER NOT NULL CHECK (time_limit_seconds > 0),
    points_per_location INTEGER NOT NULL CHECK (points_per_location > 0),
    clue_style TEXT NOT NULL CHECK (clue_style IN ('numbers', 'numbers_and_description', 'description'))
);

CREATE TABLE classes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID NOT NULL REFERENCES teachers (user_id) ON DELETE CASCADE,
    name TEXT NOT NULL CHECK (btrim(name) <> ''),
    language_code VARCHAR(5) NOT NULL REFERENCES languages (code),
    class_code VARCHAR(12) NOT NULL UNIQUE
        DEFAULT upper(substr(replace(gen_random_uuid()::text, '-', ''), 1, 12)),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (id, language_code)
);
CREATE INDEX classes_teacher_idx ON classes (teacher_id);

CREATE TABLE class_enrollments (
    class_id UUID NOT NULL REFERENCES classes (id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students (user_id) ON DELETE CASCADE,
    enrolled_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (class_id, student_id)
);
CREATE INDEX class_enrollments_student_idx ON class_enrollments (student_id);

CREATE TABLE student_languages (
    student_id UUID NOT NULL REFERENCES students (user_id) ON DELETE CASCADE,
    language_code VARCHAR(5) NOT NULL REFERENCES languages (code),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (student_id, language_code)
);

CREATE TABLE locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL CHECK (btrim(name) <> ''),
    building TEXT NOT NULL CHECK (btrim(building) <> ''),
    room_number TEXT NOT NULL CHECK (btrim(room_number) <> ''),
    latitude NUMERIC(9,6) NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude NUMERIC(9,6) NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    gps_radius_meters INTEGER NOT NULL DEFAULT 25 CHECK (gps_radius_meters > 0),
    is_active BOOLEAN NOT NULL DEFAULT true,
    UNIQUE (building, room_number)
);

CREATE TABLE location_clues (
    location_id UUID NOT NULL REFERENCES locations (id) ON DELETE CASCADE,
    language_code VARCHAR(5) NOT NULL REFERENCES languages (code),
    difficulty_code TEXT NOT NULL REFERENCES difficulty_levels (code),
    clue_text TEXT NOT NULL CHECK (btrim(clue_text) <> ''),
    audio_url TEXT NOT NULL CHECK (btrim(audio_url) <> ''),
    hint_text TEXT,
    vocabulary TEXT[] NOT NULL DEFAULT '{}',
    PRIMARY KEY (location_id, language_code, difficulty_code)
);

CREATE TABLE game_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students (user_id) ON DELETE CASCADE,
    class_id UUID,
    language_code VARCHAR(5) NOT NULL REFERENCES languages (code),
    difficulty_code TEXT NOT NULL REFERENCES difficulty_levels (code),
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'paused', 'completed', 'expired', 'abandoned', 'reset')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    paused_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    elapsed_seconds INTEGER NOT NULL DEFAULT 0 CHECK (elapsed_seconds >= 0),
    time_limit_seconds INTEGER NOT NULL CHECK (time_limit_seconds > 0),
    -- Snapshot limits/scoring so later difficulty edits do not alter an existing hunt.
    max_audio_replays INTEGER CHECK (max_audio_replays >= 0),
    max_photo_attempts INTEGER NOT NULL CHECK (max_photo_attempts BETWEEN 1 AND 3),
    points_per_location INTEGER NOT NULL CHECK (points_per_location > 0),
    FOREIGN KEY (class_id, student_id)
        REFERENCES class_enrollments (class_id, student_id) ON DELETE SET NULL (class_id),
    FOREIGN KEY (class_id, language_code)
        REFERENCES classes (id, language_code) ON DELETE SET NULL (class_id),
    UNIQUE (id, language_code, difficulty_code),
    CHECK ((status = 'paused') = (paused_at IS NOT NULL)),
    CHECK ((status IN ('completed', 'expired', 'abandoned', 'reset')) = (ended_at IS NOT NULL)),
    CHECK (ended_at IS NULL OR ended_at >= started_at)
);
CREATE INDEX game_sessions_student_history_idx ON game_sessions (student_id, started_at DESC);
CREATE INDEX game_sessions_class_idx ON game_sessions (class_id) WHERE class_id IS NOT NULL;
CREATE UNIQUE INDEX one_open_session_per_student ON game_sessions (student_id)
    WHERE status IN ('active', 'paused');

CREATE TABLE session_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    location_id UUID NOT NULL,
    language_code VARCHAR(5) NOT NULL,
    difficulty_code TEXT NOT NULL,
    position SMALLINT NOT NULL CHECK (position BETWEEN 1 AND 5),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'skipped')),
    audio_replay_count INTEGER NOT NULL DEFAULT 0 CHECK (audio_replay_count >= 0),
    consecutive_failures INTEGER NOT NULL DEFAULT 0 CHECK (consecutive_failures >= 0),
    hints_shown INTEGER NOT NULL DEFAULT 0 CHECK (hints_shown >= 0),
    points_awarded INTEGER NOT NULL DEFAULT 0 CHECK (points_awarded >= 0),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    FOREIGN KEY (session_id, language_code, difficulty_code)
        REFERENCES game_sessions (id, language_code, difficulty_code) ON DELETE CASCADE,
    FOREIGN KEY (location_id, language_code, difficulty_code)
        REFERENCES location_clues (location_id, language_code, difficulty_code),
    UNIQUE (session_id, position),
    UNIQUE (session_id, location_id),
    CHECK (status = 'completed' OR points_awarded = 0),
    CHECK ((status IN ('completed', 'skipped')) = (finished_at IS NOT NULL)),
    CHECK (finished_at IS NULL OR (started_at IS NOT NULL AND finished_at >= started_at))
);

CREATE TABLE location_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_location_id UUID NOT NULL REFERENCES session_locations (id) ON DELETE CASCADE,
    attempt_number SMALLINT NOT NULL CHECK (attempt_number BETWEEN 1 AND 3),
    image_url TEXT NOT NULL CHECK (btrim(image_url) <> ''),
    latitude NUMERIC(9,6) NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude NUMERIC(9,6) NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    gps_accuracy_meters NUMERIC CHECK (gps_accuracy_meters >= 0),
    recognized_text TEXT,
    gps_passed BOOLEAN NOT NULL,
    image_passed BOOLEAN NOT NULL,
    succeeded BOOLEAN GENERATED ALWAYS AS (gps_passed AND image_passed) STORED,
    failure_reason TEXT,
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (session_location_id, attempt_number)
);

CREATE TABLE badges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    language_code VARCHAR(5) NOT NULL REFERENCES languages (code),
    difficulty_code TEXT REFERENCES difficulty_levels (code),
    required_locations INTEGER NOT NULL CHECK (required_locations > 0),
    image_url TEXT
);

CREATE TABLE student_badges (
    student_id UUID NOT NULL REFERENCES students (user_id) ON DELETE CASCADE,
    badge_id UUID NOT NULL REFERENCES badges (id),
    earned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (student_id, badge_id)
);

CREATE TABLE profile_icons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    image_url TEXT NOT NULL CHECK (btrim(image_url) <> ''),
    point_cost INTEGER NOT NULL CHECK (point_cost >= 0),
    is_active BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE student_icons (
    student_id UUID NOT NULL REFERENCES students (user_id) ON DELETE CASCADE,
    icon_id UUID NOT NULL REFERENCES profile_icons (id),
    points_spent INTEGER NOT NULL CHECK (points_spent >= 0),
    redeemed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (student_id, icon_id)
);
-- A student can only equip an icon they own; NULL selects the UI's default avatar.
ALTER TABLE students ADD CONSTRAINT equipped_icon_owned
    FOREIGN KEY (user_id, equipped_icon_id) REFERENCES student_icons (student_id, icon_id)
    DEFERRABLE INITIALLY IMMEDIATE;

CREATE TABLE session_debriefs (
    session_id UUID PRIMARY KEY REFERENCES game_sessions (id) ON DELETE CASCADE,
    summary TEXT NOT NULL CHECK (btrim(summary) <> ''),
    struggled_vocabulary TEXT[] NOT NULL DEFAULT '{}',
    suggested_vocabulary TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE chat_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students (user_id) ON DELETE CASCADE,
    language_code VARCHAR(5) NOT NULL REFERENCES languages (code),
    difficulty_code TEXT NOT NULL REFERENCES difficulty_levels (code),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX chat_conversations_student_idx ON chat_conversations (student_id, created_at DESC);

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES chat_conversations (id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL CHECK (btrim(content) <> ''),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX chat_messages_conversation_idx ON chat_messages (conversation_id, created_at, id);

-- Views avoid independently stored totals/ranks drifting out of sync.
-- Completed sessions alone contribute to the permanent score and wallet.
CREATE VIEW student_point_totals AS
WITH earned AS (
    SELECT gs.student_id, sum(sl.points_awarded) AS total_points
    FROM game_sessions gs
    JOIN session_locations sl ON sl.session_id = gs.id
    WHERE gs.status = 'completed' AND sl.status = 'completed'
    GROUP BY gs.student_id
), spent AS (
    SELECT student_id, sum(points_spent) AS spent_points
    FROM student_icons GROUP BY student_id
)
SELECT s.user_id AS student_id,
    coalesce(e.total_points, 0)::bigint AS total_points,
    coalesce(p.spent_points, 0)::bigint AS spent_points,
    (coalesce(e.total_points, 0) - coalesce(p.spent_points, 0))::bigint AS available_points
FROM students s
LEFT JOIN earned e ON e.student_id = s.user_id
LEFT JOIN spent p ON p.student_id = s.user_id;

CREATE VIEW global_leaderboard AS
SELECT p.student_id, u.username, s.equipped_icon_id, p.total_points,
    dense_rank() OVER (ORDER BY p.total_points DESC) AS rank
FROM student_point_totals p
JOIN users u ON u.id = p.student_id
JOIN students s ON s.user_id = p.student_id;

CREATE VIEW class_student_progress AS
SELECT ce.class_id, ce.student_id, u.username, s.equipped_icon_id,
    coalesce(sum(sl.points_awarded) FILTER (
        WHERE gs.status = 'completed' AND sl.status = 'completed'), 0)::bigint AS total_points,
    count(sl.id) FILTER (WHERE sl.started_at IS NOT NULL) AS levels_played,
    count(sl.id) FILTER (WHERE sl.status = 'completed') AS levels_completed
FROM class_enrollments ce
JOIN users u ON u.id = ce.student_id
JOIN students s ON s.user_id = ce.student_id
LEFT JOIN game_sessions gs ON gs.class_id = ce.class_id AND gs.student_id = ce.student_id
LEFT JOIN session_locations sl ON sl.session_id = gs.id
GROUP BY ce.class_id, ce.student_id, u.username, s.equipped_icon_id;

CREATE VIEW class_leaderboard AS
SELECT *, dense_rank() OVER (PARTITION BY class_id ORDER BY total_points DESC) AS rank
FROM class_student_progress;

-- Backend-only helper. Serialize redemptions for a student to prevent overspending.
-- Always call with the authenticated student's ID; never expose direct SQL access.
CREATE FUNCTION redeem_profile_icon(p_student_id UUID, p_icon_id UUID)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE
    cost INTEGER;
    balance BIGINT;
BEGIN
    PERFORM 1 FROM students WHERE user_id = p_student_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Student does not exist' USING ERRCODE = '23503';
    END IF;
    SELECT point_cost INTO cost FROM profile_icons WHERE id = p_icon_id AND is_active FOR SHARE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Icon is unavailable' USING ERRCODE = '23503';
    END IF;
    IF EXISTS (SELECT 1 FROM student_icons WHERE student_id = p_student_id AND icon_id = p_icon_id) THEN
        RAISE EXCEPTION 'Icon already owned' USING ERRCODE = '23505';
    END IF;
    SELECT available_points INTO balance FROM student_point_totals WHERE student_id = p_student_id;
    IF balance < cost THEN
        RAISE EXCEPTION 'Insufficient points' USING ERRCODE = '23514';
    END IF;
    INSERT INTO student_icons (student_id, icon_id, points_spent) VALUES (p_student_id, p_icon_id, cost);
END;
$$;

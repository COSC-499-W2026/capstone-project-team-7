-- Credentials are managed by the backend; password holds an encoded salted hash.
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL CHECK (email = btrim(email) AND email <> ''),
    username VARCHAR(50) NOT NULL CHECK (username = btrim(username) AND username <> ''),
    password TEXT NOT NULL CHECK (btrim(password) <> ''),
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
    FOREIGN KEY (user_id, role) REFERENCES users (id, role) ON DELETE CASCADE
);
CREATE TABLE teachers (
    user_id UUID PRIMARY KEY,
    role TEXT NOT NULL DEFAULT 'teacher' CHECK (role = 'teacher'),
    FOREIGN KEY (user_id, role) REFERENCES users (id, role) ON DELETE CASCADE
);

-- Signup must check this allowlist before granting the teacher role.
CREATE TABLE authorized_teacher_emails (
    email TEXT PRIMARY KEY CHECK (email = lower(btrim(email)) AND email <> ''),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE languages (
    code VARCHAR(5) PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
INSERT INTO languages (code, name) VALUES
    ('zh', 'Chinese'), ('fr', 'French'), ('de', 'German'),
    ('ja', 'Japanese'), ('ko', 'Korean'), ('es', 'Spanish');

CREATE TABLE classes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID NOT NULL REFERENCES teachers (user_id) ON DELETE CASCADE,
    name TEXT NOT NULL CHECK (btrim(name) <> ''),
    language_code VARCHAR(5) NOT NULL REFERENCES languages (code),
    class_code VARCHAR(12) NOT NULL UNIQUE
        DEFAULT upper(substr(replace(gen_random_uuid()::text, '-', ''), 1, 12)),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
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
    PRIMARY KEY (student_id, language_code)
);

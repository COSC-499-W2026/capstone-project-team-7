CREATE TABLE password_reset_email_limits (
    user_id UUID PRIMARY KEY REFERENCES users (id) ON DELETE CASCADE,
    requested_at TIMESTAMPTZ[] NOT NULL CHECK (cardinality(requested_at) BETWEEN 1 AND 5)
);

INSERT INTO password_reset_email_limits (user_id, requested_at)
SELECT user_id, ARRAY[created_at] FROM password_reset_tokens
WHERE created_at > now() - interval '1 hour';

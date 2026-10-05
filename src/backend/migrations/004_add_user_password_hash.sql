-- All account types share users, so password storage belongs here.
-- The authentication code must supply a salted password hash, never plaintext.
ALTER TABLE users ADD COLUMN password_hash TEXT;

-- Locally authenticated accounts do not need a Firebase identity.
-- Preserve existing Firebase IDs and their uniqueness for legacy accounts.
ALTER TABLE users ALTER COLUMN firebase_uid DROP NOT NULL;

-- Enforce a hash on new inserts/updates while retaining existing accounts.
-- Legacy users must set/reset a password before their account row is updated.
-- Once every legacy account has a hash, validate this constraint in a new migration.
ALTER TABLE users ADD CONSTRAINT users_password_hash_required
    CHECK (password_hash IS NOT NULL AND btrim(password_hash) <> '') NOT VALID;

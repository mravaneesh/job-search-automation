-- Phase 5 schema: multi-user auth + per-user profiles.
-- Auth.js (NextAuth) tables follow the @auth/pg-adapter required schema EXACTLY
-- (SERIAL int ids, quoted camelCase columns) — do not rename these.

CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255),
    email           VARCHAR(255),
    "emailVerified" TIMESTAMPTZ,
    image           TEXT
);

CREATE TABLE IF NOT EXISTS accounts (
    id                  SERIAL PRIMARY KEY,
    "userId"            INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type                VARCHAR(255) NOT NULL,
    provider            VARCHAR(255) NOT NULL,
    "providerAccountId" VARCHAR(255) NOT NULL,
    refresh_token       TEXT,
    access_token        TEXT,
    expires_at          BIGINT,
    id_token            TEXT,
    scope               TEXT,
    session_state       TEXT,
    token_type          TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
    id             SERIAL PRIMARY KEY,
    "userId"       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires        TIMESTAMPTZ NOT NULL,
    "sessionToken" VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS verification_token (
    identifier TEXT NOT NULL,
    expires    TIMESTAMPTZ NOT NULL,
    token      TEXT NOT NULL,
    PRIMARY KEY (identifier, token)
);

-- --- Per-user profile (built by the onboarding wizard) --------------------
CREATE TABLE IF NOT EXISTS profiles (
    user_id             INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    full_name           TEXT,
    target_roles        TEXT[] NOT NULL DEFAULT '{}',   -- android / backend / ai_ml
    experience_years    NUMERIC NOT NULL DEFAULT 0,
    skills              TEXT[] NOT NULL DEFAULT '{}',
    preferred_locations TEXT[] NOT NULL DEFAULT '{}',
    remote_only         BOOLEAN NOT NULL DEFAULT FALSE,
    min_salary          NUMERIC,
    salary_currency     TEXT DEFAULT 'INR',
    work_authorization  TEXT,                            -- e.g. "India citizen", "needs visa"
    resume_filename     TEXT,
    resume_text         TEXT,
    onboarded           BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- --- Make application tracking per-user ------------------------------------
ALTER TABLE applications ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;
-- Legacy single-user rows (no user) are not part of the multi-user product.
DELETE FROM applications WHERE user_id IS NULL;
ALTER TABLE applications DROP CONSTRAINT IF EXISTS applications_job_key;
CREATE UNIQUE INDEX IF NOT EXISTS applications_user_job_key ON applications(user_id, job_id);
CREATE INDEX IF NOT EXISTS idx_applications_user ON applications(user_id);

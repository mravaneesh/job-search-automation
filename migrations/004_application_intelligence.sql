-- Phase 4 schema: application intelligence. Strictly ADDITIVE — extends jobs
-- and companies with new columns and adds new tables. Nothing existing is
-- dropped or altered in a breaking way.

-- --- Salary intelligence (additive columns on jobs) -----------------------
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary_min          NUMERIC;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary_max          NUMERIC;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS currency            TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS compensation_source TEXT;

-- --- Company tiering (additive column on companies) ------------------------
ALTER TABLE companies ADD COLUMN IF NOT EXISTS tier TEXT;  -- tier1 / tier2 / tier3

-- --- Master resumes + version tracking ------------------------------------
CREATE TABLE IF NOT EXISTS resumes (
    id            BIGSERIAL PRIMARY KEY,
    role_category TEXT NOT NULL,                 -- android / backend / ai_ml
    name          TEXT NOT NULL,
    version       INT  NOT NULL DEFAULT 1,
    focus_skills  TEXT[] NOT NULL DEFAULT '{}',
    themes        TEXT[] NOT NULL DEFAULT '{}',
    file_path     TEXT,
    notes         TEXT,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT resumes_role_name_version_key UNIQUE (role_category, name, version)
);

-- --- Recruiters -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS recruiters (
    id              BIGSERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    company         TEXT,
    linkedin_url    TEXT,
    email           TEXT,
    contacted_at    TIMESTAMPTZ,
    response_status TEXT NOT NULL DEFAULT 'NOT_CONTACTED',
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- --- Applications (one per job) -------------------------------------------
CREATE TABLE IF NOT EXISTS applications (
    id               BIGSERIAL PRIMARY KEY,
    job_id           BIGINT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    status           TEXT NOT NULL DEFAULT 'SAVED',
    application_date DATE,
    recruiter_id     BIGINT REFERENCES recruiters(id) ON DELETE SET NULL,
    resume_id        BIGINT REFERENCES resumes(id) ON DELETE SET NULL,
    resume_version   INT,
    notes            TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_update      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT applications_job_key UNIQUE (job_id)
);

CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);

-- --- Generated artifacts (cover letters, outreach, recommendations) --------
-- Deduped by (job_id, kind, input_hash) so identical inputs never regenerate.
CREATE TABLE IF NOT EXISTS application_artifacts (
    id           BIGSERIAL PRIMARY KEY,
    job_id       BIGINT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    kind         TEXT NOT NULL,                 -- cover_letter / linkedin / recruiter_email / follow_up / recommendation / bullets
    content      TEXT NOT NULL,
    generated_by TEXT NOT NULL,                 -- 'deterministic' or model id
    input_hash   TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT application_artifacts_key UNIQUE (job_id, kind, input_hash)
);

CREATE INDEX IF NOT EXISTS idx_artifacts_job ON application_artifacts(job_id, kind);

-- --- LLM token ledger for the daily budget guard --------------------------
CREATE TABLE IF NOT EXISTS generation_runs (
    id            BIGSERIAL PRIMARY KEY,
    started_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    kind          TEXT,
    input_tokens  INT NOT NULL DEFAULT 0,
    output_tokens INT NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_generation_runs_started ON generation_runs(started_at);

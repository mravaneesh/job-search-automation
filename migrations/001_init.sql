-- Phase 1 schema: companies, jobs, collection_runs.
-- Idempotent collection is enforced via UNIQUE(fingerprint) on jobs.

CREATE TABLE IF NOT EXISTS companies (
    id             BIGSERIAL PRIMARY KEY,
    name           TEXT NOT NULL UNIQUE,
    category       TEXT,                       -- global / india_product / unicorn / ai / backend
    primary_source TEXT,                        -- greenhouse / lever / ashby / career_page / <aggregator>
    source_token   TEXT,                        -- board token / handle for the source
    status         TEXT NOT NULL DEFAULT 'pending',
    is_active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS jobs (
    id              BIGSERIAL PRIMARY KEY,
    company_id      BIGINT REFERENCES companies(id),
    company_name    TEXT NOT NULL,
    role_category   TEXT NOT NULL,              -- android / ai_ml / backend
    title           TEXT NOT NULL,
    source          TEXT NOT NULL,              -- greenhouse / lever / ashby / career_page / linkedin ...
    source_priority INT  NOT NULL DEFAULT 100,  -- lower = higher priority for dedup conflict resolution
    source_job_id   TEXT,                        -- stable id from the source, when available
    url             TEXT NOT NULL,
    location        TEXT,
    experience      TEXT,                        -- parsed level / years, when available
    employment_type TEXT,                        -- full-time / contract / intern ...
    description     TEXT,                        -- plain-text job description
    skills          TEXT[] NOT NULL DEFAULT '{}',
    created_date    DATE,                        -- the posting's own created/posted date
    discovered_date TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    status          TEXT NOT NULL DEFAULT 'open',-- open / stale
    fingerprint     TEXT NOT NULL,               -- cross-source dedup key
    raw             JSONB,                        -- original payload, for audit / re-normalization
    CONSTRAINT jobs_fingerprint_key UNIQUE (fingerprint)
);

CREATE INDEX IF NOT EXISTS idx_jobs_company        ON jobs(company_id);
CREATE INDEX IF NOT EXISTS idx_jobs_role           ON jobs(role_category);
CREATE INDEX IF NOT EXISTS idx_jobs_discovered     ON jobs(discovered_date);
CREATE INDEX IF NOT EXISTS idx_jobs_source_jobid   ON jobs(source, source_job_id);
CREATE INDEX IF NOT EXISTS idx_jobs_skills_gin     ON jobs USING GIN (skills);

CREATE TABLE IF NOT EXISTS collection_runs (
    id            BIGSERIAL PRIMARY KEY,
    started_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at   TIMESTAMPTZ,
    source        TEXT,
    company_name  TEXT,
    jobs_found    INT NOT NULL DEFAULT 0,
    jobs_inserted INT NOT NULL DEFAULT 0,
    jobs_updated  INT NOT NULL DEFAULT 0,
    status        TEXT,                          -- success / partial / failed
    error         TEXT
);

CREATE INDEX IF NOT EXISTS idx_runs_started ON collection_runs(started_at);

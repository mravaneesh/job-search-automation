-- Phase 2 schema: scoring output + token-budget accounting.
-- Collectors and the jobs table from Phase 1 are unchanged.

CREATE TABLE IF NOT EXISTS job_scores (
    id                   BIGSERIAL PRIMARY KEY,
    job_id               BIGINT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    role_category        TEXT NOT NULL,               -- android / backend / ai_ml
    match_score          INT  NOT NULL,               -- 0-100 overall fit
    skill_score          INT  NOT NULL,
    experience_score     INT  NOT NULL,
    location_score       INT  NOT NULL,
    seniority_score      INT  NOT NULL,
    company_score        INT  NOT NULL,
    interview_likelihood INT  NOT NULL,                -- 0-100, deterministic or LLM-refined
    matched_skills       TEXT[] NOT NULL DEFAULT '{}',
    missing_skills       TEXT[] NOT NULL DEFAULT '{}',
    priority             TEXT NOT NULL,                -- HIGH / MEDIUM / LOW
    scorer_version       INT  NOT NULL,                -- bumped when scoring logic changes
    scored_by            TEXT NOT NULL,                -- 'deterministic' or the model id
    input_hash           TEXT NOT NULL,                -- fingerprint of scoring inputs (re-score guard)
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT job_scores_job_key UNIQUE (job_id)
);

CREATE INDEX IF NOT EXISTS idx_job_scores_priority ON job_scores(priority);
CREATE INDEX IF NOT EXISTS idx_job_scores_match    ON job_scores(match_score);
CREATE INDEX IF NOT EXISTS idx_job_scores_role     ON job_scores(role_category);

-- One row per scoring run; the token columns drive the daily budget guard.
CREATE TABLE IF NOT EXISTS scoring_runs (
    id               BIGSERIAL PRIMARY KEY,
    started_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at      TIMESTAMPTZ,
    jobs_considered  INT NOT NULL DEFAULT 0,
    jobs_scored      INT NOT NULL DEFAULT 0,
    llm_calls        INT NOT NULL DEFAULT 0,
    input_tokens     INT NOT NULL DEFAULT 0,
    output_tokens    INT NOT NULL DEFAULT 0,
    status           TEXT,
    error            TEXT
);

CREATE INDEX IF NOT EXISTS idx_scoring_runs_started ON scoring_runs(started_at);

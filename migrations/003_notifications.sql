-- Phase 3 schema: notification dedup state.
-- One row per job records the last-notified state, so daily runs only notify
-- on new jobs, score changes, or newly high-priority matches — never repeats.

CREATE TABLE IF NOT EXISTS notifications (
    job_id      BIGINT PRIMARY KEY REFERENCES jobs(id) ON DELETE CASCADE,
    fingerprint TEXT NOT NULL,            -- "<priority>:<match_score>" at last notify
    priority    TEXT NOT NULL,
    match_score INT  NOT NULL,
    notified_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_notifications_notified ON notifications(notified_at);

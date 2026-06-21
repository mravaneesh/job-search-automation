-- Evolve the existing recruiters table (created outside migrations) to support
-- per-user outreach tracking with the additional fields we need.

-- Add user ownership (nullable first so no existing rows break)
ALTER TABLE recruiters ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;

-- Add recruiter job title
ALTER TABLE recruiters ADD COLUMN IF NOT EXISTS title TEXT;

-- Rename company -> company_name if the old column exists
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='recruiters' AND column_name='company'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='recruiters' AND column_name='company_name'
  ) THEN
    ALTER TABLE recruiters RENAME COLUMN company TO company_name;
  END IF;
END $$;

-- Rename response_status -> outreach_status if the old column exists
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='recruiters' AND column_name='response_status'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='recruiters' AND column_name='outreach_status'
  ) THEN
    ALTER TABLE recruiters RENAME COLUMN response_status TO outreach_status;
  END IF;
END $$;

-- Rename contacted_at -> last_contacted_at if the old column exists
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='recruiters' AND column_name='contacted_at'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='recruiters' AND column_name='last_contacted_at'
  ) THEN
    ALTER TABLE recruiters RENAME COLUMN contacted_at TO last_contacted_at;
  END IF;
END $$;

-- Make name nullable (was NOT NULL in the old schema; we allow anonymous entries)
ALTER TABLE recruiters ALTER COLUMN name DROP NOT NULL;

-- Normalise the default value for outreach_status to lowercase
ALTER TABLE recruiters ALTER COLUMN outreach_status SET DEFAULT 'not_contacted';

-- Update any old-style uppercase values
UPDATE recruiters SET outreach_status = lower(outreach_status) WHERE outreach_status = outreach_status;

CREATE INDEX IF NOT EXISTS idx_recruiters_user    ON recruiters(user_id);
CREATE INDEX IF NOT EXISTS idx_recruiters_company ON recruiters(company_name);

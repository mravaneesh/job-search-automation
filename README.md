# Job Search Automation — Phase 1

Production-grade, **deterministic** job collection and storage for three target
roles — **Android**, **Backend**, and **AI/ML** engineering — across a curated
set of companies and job sources.

> **Phase 1 scope:** reliable job collection + storage only.
> No AI scoring, no resume generation, no notifications.
>
> **Hard rule:** an LLM is **never** used to browse websites, read HTML, or
> extract job information. All collection, parsing, classification, and skill
> extraction is deterministic code. Sources are consumed via public JSON APIs
> wherever possible; Playwright is used only where no API exists.

---

## Architecture

```
Company Registry  ─▶  Collectors  ─▶  Normalizer  ─▶  Dedup Engine  ─▶  PostgreSQL
(config/*.yaml)       (per source)    raw → Job        fingerprint        companies
                                      role + skills    + priority         jobs
                                                                          collection_runs
```

1. **Registry** (`config/companies.yaml`) — the single source of truth. Each
   company is mapped to a source (`greenhouse` / `lever` / `ashby` /
   `career_page`) and a `status` (`implemented` / `pending`). It doubles as a
   coverage map — no silently-broken collectors.
2. **Collectors** (`src/jobsearch/collectors/`) — one per source. ATS collectors
   hit public JSON APIs. The `career_page` collector is config-driven JSON.
   Aggregators (LinkedIn/Indeed/Naukri/Wellfound) use Playwright. **Parsing is a
   pure function over a payload**, separated from fetching, so it is unit-tested
   with fixtures — no network, no browser.
3. **Normalizer** (`src/jobsearch/normalize/`) — converts a `RawJob` into the
   canonical `Job`: strips HTML to text deterministically, classifies the role
   (dropping anything outside the three targets), extracts skills from a curated
   dictionary, and parses experience.
4. **Dedup engine** (`src/jobsearch/dedup/`) — a content fingerprint over
   company + normalized title + location collapses the same role seen on
   multiple sources. On conflict the higher-priority source wins (career page >
   greenhouse > lever > ashby > … > naukri).
5. **Storage** (`src/jobsearch/db/`) — idempotent upsert keyed on the
   fingerprint. Re-runs update `last_seen_at`; every run is recorded in
   `collection_runs`. Original payloads are stored in `jobs.raw` so
   normalization can be re-run later without re-fetching.

### Why APIs first
- **Greenhouse:** `https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true`
- **Lever:** `https://api.lever.co/v0/postings/{token}?mode=json`
- **Ashby:** `https://api.ashbyhq.com/posting-api/job-board/{token}?includeCompensation=true`

These return clean, structured JSON — fast, stable, and ToS-friendly. The
Playwright aggregators are intentionally **best-effort** and marked `pending`:
they are brittle and subject to anti-bot defences. Promote a target to
`implemented` only after verifying its token/endpoint.

## Folder structure

```
config/            companies.yaml (registry), roles.yaml, skills.yaml
migrations/        001_init.sql (plain versioned SQL)
src/jobsearch/
  collectors/      base, greenhouse, lever, ashby, career_page, aggregators, registry
  normalize/       text (html→text), roles, skills, normalizer
  dedup/           fingerprint
  db/              connection, migrate, repository
  registry/        loader (+ validation)
  pipeline.py      orchestration
  cli.py           `python -m jobsearch ...`
tests/             pure parser/classifier/dedup tests + db tests (fixtures)
```

## Database schema

`companies`, `jobs`, `collection_runs` (see `migrations/001_init.sql`). The
`jobs` table stores every field in the required data model: company, role,
source, url, location, experience, employment type, description, skills,
created date, discovered date — plus `fingerprint` (dedup), `status`
(open/stale), `source_priority`, and `raw` (JSONB, for audit / re-normalization).

## Setup

### Local (Python 3.11+)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt && pip install -e .
playwright install chromium          # only needed for aggregator collectors

cp .env.example .env                  # then export the vars, or use your own
docker compose up -d db               # start PostgreSQL
export DATABASE_URL=postgresql://jobsearch:jobsearch@localhost:5432/jobsearch

python -m jobsearch migrate           # apply schema
python -m jobsearch list-targets      # show the coverage map
python -m jobsearch collect --dry-run # collect without writing
python -m jobsearch collect --source greenhouse --company Stripe
```

### CLI commands

| Command | Description |
|---|---|
| `migrate` | apply database migrations |
| `collect` | collect jobs; flags: `--source`, `--company` (repeatable), `--dry-run`, `--limit` |
| `renormalize` | re-run normalization over stored `raw` payloads (after tuning roles/skills) |
| `list-targets` | print the registry coverage map |

### Docker

```bash
docker compose up --build     # starts Postgres + runs a dry-run collection
```

### Tests

```bash
pytest                        # parser/classifier/dedup tests run with no DB
DATABASE_URL=... pytest       # also runs the repository (db-marked) tests
ruff check src tests          # lint
```

CI (`.github/workflows/ci.yml`) runs ruff + pytest against a Postgres service.
Collector tests use saved JSON/HTML fixtures — **no live network calls in CI**.

## Tuning (no code changes)

- **Roles:** edit `config/roles.yaml` (keywords + priority).
- **Skills:** edit `config/skills.yaml` (canonical → aliases).
- **Targets:** edit `config/companies.yaml`, then re-run `collect`.

After tuning roles/skills, run `renormalize` to re-classify existing rows from
their stored `raw` payloads without hitting any source again.

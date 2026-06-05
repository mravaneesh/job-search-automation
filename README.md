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

---

# Phase 2 — Scoring Engine

Evaluates collected jobs against a candidate profile and assigns each a match
score, missing skills, and a HIGH/MEDIUM/LOW priority.

> **Deterministic by default.** Skill, experience, location, seniority, and
> company-quality scoring is pure code — **zero tokens**. An LLM optionally
> refines only the *interview-likelihood* dimension, receives **structured JSON
> only** (never HTML or job descriptions), is batched, prompt-cached, and capped
> by a daily token budget. Target: **< 20k tokens/day** — met by construction.

## How scoring works

```
open jobs ─▶ re-score guard ─▶ deterministic engine ─▶ [optional LLM refine] ─▶ job_scores
            (input hash +        6 sub-scores →           interview-likelihood
             scorer_version)     weighted match score      via structured JSON
```

1. **Re-score guard** — only **new or changed** jobs are scored. Each score row
   stores an `input_hash` (a fingerprint of the job's scoring-relevant fields)
   and the `scorer_version`. A job is re-scored only if it is unscored, its
   inputs changed, or the scorer version bumped. Unchanged jobs are skipped.
2. **Deterministic engine** (`src/jobsearch/scoring/engine.py`) computes six
   0-100 dimensions — **skill match**, **experience match**, **location match**,
   **seniority**, **company quality**, and a baseline **interview likelihood** —
   combines them by configured weights, applies a role-priority multiplier
   (Android primary > Backend secondary > AI/ML stretch), and maps the result to
   a priority. It also emits `matched_skills` and `missing_skills`.
3. **Optional LLM refinement** (`src/jobsearch/scoring/llm.py`) — when
   `use_llm: true` in `config/scoring.yaml` **and** `ANTHROPIC_API_KEY` is set,
   Claude re-estimates the interview-likelihood dimension from a compact JSON
   payload (role, title, company tier, location, matched/missing skills, the
   deterministic sub-scores). The stable system prompt (profile + rubric) is
   prompt-cached; thinking is disabled and output is constrained to a small JSON
   schema; batches are capped by `max_tokens_per_day`. Falls back to
   deterministic scoring if the key is missing, the budget is exhausted, or a
   call fails.

## Profile & tuning (no code changes)

- **Profile:** `config/profile.yaml` — experience, role priorities, preferred
  locations, skills per role.
- **Scoring:** `config/scoring.yaml` — weights, priority thresholds, role-fit
  multipliers, company-quality tiers, `scorer_version`, and the LLM toggle/model/
  budget. Bump `scorer_version` to force a full re-score after a logic change.

## Run it

```bash
python -m jobsearch migrate              # applies 002_scoring.sql
python -m jobsearch score                # score new/changed jobs (deterministic)
python -m jobsearch score --dry-run      # score without writing
python -m jobsearch score --rescore-all  # re-score every open job
python -m jobsearch score --llm          # force-enable LLM refinement (needs ANTHROPIC_API_KEY)
python -m jobsearch score --no-llm       # force-disable LLM refinement
```

| Output column (`job_scores`) | Meaning |
|---|---|
| `match_score` | 0-100 overall fit |
| `priority` | HIGH / MEDIUM / LOW |
| `missing_skills` | job-required skills the candidate lacks |
| `matched_skills` | overlap with the profile |
| `scored_by` | `deterministic` or the model id |

## Tokens & cost

The default run uses **0 tokens** (deterministic). With `--llm`, every run is
recorded in `scoring_runs` with its token usage; the next run sums today's usage
and stops calling the model once `max_tokens_per_day` is reached. Because only
new/changed jobs are scored, only the stable system prompt is cached, and only
structured JSON is sent, steady-state usage stays well under 20k/day. The model
defaults to `claude-opus-4-8`; set `model: claude-haiku-4-5` in `scoring.yaml`
for the cheapest option if you enable the LLM at high volume.

## Migration steps (Phase 1 → Phase 2)

1. Pull the branch and `pip install -r requirements-dev.txt && pip install -e .`
   (adds `anthropic`).
2. `python -m jobsearch migrate` — applies `002_scoring.sql` (additive; the
   `jobs`/`companies` tables and all collectors are unchanged).
3. Review `config/profile.yaml` and `config/scoring.yaml`.
4. `python -m jobsearch score` to score the existing backlog.
5. (Optional) set `ANTHROPIC_API_KEY`, flip `use_llm: true`, and run
   `python -m jobsearch score --llm`.

---

# Phase 3 — Daily Automation & Reporting

Runs the whole pipeline on a schedule and tells you what's new.

```
(GitHub Actions cron) → migrate → collect → score → report (dashboard) → notify
```

## Daily report

`python -m jobsearch report` produces, for **jobs found today**:

- per-role **High Match** / **Medium Match** counts (Android, Backend, AI/ML)
- **Top Opportunities** — company, role, match score, URL

Render it as `text` (default), `markdown`, or a standalone HTML **dashboard**:

```bash
python -m jobsearch report                                   # text to stdout
python -m jobsearch report --format html --output dashboard/index.html
```

## Notifications (Telegram + Email)

`python -m jobsearch notify` sends the report through every configured channel.
Channels are configured by environment variables and **skip silently when
unset**, so the pipeline never fails on a missing secret.

**Deduplicated by design.** A job is notified only when it is **new** or its
**score changed**, and only at HIGH/MEDIUM priority (configurable). After a
successful send the state is recorded in the `notifications` table, so the same
match is **never sent twice**. `--dry-run` shows what would be sent without
sending or marking; `--channel telegram` limits to one channel.

| Channel | Env vars |
|---|---|
| Telegram | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` |
| Email (SMTP) | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS`, `EMAIL_FROM`, `EMAIL_TO` |

## Scheduling (GitHub Actions)

`.github/workflows/daily.yml` runs everything daily at 02:00 UTC (and on demand
via *Run workflow*). It uploads the dashboard as an artifact and can publish it
to GitHub Pages. **It requires a persistent `DATABASE_URL` secret** — the dedup
state must survive between runs. Full setup (secrets, Telegram bot, SMTP, Pages)
is in **[DEPLOYMENT.md](DEPLOYMENT.md)**.

## Tuning (no code changes)

`config/reporting.yaml` — `top_opportunities`, `notify_priorities`, and the role
labels shown in the report.

---

# Phase 4 — Application Intelligence

Prepares everything needed for a high-quality application — resume selection +
tailoring suggestions, cover letters, recruiter outreach drafts, application
tracking, salary intelligence, and company tiering. **It never submits anything
— drafts only**, and it generates materials **only for HIGH-priority or
user-selected jobs**, deterministically by default (zero tokens).

```
existing jobs + scores + companies ──┐
                                     ▼
        ┌──────────── Application Intelligence ─────────────┐
        │  resume selection (deterministic)                 │
        │  recommendation: why-fit / missing / strategy     │
        │  cover letter   (gated: HIGH + score≥threshold)   │──▶ application_artifacts (deduped)
        │  recruiter outreach (linkedin / email / follow-up)│
        │  application tracking (SAVED→…→OFFER/REJECTED)     │──▶ applications, recruiters
        │  salary extraction · company tiering              │──▶ jobs.salary_*, companies.tier
        └───────────────────────────────────────────────────┘
        deterministic by default · optional LLM polish (budget-guarded)
```

## What's new

- **Reuses existing data** — pulls role, score, matched/missing skills, company
  from Phases 1–2; nothing is duplicated. Phases 1–3 are untouched except a
  small additive change to expose **company tier** in the daily report.
- **Deterministic-first** — selection, recommendations, drafts, salary parsing,
  and tiering are pure code (0 tokens). An optional `--llm` flag polishes drafts
  within the same daily budget; it never receives HTML/raw descriptions and
  never sends anything.
- **Token gate** — materials are produced only for HIGH-priority jobs or jobs
  you explicitly pass on the CLI. Cover letters have an extra gate (priority
  HIGH **and** `match_score ≥ min`). Artifacts are deduped by input hash, so an
  unchanged job never triggers a second LLM call.

## Schema (additive — migration `004_application_intelligence.sql`)

```
jobs        + salary_min, salary_max, currency, compensation_source
companies   + tier  (tier1 / tier2 / tier3)

resumes(id, role_category, name, version, focus_skills[], themes[], file_path, …)
recruiters(id, name, company, linkedin_url, email, contacted_at,
           response_status[NOT_CONTACTED|CONTACTED|RESPONDED|INTERVIEWING|REJECTED], notes)
applications(id, job_id→jobs, status[SAVED|READY_TO_APPLY|APPLIED|RECRUITER_SCREEN|
             ONLINE_ASSESSMENT|TECHNICAL|FINAL|OFFER|REJECTED],
             application_date, last_update, recruiter_id→recruiters, resume_id→resumes,
             resume_version, notes)            UNIQUE(job_id)
application_artifacts(id, job_id→jobs, kind, content, generated_by, input_hash)
                                               UNIQUE(job_id, kind, input_hash)   ← dedup
generation_runs(id, started_at, kind, input_tokens, output_tokens)  ← daily LLM budget
```

## CLI commands

| Command | Purpose |
|---|---|
| `resume-select --job <id> [--apply]` | Pick the best master resume + tailoring tips; `--apply` stores it on the application |
| `application-recommend --job <id> [--output PATH]` | Why-fit / missing skills / resume recs / strategy |
| `generate-cover-letter --job <id> [--force] [--llm] [--output PATH]` | Tailored cover letter (gated; `--force` bypasses the gate) |
| `generate-outreach --job <id> [--kind linkedin\|email\|followup\|all] [--recruiter <id>] [--llm]` | Recruiter outreach drafts |
| `application-create --job <id> [--status] [--notes]` | Start tracking an application |
| `application-update --job <id> [--status] [--recruiter <id>] [--resume <id>] [--notes] [--date]` | Advance the workflow |
| `application-list [--status] [--limit]` | List tracked applications |
| `recruiter-add --name <n> [--company] [--linkedin] [--email] [--notes]` | Add a recruiter |
| `salary-backfill` | Extract salary for jobs that lack it (from `raw` + description) |
| `tiers-sync` | Persist company tiers from config onto `companies.tier` |
| `resumes-sync` | Persist master resumes from config into the DB |

## Usage examples

```bash
python -m jobsearch migrate          # applies 004 (additive)
python -m jobsearch resumes-sync     # seed master resumes
python -m jobsearch tiers-sync       # set company tiers
python -m jobsearch salary-backfill  # opportunistically fill salary

# For a HIGH-priority job (id 9):
python -m jobsearch application-recommend --job 9
python -m jobsearch resume-select --job 9 --apply
python -m jobsearch generate-cover-letter --job 9 --output out/cover_9.txt
python -m jobsearch recruiter-add --name "Dana" --company Stripe --email dana@stripe.com
python -m jobsearch generate-outreach --job 9 --kind all --recruiter 1

# Track it through the funnel:
python -m jobsearch application-create --job 9 --status SAVED
python -m jobsearch application-update --job 9 --status APPLIED --recruiter 1
python -m jobsearch application-list --status APPLIED
```

Example `application-recommend` output:

```
MATCH SCORE: 98   PRIORITY: HIGH
Acme — Android Engineer
Best resume: Android (v1)

Why:
  - Strong skill match: Android SDK, Kotlin.
  - Experience requirement aligns with your ~2 years.
Missing:
  - none
Recommendation: Apply immediately.
```

## Configuration (no code changes)

- `config/candidate.yaml` — identity used in drafts.
- `config/resumes.yaml` — the three master resumes (focus skills + themes).
- `config/company_tiers.yaml` — Tier 1/2 lists; everything else is Tier 3.
- `config/application.yaml` — cover-letter gate, strategy thresholds, bullet
  count, and the optional LLM toggle/model/`max_tokens_per_day`.

## Migration guide (Phase 3 → Phase 4)

1. `pip install -r requirements-dev.txt && pip install -e .` (no new deps).
2. `python -m jobsearch migrate` — applies `004_application_intelligence.sql`
   (purely additive: new columns on `jobs`/`companies`, new tables; nothing
   dropped or altered).
3. `python -m jobsearch resumes-sync && python -m jobsearch tiers-sync`.
4. Review `config/candidate.yaml` and `config/application.yaml`.
5. Generate materials for HIGH-priority jobs as shown above.

---

# Web Dashboard (Next.js)

An interactive dashboard lives in [`web/`](web/) — a Next.js 16 app that reads the
**same Postgres** the pipeline writes to and renders it live (overview charts, a
filterable/sortable jobs explorer, job detail with score breakdown, an
application-tracking kanban, and a companies roll-up).

```bash
docker compose up -d db                 # DB must be running + populated
python -m jobsearch collect && python -m jobsearch score
cd web && npm install && npm run dev    # http://localhost:3000
```

See [`web/README.md`](web/README.md) for details. It replaces the static
`report --format html` export with a real, interactive UI; the CLI HTML export
still works for emails/CI.

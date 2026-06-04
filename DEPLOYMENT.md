# Deployment Guide — Phase 3 (Daily Automation & Notifications)

This guide turns the project into a hands-off daily job-search agent: GitHub
Actions runs the full pipeline on a schedule, writes a dashboard, and notifies
you via Telegram and/or email about new and changed matches.

```
(cron) → migrate → collect → score → report (dashboard) → notify
```

## 1. Prerequisites

- A **persistent PostgreSQL database**. This is required: the notification
  dedup state and "jobs found today" both live in the DB, so an ephemeral
  per-run database would re-notify everything every day. Any managed Postgres
  works — Neon, Supabase, Railway, RDS, etc. Get its connection string, e.g.
  `postgresql://user:pass@host:5432/dbname`.
- A GitHub repository with Actions enabled.

## 2. Configure repository secrets

Repo → **Settings → Secrets and variables → Actions → New repository secret**.

**Required**

| Secret | Value |
|---|---|
| `DATABASE_URL` | Your persistent Postgres connection string |

**Optional — Telegram** (notifications are skipped if unset)

| Secret | How to get it |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Message **@BotFather** → `/newbot` → copy the token |
| `TELEGRAM_CHAT_ID` | Message your bot once, then open `https://api.telegram.org/bot<token>/getUpdates` and read `result[].message.chat.id` (or use **@userinfobot**) |

**Optional — Email (SMTP)**

| Secret | Example |
|---|---|
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USERNAME` | your SMTP user |
| `SMTP_PASSWORD` | SMTP password / app password |
| `SMTP_USE_TLS` | `true` |
| `EMAIL_FROM` | `you@example.com` |
| `EMAIL_TO` | `you@example.com` (comma-separated for multiple) |

> Gmail: enable 2FA and create an **App Password** — your normal password will
> not work over SMTP.

**Optional — LLM scoring** (only if `config/scoring.yaml` has `use_llm: true`)

| Secret | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |

## 3. The workflow

`.github/workflows/daily.yml` runs:

- **Schedule:** `0 2 * * *` (02:00 UTC daily). Edit the cron to taste.
- **Manual:** Actions → *Daily Job Search* → **Run workflow** (with an optional
  *Publish to GitHub Pages* checkbox).

Each run applies migrations, collects jobs, scores them, builds
`dashboard/index.html`, and notifies. It fails fast with a clear message if
`DATABASE_URL` is not set.

## 4. The dashboard

Every run uploads the dashboard as a build **artifact** (Actions → run →
*Artifacts → dashboard*). To publish it as a web page:

1. Repo → **Settings → Pages → Build and deployment → Source: GitHub Actions**.
2. Run the workflow manually with **Publish to GitHub Pages = true**, or wire it
   into the schedule. The `deploy-pages` job publishes it to your Pages URL.

## 5. Notifications: what gets sent, and when

A job is included in a notification only when it is **new** or its **score
changed**, and its priority is in `notify_priorities` (default HIGH, MEDIUM in
`config/reporting.yaml`). After a successful send, the job's state is recorded
in the `notifications` table, so it is **never re-notified at the same state** —
no duplicates. If no channel is configured or all sends fail, nothing is marked,
so the next run will try again.

## 6. Run it locally first

```bash
cp .env.example .env            # fill in DATABASE_URL (+ optional channels)
set -a && . ./.env && set +a    # export the vars
docker compose up -d db         # or point DATABASE_URL at any Postgres
python -m jobsearch migrate
python -m jobsearch collect
python -m jobsearch score
python -m jobsearch report                         # print today's report
python -m jobsearch report --format html --output dashboard/index.html
python -m jobsearch notify --dry-run               # see what would be sent
python -m jobsearch notify                         # actually send
```

`notify --dry-run` resolves the pending set and lists the channels it would use,
without sending or marking anything.

## 7. Tuning

- **Schedule:** edit the `cron` in `daily.yml`.
- **What to notify on:** `config/reporting.yaml` → `notify_priorities`.
- **Report size:** `config/reporting.yaml` → `top_opportunities`.
- **Channels:** add a class under `src/jobsearch/reporting/channels/` and list it
  in `build_channels()` — the `Channel` protocol is `is_configured()` + `send()`.

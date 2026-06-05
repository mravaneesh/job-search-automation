# JobScope — Multi-user Dashboard (Next.js)

A production-style, **multi-user** job-search app. Users sign in with Google,
complete an onboarding profile, and get jobs from a shared corpus **ranked and
filtered to them** — scored at read-time, so editing the profile instantly
re-ranks. It reads the same Postgres the Python pipeline writes to.

## Stack
- **Next.js 16** (App Router / RSC) + **TypeScript** + **Tailwind v4**
- **Auth.js (NextAuth v5)** + Google provider, **database sessions** via
  `@auth/pg-adapter`
- **node-postgres** for SQL; **Recharts**, **lucide-react**
- Deterministic **per-profile scoring ported to TypeScript** (`src/lib/scoring.ts`)

## How it works
- **Collection is shared** (Python pipeline → one deduped corpus).
- **Personalization is per-user**: each request scores & filters the corpus
  against the signed-in user's profile (roles, experience, skills, locations,
  salary). No per-user score storage — it scales by computing at read-time.
- **Applications/tracking are per-user** (`applications.user_id`).

## Pages
`/signin` · `/onboarding` (profile wizard) · `/` overview · `/jobs` explorer ·
`/jobs/[id]` detail · `/applications` kanban · `/companies` roll-up.

## Setup
1. DB up + populated (repo root): `docker compose up -d db` then
   `python -m jobsearch migrate && python -m jobsearch collect && python -m jobsearch score`.
   (`migrate` also creates the auth/profile tables from `migrations/005_users.sql`.)
2. `cd web && npm install`
3. `cp .env.example .env.local` and set `AUTH_SECRET` (and Google creds, below).
4. `npm run dev` → http://localhost:3000

### Google sign-in
Create an OAuth client at https://console.cloud.google.com/apis/credentials:
- Authorized JavaScript origin: `http://localhost:3000`
- Authorized redirect URI: `http://localhost:3000/api/auth/callback/google`

Put the Client ID/Secret in `.env.local` as `AUTH_GOOGLE_ID` / `AUTH_GOOGLE_SECRET`
and restart. Until then, `DEV_LOGIN=1` enables a local "Continue as dev user"
button so you can try the whole flow without Google.

## Deploy later (cloud)
Built cloud-ready: point `DATABASE_URL` at managed Postgres (e.g. Neon), set
`AUTH_SECRET` + Google creds + `AUTH_URL` as env vars, deploy to Vercel, and run
the Python collector on a schedule (GitHub Actions / a worker). Set `DEV_LOGIN`
unset in production.

## Notes
- Resume uploads are stored under `web/uploads/` (git-ignored) for local dev; for
  cloud, swap to object storage (S3/Vercel Blob).
- The shared corpus currently keeps India/remote IC roles; per-user filters
  (role/skills/experience/salary) apply on top.

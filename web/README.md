# JobScope — Dashboard (Next.js)

A production-style, interactive dashboard for the job-search pipeline. It reads
the **same Postgres** the Python pipeline writes to (jobs, scores, companies,
applications) and renders it as a live web app — no static HTML export.

## Stack
- **Next.js 16** (App Router, React Server Components) + **TypeScript**
- **Tailwind CSS v4** (custom dark theme)
- **node-postgres (`pg`)** — direct, parameterized SQL (server-only)
- **Recharts** — charts · **lucide-react** — icons
- **Server Actions** — application status writes back to the DB

## Pages
| Route | What |
|---|---|
| `/` | Overview — stat cards + charts (priority, role, score distribution, sources, discoveries, top companies) |
| `/jobs` | Explorer — server-side search, filters (role / priority / source / company / location / min-score), sorting, pagination |
| `/jobs/[id]` | Detail — score breakdown, matched/missing skills, salary, description, **Track application** |
| `/applications` | Interactive **kanban** — move cards through Saved → Applied → … → Offer (writes to DB) |
| `/companies` | Per-company roll-up with tiers and HIGH/MEDIUM counts |

## Run it
The Postgres DB must be up (`docker compose up -d db` in the repo root) and
populated (`python -m jobsearch collect && python -m jobsearch score`).

```bash
cd web
npm install          # first time only
npm run dev          # http://localhost:3000  (hot reload)
# or, production:
npm run build && npm run start
```

Connection comes from `web/.env.local`:
```
DATABASE_URL=postgresql://jobsearch:jobsearch@localhost:5432/jobsearch
```

The dashboard is **read-mostly**: it shows whatever the pipeline has collected.
Re-run `jobsearch collect` / `score` to refresh the data, then reload the page.
The only writes it makes are to the `applications` table (tracking status).

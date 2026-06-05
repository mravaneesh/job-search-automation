#!/usr/bin/env bash
# Run the full job-search pipeline locally and show the results.
#
#   ./scripts/run-local.sh            # collect -> score -> prep -> report + dashboard
#   ./scripts/run-local.sh --notify   # also send the email/Telegram digest
#   DAYS=7 ./scripts/run-local.sh     # widen the report window (default 3)
#
# Reads .env if present. Requires DATABASE_URL (and, for --notify, the SMTP /
# Telegram vars). Safe to re-run: collection and scoring are idempotent.

set -euo pipefail
cd "$(dirname "$0")/.."

# Load .env if it exists (export every var defined there).
if [ -f .env ]; then
  set -a; . ./.env; set +a
fi

if [ -z "${DATABASE_URL:-}" ]; then
  echo "ERROR: DATABASE_URL is not set. Put it in .env or export it." >&2
  echo "  e.g. export DATABASE_URL=postgresql://jobsearch:jobsearch@localhost:5432/jobsearch" >&2
  exit 1
fi

DAYS="${DAYS:-3}"
DASHBOARD="${DASHBOARD:-dashboard/index.html}"
NOTIFY=0
[ "${1:-}" = "--notify" ] && NOTIFY=1

run() { echo; echo ">>> jobsearch $*"; python -m jobsearch "$@"; }

run migrate
run collect
run score
run resumes-sync
run tiers-sync
run salary-backfill
run recommend-high
run report --days "$DAYS" --format html --output "$DASHBOARD"
run report --days "$DAYS"          # also print the text report

if [ "$NOTIFY" = "1" ]; then
  run notify --always --days "$DAYS"
fi

echo
echo "Done. Open the dashboard: $DASHBOARD"

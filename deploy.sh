#!/bin/bash
# Publish the latest built page to GitHub Pages.
# Usage: ./deploy.sh [path-to-built-html]   (default: the photo-drive build)
set -euo pipefail
cd "$(dirname "$0")"

SRC="${1:-/Volumes/Photography/vail_tournament.html}"
if [ ! -f "$SRC" ]; then
  echo "!!! Built page not found: $SRC" >&2
  echo "    Build it first (see README), or pass the path as an argument." >&2
  exit 1
fi

cp "$SRC" index.html
# refresh data snapshots if present alongside the build
[ -f /Volumes/Photography/vail_schedule_master.csv ] && cp /Volumes/Photography/vail_schedule_master.csv data/ || true
# publish calendar files (served at site root for the download links)
for f in /Volumes/Photography/vail_day1_route.ics /Volumes/Photography/vail_full_schedule.ics; do
  [ -f "$f" ] && cp "$f" . || true
done

git add -A
if git diff --cached --quiet; then
  echo ">>> No changes to publish."
  exit 0
fi
git commit -m "Update schedule/route ($(date +%Y-%m-%d\ %H:%M))"
git push
echo ">>> Pushed. GitHub Pages will redeploy in ~30-60s."

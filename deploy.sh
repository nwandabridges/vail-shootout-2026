#!/bin/bash
# Build the page from data/games.json and publish to GitHub Pages.
# Everything lives in this repo — no external drive needed.
set -euo pipefail
cd "$(dirname "$0")"

python3 tools/generate_html.py   # regenerates index.html + manifest + sw.js + .ics in place

git add -A
if git diff --cached --quiet; then
  echo ">>> No changes to publish."
  exit 0
fi
git commit -m "Update schedule/route ($(date +%Y-%m-%d\ %H:%M))"
git push
echo ">>> Pushed. GitHub Pages will redeploy in ~30-60s."

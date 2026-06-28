# Vail Lacrosse Shootout 2026 — Schedule & Photo Route

Self-contained interactive page for photographing the Vail Lacrosse Shootout
(Jun 27 – Jul 5, 2026). Two views:

- **📋 Schedule** — all games, filterable by day / division / field / team.
- **📷 My Route** — an optimized per-day plan that maximizes the number of
  distinct teams photographed while minimizing travel between fields.

Hosted on GitHub Pages → open the Pages URL on your phone. The page is one
static `index.html` with the data embedded. It's also an installable PWA
(Add to Home Screen) that works **fully offline** via a service worker, shows
a **live "now / next" game** indicator on the day-of, and lets you add **any
single game** to your calendar (not just the whole route).

> The PWA/offline features need HTTPS, so they only activate on the deployed
> Pages URL — not when opening `index.html` as a `file://`. To exercise them
> locally, serve the folder: `python3 -m http.server` then open
> `http://localhost:8000`.

## Updating each day

The route is planned the night before (bracket games only get real team names
once pools resolve). Everything builds in this repo — no external drive.

1. Re-scrape the resolved schedule into `data/games.json`:
   ```sh
   cd tools
   python3 fetch_parse.py     # download division pages -> tools/divpages/
   python3 parse2.py          # parse -> tools/games.json
   cp games.json ../data/games.json
   cd ..
   ```
   `fetch_parse.py` caches pages in `tools/divpages/` — `rm -rf tools/divpages`
   to force a fresh fetch. If Python's downloader hits a macOS SSL error, fetch
   the pages with `curl` into `tools/divpages/<division-id>.html` first, then
   run `parse2.py`.
2. Build + publish:
   ```sh
   ./deploy.sh                # runs generate_html.py, commits, pushes
   ```
   GitHub Pages redeploys automatically (~30–60s).

`tools/generate_html.py` reads `data/games.json` and writes `index.html`,
`manifest.webmanifest`, `sw.js`, and the `.ics` files directly into the repo
root. The PWA icons (`icon-*.png`) are committed assets; regenerate them with
PIL only if the branding changes.

## Files

- `index.html` — the live page (Pages serves this at the site root).
- `manifest.webmanifest`, `sw.js`, `icon-{180,192,512}.png` — PWA install +
  offline support.
- `vail_day1_route.ics`, `vail_full_schedule.ics` — downloadable calendars.
- `data/games.json` — parsed schedule (127 games).
- `data/vail_schedule_master.csv` — same data as a spreadsheet.
- `tools/` — the scraper, parser, route solver, and HTML generator.

## Data source

SportsEngine Tourney / TourneyMachine, tournament
`h202606131547484418093d8b9bb4e49`. Per-division `Division.aspx` pages are
fetched server-rendered (the JSON API requires auth). See `tools/` for details.

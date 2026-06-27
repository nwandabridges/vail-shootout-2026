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
once pools resolve). To refresh and publish:

1. Re-scrape + rebuild the page on the photo drive:
   ```sh
   cd /Volumes/Photography   # or the tools/ dir here
   python3 tools/fetch_parse.py     # re-fetch division pages -> data/games.json
   python3 tools/parse2.py          # clean parse
   # edit tools/route_day1.py for the target day, then:
   python3 tools/generate_html.py   # writes the photo-drive build (or builds locally — see below)
   ```
2. Publish:
   ```sh
   ./deploy.sh                      # copies the fresh build -> repo root, commits, pushes
   ```
   GitHub Pages redeploys automatically (~30–60s).

`generate_html.py` builds onto `/Volumes/Photography` when that drive is
mounted (the normal flow `deploy.sh` expects). **When the drive is not
mounted it builds straight into the repo** — writing `index.html`,
`manifest.webmanifest`, `sw.js`, and the two `.ics` files in place — so you
can edit `tools/generate_html.py` and refresh the page without the drive.
It reads `data/games.json` automatically in that case. The PWA icons
(`icon-*.png`) are committed assets; regenerate them with PIL only if the
branding changes.

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

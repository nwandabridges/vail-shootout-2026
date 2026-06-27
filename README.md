# Vail Lacrosse Shootout 2026 — Schedule & Photo Route

Self-contained interactive page for photographing the Vail Lacrosse Shootout
(Jun 27 – Jul 5, 2026). Two views:

- **📋 Schedule** — all games, filterable by day / division / field / team.
- **📷 My Route** — an optimized per-day plan that maximizes the number of
  distinct teams photographed while minimizing travel between fields.

Hosted on GitHub Pages → open the Pages URL on your phone. The page is one
static `index.html` with the data embedded, so it works offline once loaded.

## Updating each day

The route is planned the night before (bracket games only get real team names
once pools resolve). To refresh and publish:

1. Re-scrape + rebuild the page on the photo drive:
   ```sh
   cd /Volumes/Photography   # or the tools/ dir here
   python3 tools/fetch_parse.py     # re-fetch division pages -> data/games.json
   python3 tools/parse2.py          # clean parse
   # edit tools/route_day1.py for the target day, then:
   python3 tools/generate_html.py   # writes /Volumes/Photography/vail_tournament.html
   ```
2. Publish:
   ```sh
   ./deploy.sh                      # copies the fresh HTML -> index.html, commits, pushes
   ```
   GitHub Pages redeploys automatically (~30–60s).

## Files

- `index.html` — the live page (Pages serves this at the site root).
- `data/games.json` — parsed schedule (127 games).
- `data/vail_schedule_master.csv` — same data as a spreadsheet.
- `tools/` — the scraper, parser, route solver, and HTML generator.

## Data source

SportsEngine Tourney / TourneyMachine, tournament
`h202606131547484418093d8b9bb4e49`. Per-division `Division.aspx` pages are
fetched server-rendered (the JSON API requires auth). See `tools/` for details.

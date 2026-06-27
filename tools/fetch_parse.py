#!/usr/bin/env python3
import urllib.request, re, html, json, os, sys

ID = "h202606131547484418093d8b9bb4e49"
DIVS = [
    "h2026061315474844314d19b35438042",
    "h2026061315474844349e209f1be924f",
    "h202606131547484434c11cc4ba34143",
    "h202606131547484435d9aa5c85cc54c",
    "h20260613154748443ae480085aecb4c",
    "h20260613154748443afb310e6785a4b",
    "h20260613154748443badab1eb630845",
    "h20260613154748443c98d18f327eb47",
]
OUT = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(OUT, "divpages")
os.makedirs(CACHE, exist_ok=True)

def fetch(div):
    p = os.path.join(CACHE, div + ".html")
    if os.path.exists(p) and os.path.getsize(p) > 1000:
        return open(p, encoding="utf-8", errors="replace").read()
    url = f"https://tourneymachine.com/Public/Results/Division.aspx?IDTournament={ID}&IDDivision={div}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "replace")
    open(p, "w", encoding="utf-8").write(data)
    return data

def clean(s):
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def div_name(doc):
    # division name appears as (Division: NAME) in JS strings
    m = re.search(r"Division:\s*([^)]+?)\)", doc)
    if m:
        return html.unescape(m.group(1)).strip()
    return "?"

# Parse one schedule_row <tr> ... up to next <tr or </table
row_re = re.compile(r"<tr class='schedule_row[^']*'[^>]*data-gameid='([^']*)'[^>]*>(.*?)</tr>", re.S)
date_re = re.compile(r"date_(\d{8})")

def parse(doc, divlabel):
    games = []
    for tr_full in re.finditer(r"<tr class='schedule_row.*?</tr>", doc, re.S):
        block = tr_full.group(0)
        gid_m = re.search(r"data-gameid='([^']*)'", block)
        date_m = date_re.search(block)
        tds = re.findall(r"<td\b(.*?)</td>", block, re.S)
        # td[0]=game#, td[1]=date+time, td[2]=field(facility), td[3]=team1, td[4]=score1, td[5]=score2, td[6]=team2
        def td_text(i):
            return clean(tds[i]) if i < len(tds) else ""
        gameno = td_text(0)
        datetime_txt = td_text(1)
        field = td_text(2)
        team1 = td_text(3)
        team2 = td_text(6) if len(tds) > 6 else ""
        fac_m = re.search(r"data-facilityid='([^']*)'", tds[2]) if len(tds) > 2 else None
        # time: from datetime text strip the date prefix
        tm = re.search(r"(\d{1,2}:\d{2}\s*[AP]M)", datetime_txt)
        time = tm.group(1) if tm else datetime_txt
        date = date_m.group(1) if date_m else ""
        games.append({
            "division": divlabel,
            "game": gameno,
            "date": date,
            "time": time,
            "field": field,
            "facilityid": fac_m.group(1) if fac_m else "",
            "team1": team1,
            "team2": team2,
        })
    return games

all_games = []
divnames = {}
for d in DIVS:
    doc = fetch(d)
    name = div_name(doc)
    divnames[d] = name
    g = parse(doc, name)
    all_games.extend(g)
    print(f"{name:20s} {d}  -> {len(g)} games", file=sys.stderr)

json.dump(all_games, open(os.path.join(OUT, "games.json"), "w"), indent=1)
print(f"\nTOTAL GAMES: {len(all_games)}", file=sys.stderr)

# Summaries
from collections import Counter, defaultdict
print("\n=== Divisions ===", file=sys.stderr)
for d, n in divnames.items():
    print(f"  {n}", file=sys.stderr)
print("\n=== Dates ===", file=sys.stderr)
for dt, c in sorted(Counter(g["date"] for g in all_games).items()):
    print(f"  {dt}: {c} games", file=sys.stderr)
print("\n=== Fields ===", file=sys.stderr)
for f, c in sorted(Counter(g["field"] for g in all_games).items()):
    print(f"  {f!r}: {c} games", file=sys.stderr)

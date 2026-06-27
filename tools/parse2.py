#!/usr/bin/env python3
import re, html, os, json, sys
from collections import Counter, defaultdict

CACHE = "divpages"
NAME = {
  "h2026061315474844314d19b35438042": "Grandmasters",
  "h2026061315474844349e209f1be924f": "Women's Elite",
  "h202606131547484434c11cc4ba34143": "Supermasters",
  "h202606131547484435d9aa5c85cc54c": "Masters",
  "h20260613154748443ae480085aecb4c": "U19 Girls",
  "h20260613154748443afb310e6785a4b": "Men's Elite",
  "h20260613154748443badab1eb630845": "Zenmasters",
  "h20260613154748443c98d18f327eb47": "U19 Boys",
}

def clean(s):
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()

td_re = re.compile(r"<td\b([^>]*)>(.*?)</td>", re.S)
row_re = re.compile(r"<tr class='schedule_row[^']*'([^>]*)>(.*?)</tr>", re.S)

def parse(doc, divname):
    games = []
    for rm in row_re.finditer(doc):
        rattrs, body = rm.group(1), rm.group(2)
        gid = (re.search(r"data-gameid='([^']*)'", rattrs) or [None,""])[1] if "data-gameid" in rattrs else ""
        gidm = re.search(r"data-gameid='([^']*)'", rattrs); gid = gidm.group(1) if gidm else ""
        datem = re.search(r"date_(\d{8})", rm.group(0)); date = datem.group(1) if datem else ""
        cells = [(a, c) for a, c in td_re.findall(body)]
        gameno = clean(cells[0][1]) if cells else ""
        field = ""; teams = []; time = ""; datetxt = ""
        for a, c in cells:
            if "data-facilityid" in a:
                field = clean(c)
            if "data-teamid" in a:
                teams.append(clean(c))
            if ("schedule_row_date" in c) or re.search(r"\d{1,2}:\d{2}\s*[AP]M", c):
                tt = clean(c)
                tm = re.search(r"(\d{1,2}:\d{2}\s*[AP]M)", tt)
                if tm: time = tm.group(1)
                dm = re.search(r"([A-Za-z]{3}\s+\d{2}/\d{2}/\d{2})", tt)
                if dm: datetxt = dm.group(1)
        team1 = teams[0] if teams else ""
        team2 = teams[-1] if len(teams) > 1 else ""
        games.append({"division": divname, "game": gameno, "date": date,
                      "datetxt": datetxt, "time": time, "field": field,
                      "team1": team1, "team2": team2, "gid": gid})
    return games

allg = []
for fid, name in NAME.items():
    p = os.path.join(CACHE, fid + ".html")
    doc = open(p, encoding="utf-8", errors="replace").read()
    g = parse(doc, name)
    allg.append((name, len(g)))
    parse.last = g
    json.dump  # noop
    globals().setdefault("ALL", []).extend(g)

ALL = globals()["ALL"]
# real game = has a time and at least one team
RAW = ALL
ALL = [g for g in RAW if g["time"] and (g["team1"] or g["team2"])]
json.dump(ALL, open("games.json","w"), indent=1)
print(f"(raw rows {len(RAW)}, real games {len(ALL)})\n")

def t24(s):
    m = re.match(r"(\d{1,2}):(\d{2})\s*([AP]M)", s)
    if not m: return 9999
    h,mi,ap = int(m.group(1)), int(m.group(2)), m.group(3)
    if ap=="PM" and h!=12: h+=12
    if ap=="AM" and h==12: h=0
    return h*60+mi

print("=== games per division ===")
for n,c in allg: print(f"  {n:15s} {c}")
print(f"  TOTAL {len(ALL)}")

print("\n=== fields (assigned) ===")
fc = Counter(g["field"] for g in ALL)
for f,c in sorted(fc.items(), key=lambda x:-x[1]):
    print(f"  {c:4d}  {f!r}")

print("\n=== dates ===")
for d,c in sorted(Counter(g['date'] for g in ALL).items()):
    print(f"  {d}: {c}")

print("\n=== time range on a sample day (2026-06-28) ===")
day = [g for g in ALL if g['date']=='20260628' and g['field']]
for g in sorted(day, key=lambda g:(g['field'], t24(g['time'])))[:12]:
    print(f"  {g['time']:9s} {g['field']:18s} {g['division']:13s} {g['team1']} vs {g['team2']}")

print("\n=== rows missing field ===", sum(1 for g in ALL if not g['field']), "of", len(ALL))
print("=== sample no-field rows ===")
for g in [g for g in ALL if not g['field']][:6]:
    print(f"  {g['date']} {g['time']:9s} {g['division']:13s} {g['team1']!r} vs {g['team2']!r} game={g['game']!r}")

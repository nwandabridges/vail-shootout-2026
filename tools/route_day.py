#!/usr/bin/env python3
"""Generalized photo-route solver.

Maximises distinct teams photographed on a given day, with an optional
"already seen" set so multi-day planning prioritises teams not yet shot.

Usage:
    python3 route_day.py YYYYMMDD [--seen-date YYYYMMDD ...] [--seen TEAM ...]

Objective (lexicographic): most UNSEEN teams, then most total distinct teams,
then fewest field-changes, then least travel time.
"""
import json, re, sys, os, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
GAMES = "games.json" if os.path.exists("games.json") else os.path.join(REPO, "data", "games.json")
g = json.load(open(GAMES))

def t24(s):
    m = re.match(r"(\d{1,2}):(\d{2})\s*([AP]M)", s)
    if not m: return 9999
    h, mi, ap = int(m[1]), int(m[2]), m[3]
    if ap == "PM" and h != 12: h += 12
    if ap == "AM" and h == 12: h = 0
    return h*60 + mi
def hhmm(x): return f"{x//60}:{x%60:02d}{'am' if x<720 else 'pm'}"
def loc(f):
    if f.startswith("Ford"): return "Ford"
    if f == "Athletic": return "Athletic"
    if "Mountain School" in f: return "VMS"
    if f.startswith("EDW"): return "Edwards"
    return f
PH = re.compile(r"(Pool|Bracket|Conference|Place|Winner|Loser|Seed|TBD|Unknown|^\d+(st|nd|rd|th))", re.I)
def tbd(t): return bool(PH.search(t)) if t else True

DWELL, SLOT = 35, 45
TRAVEL = {("Ford","Ford"):0, ("Athletic","Athletic"):0, ("VMS","VMS"):0, ("Edwards","Edwards"):0,
          ("Ford","Athletic"):7, ("Athletic","Ford"):7,
          ("Ford","VMS"):38, ("VMS","Ford"):38, ("Athletic","VMS"):38, ("VMS","Athletic"):38,
          ("Ford","Edwards"):40, ("Edwards","Ford"):40}

ap = argparse.ArgumentParser()
ap.add_argument("date")
ap.add_argument("--seen-date", action="append", default=[])
ap.add_argument("--seen", action="append", default=[])
A = ap.parse_args()

SEEN = set(A.seen)
for sd in A.seen_date:
    for x in g:
        if x["date"] == sd:
            for t in (x["team1"], x["team2"]):
                if not tbd(t): SEEN.add(t)

day = [dict(x) for x in g if x["date"] == A.date]
for x in day:
    x["t"] = t24(x["time"]); x["loc"] = loc(x["field"])
    x["teams"] = frozenset(t for t in (x["team1"], x["team2"]) if not tbd(t))
day = [x for x in day if x["teams"]]          # drop fully-TBD games
day.sort(key=lambda r: (r["t"], r["loc"]))
N = len(day)
ALL = frozenset().union(*[x["teams"] for x in day]) if day else frozenset()
UNSEEN = ALL - SEEN
print(f"{A.date}: {N} games | {len(ALL)} distinct teams | {len(SEEN)} already seen | {len(UNSEEN)} unseen here", file=sys.stderr)

def feasible(a, b):
    if b["t"] < a["t"] or a is b: return False
    return b["t"] >= a["t"] + DWELL + TRAVEL[(a["loc"], b["loc"])]

best = {"score": (-1, -1, 1, 10**9), "route": []}
def score(seq, covered, travel):
    uns = len(covered & UNSEEN)
    return (uns, len(covered), -len(seq), -travel)   # maximise
def search(seq, covered, travel):
    sc = score(seq, covered, travel)
    # compare: higher unseen, higher total, fewer moves (less negative), less travel
    b = best["score"]
    if (sc[0], sc[1], sc[2], sc[3]) > (b[0], b[1], b[2], b[3]):
        best["score"] = sc; best["route"] = list(seq)
    last = seq[-1] if seq else None
    # optimistic bound on unseen still reachable
    future = [gm for gm in day if (last is None or gm["t"] >= last["t"]) and gm not in seq]
    reach = frozenset().union(*[c["teams"] for c in future]) if future else frozenset()
    if len((covered & UNSEEN) | (reach & UNSEEN)) < best["score"][0]: return
    for gm in day:
        if gm in seq: continue
        if last is not None and not feasible(last, gm): continue
        if last is None and gm["t"] < 0: continue
        tr = travel + (TRAVEL[(last["loc"], gm["loc"])] if last else 0)
        search(seq + [gm], covered | gm["teams"], tr)

search([], frozenset(), 0)
r = best["route"]
cov = frozenset().union(*[x["teams"] for x in r]) if r else frozenset()
print(f"\nBEST: {len(r)} games | NEW teams {len(cov & UNSEEN)}/{len(UNSEEN)} | total distinct {len(cov)} | ~{-best['score'][3]}min travel\n")
prev = None
for x in r:
    mv = "" if prev is None else (f"  (→{TRAVEL[(prev,x['loc'])]}min)" if prev != x["loc"] else "  (stay)")
    new = sorted(t for t in x["teams"] if t in UNSEEN)
    tag = "  ★NEW: " + ", ".join(new) if new else ""
    print(f"  {hhmm(x['t']):>7}  {x['field']:16s} {x['division']:13s} {x['team1']} vs {x['team2']}{mv}{tag}")
print("\nNEW teams captured:", ", ".join(sorted(cov & UNSEEN)) or "none")
print("Unseen teams NOT captured:", ", ".join(sorted(UNSEEN - cov)) or "none — got them all!")

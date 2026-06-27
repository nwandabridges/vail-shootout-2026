#!/usr/bin/env python3
import json, re, sys
from functools import lru_cache

g = json.load(open("games.json"))
def t24(s):
    m=re.match(r"(\d{1,2}):(\d{2})\s*([AP]M)",s); h,mi,ap=int(m[1]),int(m[2]),m[3]
    if ap=="PM" and h!=12:h+=12
    if ap=="AM" and h==12:h=0
    return h*60+mi
def hhmm(x): return f"{x//60}:{x%60:02d}{'am' if x<720 else 'pm'}"

DWELL = 35          # minutes the photographer spends per game (~30-40)
SLOT  = 45          # games are 45-min slots

def loc(field):
    if field.startswith("Ford"): return "Ford"
    if field == "Athletic": return "Athletic"
    if "Mountain School" in field: return "VMS"
    if field.startswith("EDW"): return "Edwards"
    return field
# travel minutes between Vail-core locations
TRAVEL = {
 ("Ford","Ford"):0, ("Athletic","Athletic"):0, ("VMS","VMS"):0,
 ("Ford","Athletic"):5, ("Athletic","Ford"):5,
 ("Ford","VMS"):8, ("VMS","Ford"):8,
 ("Athletic","VMS"):8, ("VMS","Athletic"):8,
}

day=[dict(x) for x in g if x['date']=='20260627']
for i,x in enumerate(day):
    x['t']=t24(x['time']); x['loc']=loc(x['field']); x['idx']=i
    x['teams']=frozenset([x['team1'],x['team2']])
day.sort(key=lambda r:(r['t'], r['loc']))
for i,x in enumerate(day): x['idx']=i
N=len(day)
ALLTEAMS=frozenset().union(*[x['teams'] for x in day])
print(f"Day1: {N} games, {len(ALLTEAMS)} distinct teams, DWELL={DWELL}min", file=sys.stderr)

def feasible(a,b):
    # can attend game a then game b?
    if b['t'] < a['t']: return False
    if a['idx']==b['idx']: return False
    return b['t'] >= a['t'] + DWELL + TRAVEL[(a['loc'],b['loc'])]

# Orienteering DFS with branch&bound: maximize distinct teams, tie-break fewer moves & less travel
best={'teams':frozenset(),'route':[],'travel':10**9}
# precompute, for pruning, union of teams reachable from each game onward (optimistic)
def search(seq, covered, travel):
    # record
    nt=len(covered)
    bt=len(best['teams'])
    if nt>bt or (nt==bt and (len(seq)<len(best['route']) or (len(seq)==len(best['route']) and travel<best['travel']))):
        best['teams']=covered; best['route']=list(seq); best['travel']=travel
    last=seq[-1] if seq else None
    # candidate next games
    cands=[gm for gm in day if (last is None) or feasible(last,gm)]
    # SAFE optimistic bound: covered + every team in any not-yet-attended game
    seqset=set(id(s) for s in seq)
    future=[gm for gm in day if id(gm) not in seqset and (last is None or gm['t']>=last['t'])]
    remain=frozenset().union(*[c['teams'] for c in future]) if future else frozenset()
    if len(covered|remain) < len(best['teams']): return
    for gm in cands:
        if last is not None and gm['t']<last['t']: continue
        if gm in seq: continue
        tr = travel + (TRAVEL[(last['loc'],gm['loc'])] if last is not None else 0)
        search(seq+[gm], covered|gm['teams'], tr)

# To keep DFS tractable & sensible, only start from games in first two slots
search([], frozenset(), 0)

r=best['route']
print(f"\nBEST ROUTE: {len(r)} games, covers {len(best['teams'])}/{len(ALLTEAMS)} teams, ~{best['travel']}min travel\n")
prevloc=None
for x in r:
    move = "" if prevloc is None else (f"  (→ {TRAVEL[(prevloc,x['loc'])]}min)" if prevloc!=x['loc'] else "  (stay)")
    print(f"  {hhmm(x['t']):>7}  {x['field']:16s} {x['division']:13s} {x['team1']} vs {x['team2']}{move}")
    prevloc=x['loc']
missed=ALLTEAMS-best['teams']
print("\nMISSED teams:", ", ".join(sorted(missed)) if missed else "NONE — full coverage!")
json.dump({'route':[x['idx'] for x in r],'covered':sorted(best['teams']),'missed':sorted(missed)}, open("route_day1.json","w"))

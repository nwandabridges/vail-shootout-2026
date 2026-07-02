#!/usr/bin/env python3
import json, re, datetime, os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
# Everything builds in-place into the repo (served at the site root by GitHub Pages).
OUT = REPO
GAMES = os.path.join(REPO, "data", "games.json")

g = json.load(open(GAMES))
def t24(s):
    m=re.match(r"(\d{1,2}):(\d{2})\s*([AP]M)",s)
    if not m: return 9999
    h,mi,ap=int(m[1]),int(m[2]),m[3]
    if ap=="PM" and h!=12:h+=12
    if ap=="AM" and h==12:h=0
    return h*60+mi
def fmt12(mins):
    h,mi=divmod(mins,60); ap="AM" if h<12 else "PM"; hh=h%12 or 12
    return f"{hh}:{mi:02d} {ap}"
def venue(f):
    if f.startswith("Ford"): return "Ford Park (Vail)"
    if f=="Athletic": return "Athletic Field (Vail)"
    if "Mountain School" in f: return "Vail Mtn School (E. Vail)"
    if f.startswith("EDW"): return "Edwards (down-valley)"
    return f
ADDR={"Ford":"Ford Park, 700 S Frontage Rd E, Vail, CO",
      "Athletic":"Vail Athletic Fields, 646 Vail Valley Dr, Vail, CO",
      "VMS":"Vail Mountain School, 3000 Booth Falls Rd, Vail, CO",
      "Edwards":"Edwards Freedom Park, 300 Miller Ranch Rd, Edwards, CO"}
def loc(f):
    if f.startswith("Ford"):return "Ford"
    if f=="Athletic":return "Athletic"
    if "Mountain School" in f:return "VMS"
    if f.startswith("EDW"):return "Edwards"
    return "x"
DOW={0:"Mon",1:"Tue",2:"Wed",3:"Thu",4:"Fri",5:"Sat",6:"Sun"}
def dlabel(d):
    dt=datetime.date(int(d[0:4]),int(d[4:6]),int(d[6:8]))
    return f"{DOW[dt.weekday()]} {d[4:6]}/{d[6:8]}"
# Placeholder matchers for unresolved bracket slots. NOTE: do NOT match a bare
# ordinal (e.g. "10th") — "10th Mtn Whiskey" is a real team; real placeholders
# always carry Place/Pool/Seed/etc.
PH=re.compile(r'(Pool|Bracket|Conference|Place|Winner|Loser|Seed|TBD|Unknown)',re.I)
def tbd(t): return bool(PH.search(t)) if t else True
# Division finals (each division's championship game), identified from the
# tournament brackets — every one is at Ford Field 1. (U19 Girls is omitted:
# its Gold final isn't in the published data; only a Silver final at Edwards.)
CHAMPIONSHIPS={("Zenmasters","B10"),("Grandmasters","B15"),("Supermasters","B14"),
               ("Masters","B8"),("U19 Boys","B11"),("Women's Elite","B15"),("Men's Elite","B20")}
for x in g:
    x['t']=t24(x['time']); x['venue']=venue(x['field']); x['dlabel']=dlabel(x['date'])
    x['tbd']=tbd(x['team1']) or tbd(x['team2'])
    x['champ']=(x['division'],x['game']) in CHAMPIONSHIPS

def game(tm,fld,date="20260627"):
    return next((x for x in g if x['date']==date and x['t']==t24(tm) and x['field']==fld),None)

# ---- Transit: SINGLE SOURCE OF TRUTH for bus times -----------------------------
# Every bus time the route mentions lives here exactly once, so the prose can't
# drift (the times below are interpolated into the step text). Re-check these
# against the published Town of Vail schedules and bump TRANSIT_VERIFIED.
TRANSIT_VERIFIED = "Jun 26, 2026"
def _q(s): return s.replace(" ","+").replace(",","%2C")
def maps_transit(orig,dest):  # tap-to-verify: opens live transit directions
    return f"https://www.google.com/maps/dir/?api=1&origin={_q(orig)}&destination={_q(dest)}&travelmode=transit"
# leg = one bus you board: which route, where/when you get on, where/when you get off.
BUSES={
 "out":   {"route":"Sandstone",     "from":"Sun Vail",                   "depart":"7:23a", "to":"Vail Transportation Center", "arrive":"~7:25a"},
 "toVMS": {"route":"East Vail",      "from":"Ford Park",                  "depart":"1:58p", "to":"Booth Falls",               "arrive":"~2:08p"},
 "home1": {"route":"East Vail",      "from":"Booth Falls",                "depart":"3:27p", "to":"Vail Transportation Center", "arrive":""},
 "home2": {"route":"West Vail Red",  "from":"Vail Transportation Center", "depart":"3:40p", "to":"Sun Vail",                  "arrive":""},
}
def verify(orig,dest):  # "check live ↗" link + a verified-on stamp, shown on every bus step
    return (f' <a class=chk href="{maps_transit(orig,dest)}" target=_blank rel=noopener>check live ↗</a>'
            f' <span class=verified>verified {TRANSIT_VERIFIED}</span>')
B=BUSES

# ---- Feasibility: compute connection cushions from the bus times + game times --
# so a too-tight (or impossible) connection is caught at build time AND shown on
# the page, instead of being eyeballed. DWELL must match route_day1_bus.py.
DWELL=35
WALK={"out":12,"toVMS":3}   # minutes from the alighting stop to the field
def hm(s):                  # parse "7:23a" / "~2:08p" -> minutes since midnight
    s=s.strip().lstrip("~"); m=re.match(r"(\d{1,2}):(\d{2})\s*([ap])",s)
    if not m: return None
    return (int(m[1])%12 + (12 if m[3]=="p" else 0))*60 + int(m[2])
FEAS=[]   # (ok, message) build-time log
def cushion(arrive_min, walk, faceoff, label, tight=8):
    cu=faceoff-(arrive_min+walk); ok=cu>=tight
    FEAS.append((ok, f"{label}: {cu}-min cushion before the {fmt12(faceoff)} faceoff"))
    cls="cushion" if ok else "cushion tight"
    return f' <span class="{cls}">{"✓" if ok else "⚠"} {cu}-min cushion before the {fmt12(faceoff).replace(":00","").replace(" ","").lower()} faceoff</span>'
CUSH_OUT = cushion(hm(B["out"]["arrive"]),   WALK["out"],   t24("8:00 AM"), "Sun Vail → 8:00 Ford")

TRANSIT_OUT  = (f"🚌 <b>{B['out']['depart']} · Sun Vail → Ford Field.</b> Board the <b>{B['out']['route']}</b> bus at "
  f"<b>{B['out']['from']} ({B['out']['depart']})</b> → <b>{B['out']['to']}</b> ({B['out']['arrive']}). Then a "
  f"<b>~12-min walk east</b> to Ford Field (frontage/Gore Valley Trail) — arrived ~7:40a, comfortably ahead of the 8:00 faceoff."
  + CUSH_OUT + verify("Sun Vail, Vail, CO","Ford Park, Vail, CO"))
# Day 1 is now a RECORD of what was shot — midday/home legs are descriptive (actual buses not pinned).
TOVMS = ("🚌 <b>Ford Park → Vail Mountain School (East Vail).</b> After the 10:30 game, In-Town Shuttle → "
  "<b>Vail Transportation Center</b> → <b>East Vail</b> route → <b>Booth Falls</b> stop → 3-min walk. Lunch on the way; "
  "in place for the 12:45 game."
  + verify("Ford Park, Vail, CO","Vail Mountain School, Vail, CO"))
HOME = ("🚌 <b>Vail Mtn School → home.</b> After the 1:30 game (~2:15p), <b>Booth Falls</b> → <b>East Vail</b> route → "
  "<b>Transportation Center</b> → <b>Sandstone</b> home."
  + verify("Vail Mountain School, Vail, CO","Sun Vail, Vail, CO"))

# ---- Day 1 — the games actually shot (Sat 6/27) ----
STEPS=[
 ("travel",TRANSIT_OUT),
 ("game","8:00 AM","Ford - Ford 2"),     # Mr Boh vs Middlebury
 ("walk","↔ 2-min walk to Ford Field 1"),
 ("game","8:45 AM","Ford - Field 1"),    # Grateful Undead vs Los Abuelos
 ("game","9:30 AM","Ford - Field 1"),    # Silverbacks vs Los Abuelos
 ("walk","↔ 2-min walk to Ford 2"),
 ("game","10:30 AM","Ford - Ford 2"),    # Generals vs Navy Grand Goats
 ("travel",TOVMS),
 ("game","12:45 PM","Vail Mountain School"),  # Domewood vs Outlaws
 ("game","1:30 PM","Vail Mountain School"),   # Old Birds vs Laxgear/Silver Oysters
 ("travel",HOME),
]
def build_route(steps, date, seen=None, highlight_new=False):
    """Turn a STEPS list into a route (games resolved + focus notes).
    seen = teams already photographed on prior days; highlight_new flags
    first-time teams (used Day 2+ to steer toward unseen teams)."""
    seen = seen or set()
    route=[]
    for s in steps:
        if s[0]=="game":
            x=game(s[1],s[2],date)
            if x: route.append({'type':'game',**x})
        else:
            route.append({'type':s[0],'instr':s[1]})
    rgames=[r for r in route if r['type']=='game']
    def appearances(team):  # times (mins) this team appears across the ROUTE
        return sorted(r['t'] for r in rgames if team in (r['team1'],r['team2']))
    for r in rgames:
        new=[t for t in (r['team1'],r['team2']) if not tbd(t) and t not in seen]
        if highlight_new and new:
            lab="NEW team"+("s" if len(new)>1 else "")
            r['focus']=f"🎯 <b>{lab}:</b> "+", ".join(f"<b>{t}</b>" for t in new)+f" — first time shooting {'them' if len(new)>1 else 'this team'}."
            continue
        a,b=r['team1'],r['team2']
        ta,tb=appearances(a),appearances(b)
        if len(ta)==len(tb):
            r['focus']=None; continue
        rarer,other=(a,b) if len(ta)<len(tb) else (b,a)
        ot=[t for t in (appearances(other)) if t!=r['t']]
        fut=[t for t in ot if t>r['t']]; past=[t for t in ot if t<r['t']]
        if fut:
            r['focus']=f"🎯 Focus on <b>{rarer}</b> — you'll catch {other} again at {fmt12(fut[0])}."
        else:
            r['focus']=f"🎯 Focus on <b>{rarer}</b> — you already have {other} (from {fmt12(past[-1])})."
    return route, rgames

route, gameobjs = build_route(STEPS, "20260627")
covered=sorted(set(t for r in gameobjs for t in (r['team1'],r['team2'])))
alld1=sorted(set(t for x in g if x['date']=='20260627' for t in (x['team1'],x['team2'])))
missed=[t for t in alld1 if t not in covered]

# ---- Day 2 (Sun Jun 28): full day at Ford; steer to teams not shot on Day 1 ----
# Andrew's confirmed Day-1 (6/27) captures, game-by-game (11 teams):
SEEN_D2 = {"Mr Boh","Middlebury","Grateful Undead","Los Abuelos","Silverbacks","Generals",
           "Navy Grand Goats","Domewood","Outlaws","Old Birds","Laxgear/Silver Oysters"}
D2_OUT  = ("🚶🚌 <b>Get to Ford for the 8:00 faceoff.</b> Same as yesterday: the <b>Sandstone</b> bus to the "
  "Transportation Center then the ~12-min walk (aim for the ~7:23a to arrive ~7:40a), or the <b>Golf Course</b> "
  "route straight to <b>Ford Park</b>. <i>Sunday service can differ — check live.</i>"
  + f' <a class=chk href="{maps_transit("Sun Vail, Vail, CO","Ford Park, Vail, CO")}" target=_blank rel=noopener>check live ↗</a>')
D2_HOME = ("🚌 <b>Head home from Ford</b> after the 2:00 game (~2:45p). <b>In-Town Shuttle</b> or <b>Golf Course</b> "
  "route → <b>Vail Transportation Center</b> → <b>Sandstone</b> or <b>West Vail Red</b> home."
  + f' <a class=chk href="{maps_transit("Ford Park, Vail, CO","Sun Vail, Vail, CO")}" target=_blank rel=noopener>check live ↗</a>')
STEPS2=[
 ("travel",D2_OUT),
 ("game","8:00 AM","Ford - Ford 2"),    # Navy Old Goats vs Silverbacks — NEW: Navy Old Goats
 ("walk","↔ 2-min walk to Ford Field 1"),
 ("game","9:30 AM","Ford - Field 1"),   # Graybirds vs Tivoli Brewery — NEW (two!)
 ("walk","📸 <b>Split the 9:30 slot</b> — shoot ~½ here, then 2-min walk to Ford 2 for the rest."),
 ("game","9:30 AM","Ford - Ford 2"),    # Middlebury vs Team 41 — NEW: Team 41
 ("walk","↔ 2-min walk back to Ford Field 1"),
 ("game","11:00 AM","Ford - Field 1"),  # Bushwood vs Navy Grand Goats — NEW: Bushwood
 ("walk","📸 <b>Split the 11:00 slot</b> — shoot ~½ here, then 2-min walk to Ford 2 for the rest."),
 ("game","11:00 AM","Ford - Ford 2"),   # Team 8 — NEW: Team 8
 ("game","12:30 PM","Ford - Ford 2"),   # Elysian Brewery vs Old Birds — NEW: Elysian Brewery (stay on Ford 2)
 ("walk","↔ 2-min walk to Ford Field 1"),
 ("game","2:00 PM","Ford - Field 1"),   # 10th Mtn Whiskey vs Outlaws — NEW: 10th Mtn Whiskey
 ("travel",D2_HOME),
]
route2, gameobjs2 = build_route(STEPS2, "20260628", seen=SEEN_D2, highlight_new=True)
covered2=sorted(set(t for r in gameobjs2 for t in (r['team1'],r['team2']) if not tbd(t)))
new2=sorted(set(covered2)-SEEN_D2)

# ---- Day 3 (Mon Jun 29): CHAMPIONSHIP DAY — all 3 masters finals at Ford Field 1 ----
# Zenmasters (B10 8:00), Grandmasters (B15 9:30), Supermasters (B14 11:00) — back-to-back,
# same field, no movement. Catching all three is the whole goal.
D3_OUT  = ("🚶🚌 <b>Get to Ford Field 1 for the 8:00 faceoff.</b> Same as the last two mornings: the <b>Sandstone</b> bus to "
  "the Transportation Center then the ~12-min walk (aim ~7:23a → ~7:40a), or the <b>Golf Course</b> route straight to "
  "<b>Ford Park</b>. <i>Monday service can differ — check live.</i>"
  + f' <a class=chk href="{maps_transit("Sun Vail, Vail, CO","Ford Park, Vail, CO")}" target=_blank rel=noopener>check live ↗</a>')
D3_LUNCH = ("🍔 <b>Lunch at Ford</b> (~11:45a–12:30). The Supermasters final wraps ~11:45 and U19 Boys start at 12:30 — "
  "grab food at the park, no need to leave.")
D3_HOME = ("🚌 <b>Head home from Ford</b> after the 2:00 game (~2:45p). <b>In-Town Shuttle</b> / <b>Golf Course</b> route → "
  "<b>Vail Transportation Center</b> → <b>Sandstone</b> home."
  + f' <a class=chk href="{maps_transit("Ford Park, Vail, CO","Sun Vail, Vail, CO")}" target=_blank rel=noopener>check live ↗</a>')
STEPS3=[
 ("travel",D3_OUT),
 ("game","8:00 AM","Ford - Field 1"),   # Zenmasters FINAL (B10)
 ("game","9:30 AM","Ford - Field 1"),   # Grandmasters FINAL (B15)
 ("game","11:00 AM","Ford - Field 1"),  # Supermasters FINAL (B14)
 ("lunch",D3_LUNCH),
 ("game","12:30 PM","Ford - Field 1"),  # U19 Boys: ADRLN vs Flip's Pirates
 ("walk","📸 <b>Split the 12:30 slot</b> — shoot ~½ here, then 2-min walk to Ford 2 for the rest."),
 ("game","12:30 PM","Ford - Ford 2"),   # U19 Boys: Laxachussetts vs Team CO 5A
 ("walk","↔ 2-min walk back to Ford Field 1"),
 ("game","2:00 PM","Ford - Field 1"),   # U19 Boys: Team CO 4A vs ADRLN — last new team
 ("travel",D3_HOME),
]
route3, gameobjs3 = build_route(STEPS3, "20260629")
covered3=sorted(set(t for r in gameobjs3 for t in (r['team1'],r['team2']) if not tbd(t)))

# ---- Day 5 (Thu Jul 2): Men's Elite kicks off — full new slate, all at Ford ----
# 9 Men's Elite teams, all unseen. Two parallel-field pools: morning pool (6 teams,
# 9:00-11:00 across Field 1 + Ford 2) and afternoon pool (3 teams, 12:00-2:00 Field 1).
# Splitting the 9:00 & 10:00 slots grabs all 6 morning teams (recovers GCC CORP Alumni,
# the one a single-field route misses); the afternoon pool adds the last 3.
D5_OUT  = ("🚶🚌 <b>Get to Ford Field 1 for the 9:00 faceoff.</b> Men's Elite starts at 9:00 today — a more relaxed morning. "
  "<b>Sandstone</b> bus → Transportation Center → ~12-min walk, or the <b>Golf Course</b> route straight to <b>Ford Park</b>. "
  "<i>Check live — holiday-week service can differ.</i>"
  + f' <a class=chk href="{maps_transit("Sun Vail, Vail, CO","Ford Park, Vail, CO")}" target=_blank rel=noopener>check live ↗</a>')
D5_LUNCH = ("🍔 <b>Lunch at Ford</b> (~10:45a–12:00). You've bagged all six morning-pool teams — the <b>11:00</b> games are teams "
  "you already have, so grab food and reset for the afternoon pool. (Want more reps? The 11:00 Field 1 &amp; Ford 2 games are a bonus.)")
D5_HOME = ("🚌 <b>Head home from Ford</b> after the 1:00 game (~1:45p) — all nine teams in the bag. <b>In-Town Shuttle</b> / "
  "<b>Golf Course</b> route → <b>Vail Transportation Center</b> → <b>Sandstone</b> home."
  + f' <a class=chk href="{maps_transit("Ford Park, Vail, CO","Sun Vail, Vail, CO")}" target=_blank rel=noopener>check live ↗</a>')
STEPS5=[
 ("travel",D5_OUT),
 ("game","9:00 AM","Ford - Field 1"),   # Northmen vs 10th Mountain
 ("walk","📸 <b>Split the 9:00 slot</b> — shoot ~½ here, then 2-min walk to Ford 2 for the rest."),
 ("game","9:00 AM","Ford - Ford 2"),    # RM Oysters vs GCC CORP Alumni — recovers GCC
 ("walk","↔ 2-min walk back to Ford Field 1"),
 ("game","10:00 AM","Ford - Field 1"),  # Northmen vs Team Craig — new: Team Craig
 ("walk","📸 <b>Split the 10:00 slot</b> — shoot ~½ here, then 2-min walk to Ford 2 for the rest."),
 ("game","10:00 AM","Ford - Ford 2"),   # GCC CORP Alumni vs Northside Boogeymen — new: Northside Boogeymen
 ("lunch",D5_LUNCH),
 ("game","12:00 PM","Ford - Field 1"),  # Mohawk Tile vs 10th Mountain OTF
 ("game","1:00 PM","Ford - Field 1"),   # Mohawk Tile vs Buffs — new: Buffs
 ("travel",D5_HOME),
]
route5, gameobjs5 = build_route(STEPS5, "20260702")
covered5=sorted(set(t for r in gameobjs5 for t in (r['team1'],r['team2']) if not tbd(t)))

# ---------- ICS calendar generation ----------
def ics_escape(s):
    return s.replace("\\","\\\\").replace(";","\\;").replace(",","\\,").replace("\n","\\n")
def fold(line):
    out=[];
    while len(line.encode("utf-8"))>73:
        # find cut so bytes<=73
        cut=73
        while len(line[:cut].encode("utf-8"))>73: cut-=1
        out.append(line[:cut]); line=" "+line[cut:]
    out.append(line); return "\r\n".join(out)
def utc(date,mins):  # Vail = MDT (UTC-6) for all tournament dates
    m=mins+360; h,mm=divmod(m,60)
    return f"{date}T{h:02d}{mm:02d}00Z"
def vevent(x,prefix=""):
    L=loc(x['field'])
    lines=[
      "BEGIN:VEVENT",
      f"UID:{x.get('gid') or (x['date']+x['time']+x['field'])}@vail-shootout-2026",
      "DTSTAMP:20260626T120000Z",
      f"DTSTART:{utc(x['date'],x['t'])}",
      f"DTEND:{utc(x['date'],x['t']+45)}",
      f"SUMMARY:{ics_escape(prefix+x['division']+': '+x['team1']+' vs '+x['team2'])}",
      f"LOCATION:{ics_escape(ADDR.get(L,x['field'])+' — '+x['field'])}",
      f"DESCRIPTION:{ics_escape('Vail Lacrosse Shootout 2026 · '+x['field'])}",
      "END:VEVENT"]
    return "\r\n".join(fold(l) for l in lines)
def calendar(events,name):
    head=["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//vail-shootout-2026//EN",
          "CALSCALE:GREGORIAN","METHOD:PUBLISH",f"X-WR-CALNAME:{name}",
          "X-WR-TIMEZONE:America/Denver"]
    return "\r\n".join(head+events+["END:VCALENDAR"])+"\r\n"

route_ics=calendar([vevent(x,"📷 ") for x in gameobjs],"My Vail Lax Route — Day 1")
route2_ics=calendar([vevent(x,"📷 ") for x in gameobjs2],"My Vail Lax Route — Day 2")
route3_ics=calendar([vevent(x,"🏆 ") for x in gameobjs3],"My Vail Lax Route — Day 3 Finals")
route5_ics=calendar([vevent(x,"📷 ") for x in gameobjs5],"My Vail Lax Route — Day 5 Men's Elite")
full_ics =calendar([vevent(x) for x in sorted(g,key=lambda r:(r['date'],r['t']))],"Vail Lax Shootout 2026 — Full Schedule")
open(os.path.join(OUT,"vail_day1_route.ics"),"w",newline="").write(route_ics)
open(os.path.join(OUT,"vail_day2_route.ics"),"w",newline="").write(route2_ics)
open(os.path.join(OUT,"vail_day3_route.ics"),"w",newline="").write(route3_ics)
open(os.path.join(OUT,"vail_day5_route.ics"),"w",newline="").write(route5_ics)
open(os.path.join(OUT,"vail_full_schedule.ics"),"w",newline="").write(full_ics)

# ---- per-day route content (intro / stat / notes / logistics) ----
D1_INTRO=("📷 <b>What you shot — Sat Jun 27.</b> Ford Park all morning, then out to <b>Vail Mountain School</b> (East Vail) "
  "for two afternoon games. "+str(len(covered))+" teams, car-free on the free Town of Vail buses.")
D1_MISSNOTE=(f"<b>You shot {len(covered)} of {len(alld1)} Day-1 teams.</b> Missed: {', '.join(missed)}.<br>"
  "Most play again Sun 6/28 — the <b>Day 2</b> route is built to catch the ones you can (all but Old Big Green).")
D1_LOGISTICS="""<details><summary>🚌 Car-free logistics</summary>
 <ul>
  <li><b>All Town of Vail buses are free.</b> Hub is the <b>Vail Transportation Center</b> — every route meets there to transfer.</li>
  <li><b>Morning:</b> Sandstone bus from Sun Vail → Transportation Center → ~12-min walk to Ford Park (or the Golf Course route straight to Ford).</li>
  <li><b>To East Vail:</b> In-Town Shuttle → Transportation Center → <b>East Vail</b> route → <b>Booth Falls</b> stop by Vail Mountain School.</li>
  <li>Live times on the <b>Transit app</b>, <a href="https://ride.vail.gov">ride.vail.gov</a>, or ☎ 970-477-3456.</li>
 </ul></details>"""

D2_INTRO=("📷 <b>Full day at Ford Park · 8:00a–2:45p</b> — all at Ford, no mid-day buses. By <b>splitting the 9:30 &amp; 11:00 slots</b> "
  "across both Ford fields (~½ a game each), you grab <b>"+str(len(new2))+" teams you haven't shot</b>: <b>"+", ".join(new2)+"</b>. Sun Jun 28.")
D2_MISSNOTE=("📸 <b>Splitting two slots is the trick.</b> At <b>9:30</b> shoot ~½ on Field 1 (Graybirds + Tivoli Brewery) then ~½ on Ford 2 "
  "(Team 41); at <b>11:00</b> ~½ Field 1 (Bushwood) then ~½ Ford 2 (Team 8). That recovers Team 41 &amp; Team 8.<br>"
  "The only team you <b>can't</b> get is <b>Old Big Green</b> (9:30 at <b>Athletic</b>) — reaching it means leaving Ford and giving up "
  "the 9:30 Ford split (3 teams), so it's not worth it. It doesn't play again after today.")
D2_LOGISTICS="""<details><summary>🚌 Getting there &amp; options</summary>
 <ul>
  <li><b>All at Ford Park</b> — no buses mid-day; just 2-min hops between Field 1 &amp; Ford 2.</li>
  <li><b>Getting there:</b> be at Ford for the 8:00 faceoff — Sandstone bus → Transportation Center → ~12-min walk, or the <b>Golf Course</b> route straight to Ford. Sunday times can differ; check live.</li>
  <li><b>Splitting a slot:</b> games are 45 min, fields are a 2-min walk apart — shoot ~22 min on one field, walk, ~20 min on the other. Easy to catch both games' teams.</li>
  <li><b>Can't-get:</b> Old Big Green (9:30 Athletic) — off-Ford, and it would cost you the 9:30 Ford split.</li>
  <li>⚠️ Bus times aren't pinned for Day 2 — confirm live on the <b>Transit app</b>, <a href="https://ride.vail.gov">ride.vail.gov</a>, or ☎ 970-477-3456.</li>
 </ul></details>"""

_fin_lines="<br>".join(f"<b>{x['time']}</b> · {x['division']} — {x['team1']} vs {x['team2']}" for x in gameobjs3 if x.get('champ'))
D3_INTRO=("🏆 <b>Championship day, then U19 Boys — all at Ford Park.</b> The three masters finals run back-to-back on "
  "<b>Ford Field 1</b> (8:00 · 9:30 · 11:00 — you've already shot all six finalists), then you stay at Ford for U19 Boys "
  "pool play at 12:30 &amp; 2:00. No mid-day buses. Mon Jun 29.")
D3_MISSNOTE=("🏆 <b>Today's finals — all at Ford Field 1:</b><br>"+_fin_lines+"<br><br>"
  "This route catches <b>every championship</b> played today. After lunch you're staying at Ford for <b>U19 Boys</b> pool "
  "play: splitting the <b>12:30</b> slot across Field 1 &amp; Ford 2 grabs all four teams (ADRLN, Flip's Pirates, "
  "Laxachussetts, Team CO 5A); the <b>2:00</b> game on Field 1 adds <b>Team CO 4A</b>.<br>"
  "<b>U19 Girls</b> pool play is over at Edwards — another photographer's covering it, so it's left off this route.")
D3_LOGISTICS="""<details><summary>🚌 Getting there &amp; the day</summary>
 <ul>
  <li><b>All at Ford Park</b> — no mid-day buses. Three finals on Field 1 (8:00 → ~11:45), then U19 Boys at 12:30 &amp; 2:00.</li>
  <li><b>Getting there:</b> Sandstone bus → Transportation Center → ~12-min walk to Ford, or the <b>Golf Course</b> route straight to Ford. Monday times can differ; check live.</li>
  <li><b>Between finals:</b> ~45-min gaps (8:00→9:30, 9:30→11:00) — stay put, you're already at the field.</li>
  <li><b>Splitting the 12:30 slot:</b> games are 45 min, Field 1 &amp; Ford 2 are a 2-min walk apart — shoot ~22 min on one, walk, ~20 on the other to catch both games' teams.</li>
  <li><b>Edwards skipped:</b> U19 Girls pool play there is covered by another photographer.</li>
  <li>⚠️ Bus times aren't pinned for Day 3 — confirm live on the <b>Transit app</b>, <a href="https://ride.vail.gov">ride.vail.gov</a>, or ☎ 970-477-3456.</li>
 </ul></details>"""

D5_INTRO=("📷 <b>Men's Elite kicks off — a full new slate at Ford.</b> Nine Men's Elite teams you haven't shot, all at Ford Park. "
  "Splitting the <b>9:00 &amp; 10:00</b> slots across both fields grabs all six morning-pool teams; the afternoon pool adds three more — "
  "every team, done by ~1:45p. Thu Jul 2.")
D5_MISSNOTE=("📸 <b>Two split slots get you the whole morning pool.</b> At <b>9:00</b> shoot ~½ Field 1 (Northmen + 10th Mountain) "
  "then ~½ Ford 2 (RM Oysters + GCC CORP Alumni); at <b>10:00</b> ~½ Field 1 (Team Craig) then ~½ Ford 2 (Northside Boogeymen). "
  "That's all six — the split recovers <b>GCC CORP Alumni</b>, which a single-field morning would miss.<br>"
  "The afternoon pool (12:00 &amp; 1:00, Field 1) adds <b>Mohawk Tile</b>, <b>10th Mountain OTF</b> &amp; <b>Buffs</b> — "
  "<b>nine total, every Men's Elite team.</b> The 11:00 &amp; 2:00 games are teams you'll already have (optional extra reps).")
D5_LOGISTICS="""<details><summary>🚌 Getting there &amp; the day</summary>
 <ul>
  <li><b>All at Ford Park</b> — no mid-day buses. Morning pool on Field 1 + Ford 2 (9:00–11:00), afternoon pool on Field 1 (12:00–2:00).</li>
  <li><b>Getting there:</b> be at Ford for the 9:00 faceoff — Sandstone bus → Transportation Center → ~12-min walk, or the <b>Golf Course</b> route straight to Ford. Holiday-week times can differ; check live.</li>
  <li><b>Splitting a slot:</b> games are 45 min, Field 1 &amp; Ford 2 are a 2-min walk apart — shoot ~22 min on one, walk, ~20 on the other to catch both games' teams.</li>
  <li><b>Optional:</b> the 11:00 (both fields) &amp; 2:00 games are all teams you'll already have — extra reps if you want them.</li>
  <li>⚠️ Bus times aren't pinned for Day 5 — confirm live on the <b>Transit app</b>, <a href="https://ride.vail.gov">ride.vail.gov</a>, or ☎ 970-477-3456.</li>
 </ul></details>"""

ROUTES=[
 {'key':'20260627','tab':'Day 1 · Sat 6/27','intro':D1_INTRO,
  'stat':[[str(len(covered)),'teams shot'],['8:00a–2:15p','your day'],['$0','buses free']],
  'dl':[['vail_day1_route.ics','📅 Add Day 1 route to Calendar']],
  'steps':route,'covered':covered,'missnote':D1_MISSNOTE,'logistics':D1_LOGISTICS},
 {'key':'20260628','tab':'Day 2 · Sun 6/28','intro':D2_INTRO,
  'stat':[[str(len(new2)),'new teams'],['8a–2:45p','full day'],['Ford','only · 2-min hops']],
  'dl':[['vail_day2_route.ics','📅 Add Day 2 route to Calendar']],
  'steps':route2,'covered':covered2,'missnote':D2_MISSNOTE,'logistics':D2_LOGISTICS},
 {'key':'20260629','tab':'Day 3 · Mon 6/29','intro':D3_INTRO,
  'stat':[['3','finals'],['+ U19 Boys','pool play'],['8a–2:45p','all at Ford']],
  'dl':[['vail_day3_route.ics','📅 Add Day 3 finals to Calendar']],
  'steps':route3,'covered':covered3,'missnote':D3_MISSNOTE,'logistics':D3_LOGISTICS},
 {'key':'20260702','tab':'Day 5 · Thu 7/2','intro':D5_INTRO,
  'stat':[[str(len(covered5)),'new teams'],['9a–1:45p','all at Ford'],['Ford','only · 2-min hops']],
  'dl':[['vail_day5_route.ics','📅 Add Day 5 route to Calendar']],
  'steps':route5,'covered':covered5,'missnote':D5_MISSNOTE,'logistics':D5_LOGISTICS},
]

DATA={'games':sorted(g,key=lambda r:(r['date'],r['venue'],r['field'],r['t'])),
      'routes':ROUTES,
      'days':sorted(set((x['date'],x['dlabel']) for x in g)),
      'divisions':sorted(set(x['division'] for x in g)),
      'fields':sorted(set(x['field'] for x in g))}

HTML = r"""<!DOCTYPE html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name=description content="Interactive schedule and a car-free photo-route plan for the Vail Lacrosse Shootout 2026 (Jun 27 – Jul 5): filter games by day, division, field or team, see an optimized bus route, and download calendar files.">
<meta name=color-scheme content=dark>
<meta name=theme-color content="#0f1720">
<meta name=apple-mobile-web-app-capable content=yes>
<meta name=apple-mobile-web-app-status-bar-style content=black-translucent>
<meta name=apple-mobile-web-app-title content="Vail Lax">
<link rel=icon href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Crect width='16' height='16' rx='3' fill='%23ef4444'/%3E%3Ctext x='8' y='12' font-size='11' text-anchor='middle' fill='white'%3EV%3C/text%3E%3C/svg%3E">
<link rel=manifest href="manifest.webmanifest">
<link rel=apple-touch-icon href="icon-180.png">
<title>Vail Lacrosse Shootout 2026 — Schedule & Photo Route</title>
<style>
:root{--bg:#0f1720;--card:#1b2430;--ink:#e7edf3;--mut:#aab8c6;--line:#2c3a4a;
--ford:#3b82f6;--ath:#10b981;--vms:#f59e0b;--edw:#a855f7;--accent:#ef4444;--bus:#38bdf8}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;font:16px/1.45 -apple-system,system-ui,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--ink)}
header{padding:calc(14px + env(safe-area-inset-top)) 16px 14px;background:linear-gradient(120deg,#16202b,#0f1720);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
h1{font-size:19px;margin:0 0 2px}.sub{color:var(--mut);font-size:12px}
nav{display:flex;gap:8px;padding:8px 12px;background:var(--card);position:sticky;top:0;z-index:4;border-bottom:1px solid var(--line)}
nav button{flex:1;min-height:48px;padding:12px;border:0;border-radius:10px;background:#23303d;color:var(--ink);font-weight:600;font-size:15px}
nav button.on{background:#b91c1c;color:#fff}
.wrap{padding:12px max(12px,env(safe-area-inset-right)) calc(20px + env(safe-area-inset-bottom)) max(12px,env(safe-area-inset-left));max-width:780px;margin:0 auto}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px}
.filters select,.filters input{min-height:48px;background:#23303d;color:var(--ink);border:1px solid var(--line);border-radius:10px;padding:10px;font-size:16px}
.filters input{flex:1;min-width:120px}
.vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.fld{margin:14px 0 6px;font-weight:700;font-size:13px;letter-spacing:.3px;text-transform:uppercase;color:var(--mut);border-left:4px solid var(--line);padding-left:8px}
.g{display:grid;grid-template-columns:64px 1fr;gap:10px;padding:10px;border:1px solid var(--line);border-radius:10px;margin:6px 0;background:var(--card)}
.g .tm{font-weight:700;color:#ff9a9a;font-size:14px}
.g .dv{font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:.3px}
.g .mt{font-weight:600}.g.tbd .mt{color:var(--mut);font-weight:500;font-style:italic}
.g.live{outline:2px solid var(--accent);background:#241a1a}
.g.next{outline:1px solid #2f6b48}
.badge{display:inline-block;font-size:10px;font-weight:800;letter-spacing:.3px;border-radius:6px;padding:2px 6px;margin-left:6px;vertical-align:middle}
.badge.live{background:var(--accent);color:#fff}
.badge.next{background:#16301f;color:#7ee2a8;border:1px solid #2f6b48}
.badge.champ{background:#3a2f10;color:#ffd54a;border:1px solid #6b551a}
.addcal{float:right;min-height:36px;min-width:44px;background:#15303f;border:1px solid var(--bus);color:#dff1fb;border-radius:8px;font-size:15px;padding:4px 9px;margin:-2px 0 0 8px;cursor:pointer}
.addcal:active{background:#1d4257}
.nowbar{display:none;align-items:center;gap:8px;background:#241a1a;border:1px solid var(--accent);border-radius:10px;padding:10px 12px;margin:0 0 10px;font-size:13px;color:#ffd9d9}
.nowbar.show{display:flex}
.nowbar button{margin-left:auto;min-height:36px;background:var(--accent);color:#fff;border:0;border-radius:8px;padding:6px 12px;font-weight:700;font-size:13px;cursor:pointer}
.focus{margin-top:6px;font-size:13px;color:#ffd9a8;background:#2a2113;border:1px solid #4a3a1a;border-radius:8px;padding:5px 8px}
.Ford{border-left:4px solid var(--ford)}.Athletic{border-left:4px solid var(--ath)}
.VMS{border-left:4px solid var(--vms)}.Edwards{border-left:4px solid var(--edw)}
.legend{display:flex;gap:12px;flex-wrap:wrap;font-size:12px;color:var(--mut);margin:4px 0 10px}
.dot{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:4px;vertical-align:middle}
.routestep{display:grid;grid-template-columns:64px 1fr;gap:10px;padding:10px;border:1px solid var(--line);border-radius:10px;margin:7px 0;background:var(--card)}
.routestep .tm{font-weight:800;color:#fff}
.dayswitch{display:flex;gap:8px;margin:0 0 12px}
.dayswitch button{flex:1;min-height:44px;border:1px solid var(--line);border-radius:10px;background:#23303d;color:var(--ink);font-weight:700;font-size:14px;cursor:pointer}
.dayswitch button.on{background:#b91c1c;color:#fff;border-color:#b91c1c}
.routestep.live{outline:2px solid var(--accent);background:#241a1a}
.routestep.next{outline:1px solid #2f6b48}
.travel{border:1px dashed var(--bus);background:#13202b;border-radius:10px;padding:10px 12px;margin:7px 0;font-size:14px;color:#cfe8f3;line-height:1.5}
.travel small{color:var(--mut)}
.chk{white-space:nowrap;font-weight:600}
.verified{color:var(--mut);font-size:11px;white-space:nowrap}
.cushion{display:inline-block;font-size:11px;font-weight:700;border-radius:6px;padding:1px 6px;background:#16301f;color:#7ee2a8;border:1px solid #2f6b48}
.cushion.tight{background:#3a2113;color:#ffcf9a;border-color:#6b4a1a}
.lunch{border:1px solid #caa24a;background:#241d10;border-radius:10px;padding:10px 12px;margin:7px 0;font-size:14px;color:#f1e2c2;line-height:1.5}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}
.chip{background:#23303d;border:1px solid var(--line);border-radius:20px;padding:4px 10px;font-size:13px}
.note{background:#1d2733;border:1px solid var(--line);border-left:4px solid var(--vms);border-radius:8px;padding:10px 12px;margin:10px 0;font-size:13px;color:#dde6ee;line-height:1.55}
.dl{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}
.dl a{flex:1;min-width:200px;min-height:48px;display:flex;align-items:center;justify-content:center;gap:6px;text-align:center;
  background:#15303f;border:1px solid var(--bus);color:#dff1fb;border-radius:10px;padding:12px;font-weight:600;font-size:14px;text-decoration:none}
.stat{display:flex;gap:12px;margin:8px 0;flex-wrap:wrap}
.stat div{flex:1;min-width:90px;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:8px 12px;font-size:13px;color:var(--mut)}
.stat b{font-size:20px;display:block;color:#fff}
small.hint{color:var(--mut)}
details{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin:10px 0;font-size:13px}
details summary{font-weight:700;cursor:pointer;min-height:24px}
details ul{margin:8px 0 0;padding-left:18px;line-height:1.65}
a{color:var(--bus)}
</style></head><body>
<header><h1>Vail Lacrosse Shootout 2026</h1>
<div class=sub>Jun 27 – Jul 5 · 8 divisions · 7 fields · __NGAMES__ games</div></header>
<nav><button id=tab-sched aria-pressed=false onclick="show('sched')">📋 Schedule</button>
<button id=tab-route class=on aria-pressed=true onclick="show('route')">📷 My Route</button></nav>

<main class=wrap id=view-sched hidden>
 <div class=legend>
   <span><i class="dot" style="background:var(--ford)"></i>Ford Park</span>
   <span><i class="dot" style="background:var(--ath)"></i>Athletic</span>
   <span><i class="dot" style="background:var(--vms)"></i>Vail Mtn School</span>
   <span><i class="dot" style="background:var(--edw)"></i>Edwards</span>
 </div>
 <div class=dl>
   <a href="vail_full_schedule.ics" download>📅 Add full schedule to Calendar</a>
 </div>
 <div class=filters>
   <label class=vh for=fDay>Filter by day</label><select id=fDay aria-label="Filter by day"></select>
   <label class=vh for=fDiv>Filter by division</label><select id=fDiv aria-label="Filter by division"></select>
   <label class=vh for=fField>Filter by field</label><select id=fField aria-label="Filter by field"></select>
   <label class=vh for=fSearch>Search team</label><input id=fSearch aria-label="Search team" placeholder="search team…">
 </div>
 <div class=nowbar id=nowbar></div>
 <div id=schedout></div>
</main>

<main class=wrap id=view-route>
 <div class=dayswitch id=dayswitch></div>
 <div class=stat id=rStat></div>
 <p class=sub id=rIntro></p>
 <div class=dl id=rDl></div>
 <div id=routeout></div>
 <div class=note id=missnote></div>
 <div id=rLogistics></div>
 <p class=fld>Teams you'll photograph</p><div class=chips id=covchips></div>
</main>

<script>
const D=__DATA__;
function loc(f){return f.startsWith('Ford')?'Ford':f=='Athletic'?'Athletic':f.includes('Mountain')?'VMS':f.startsWith('EDW')?'Edwards':'x'}
function esc(s){return String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
const SLOT=45; // games run 45-min slots
const GBYID={}; D.games.forEach((x,i)=>{GBYID[x.gid||('g'+i)]=x});

// ---- per-game "add to calendar" (.ics download) ----
const ICS_ADDR={Ford:'Ford Park, 700 S Frontage Rd E, Vail, CO',Athletic:'Vail Athletic Fields, 646 Vail Valley Dr, Vail, CO',VMS:'Vail Mountain School, 3000 Booth Falls Rd, Vail, CO',Edwards:'Edwards Freedom Park, 300 Miller Ranch Rd, Edwards, CO'};
function p2(n){return String(n).padStart(2,'0')}
function icsT(date,mins){const m=mins+360;return date+'T'+p2(Math.floor(m/60))+p2(m%60)+'00Z'} // Vail = MDT (UTC-6)
function icsEsc(s){return String(s).replace(/([\\;,])/g,'\\$1').replace(/\n/g,'\\n')}
function icsFold(l){let o='';while(l.length>73){o+=l.slice(0,73)+'\r\n ';l=l.slice(73)}return o+l}
function gameICS(x){
  const L=loc(x.field);
  const lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//vail-shootout-2026//EN','CALSCALE:GREGORIAN','METHOD:PUBLISH','X-WR-TIMEZONE:America/Denver',
   'BEGIN:VEVENT','UID:'+(x.gid||(x.date+x.t+x.field))+'@vail-shootout-2026','DTSTAMP:20260626T120000Z',
   'DTSTART:'+icsT(x.date,x.t),'DTEND:'+icsT(x.date,x.t+SLOT),
   'SUMMARY:'+icsEsc('📷 '+x.division+': '+x.team1+' vs '+x.team2),
   'LOCATION:'+icsEsc((ICS_ADDR[L]||x.field)+' — '+x.field),
   'DESCRIPTION:'+icsEsc('Vail Lacrosse Shootout 2026 · '+x.field),'END:VEVENT','END:VCALENDAR'];
  return lines.map(icsFold).join('\r\n')+'\r\n';
}
function addCal(id){
  const x=GBYID[id]; if(!x) return;
  const blob=new Blob([gameICS(x)],{type:'text/calendar'}),url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url; a.download='vail-'+(x.gid||id)+'.ics'; document.body.appendChild(a); a.click();
  setTimeout(()=>{URL.revokeObjectURL(url);a.remove()},1500);
}

// ---- "now / next" live awareness (uses Mountain time regardless of device tz) ----
function nowMtn(){
  const s=new Date().toLocaleString('en-US',{timeZone:'America/Denver',hour12:false,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});
  const m=s.match(/(\d+)\/(\d+)\/(\d+)\D+(\d+):(\d+)/); if(!m) return null;
  let hh=+m[4]; if(hh==24) hh=0;
  return {date:m[3]+p2(+m[1])+p2(+m[2]), mins:hh*60+(+m[5])};
}
function fmtIn(mins){if(mins<60)return 'in '+mins+'m';return 'in '+Math.floor(mins/60)+'h '+(mins%60)+'m'}
function updateLive(){
  const n=nowMtn(), bar=document.getElementById('nowbar');
  // Now/Next applies to both the schedule cards and the route steps.
  const cards=[...document.querySelectorAll('#schedout .g, #routeout .routestep[data-date]')];
  let nextStart=Infinity;
  if(n) for(const c of cards){ if(c.dataset.date===n.date){const t=+c.dataset.t; if(t>n.mins&&t<nextStart) nextStart=t;} }
  let liveN=0, jumpTarget=null;   // bar counts/jumps to schedule cards only
  for(const c of cards){
    c.classList.remove('live','next');
    const b=c.querySelector('.gbadge'); if(b){b.className='gbadge';b.textContent='';}
    if(!n||c.dataset.date!==n.date) continue;
    const t=+c.dataset.t, inSched=!!c.closest('#view-sched');
    if(n.mins>=t&&n.mins<t+SLOT){c.classList.add('live');if(b){b.className='gbadge badge live';b.textContent='● LIVE';}if(inSched){liveN++;if(!jumpTarget)jumpTarget=c;}}
    else if(t===nextStart){c.classList.add('next');if(b){b.className='gbadge badge next';b.textContent='NEXT · '+fmtIn(t-n.mins);}if(inSched&&!jumpTarget)jumpTarget=c;}
  }
  if(bar){
    if(jumpTarget){
      bar.innerHTML=(liveN?('🔴 <b>'+liveN+' game'+(liveN>1?'s':'')+' live now</b>'):('⏭️ <b>Next game '+fmtIn(nextStart-n.mins)+'</b>'))+' <button type=button>Jump ▾</button>';
      bar.classList.add('show');
      bar.querySelector('button').onclick=()=>jumpTarget.scrollIntoView({behavior:'smooth',block:'center'});
    } else bar.classList.remove('show');
  }
}
function gcard(x){return `<div class="g ${loc(x.field)} ${x.tbd?'tbd':''}" data-date="${x.date}" data-t="${x.t}">
  <div><div class=tm>${esc(x.time).replace(' ','')}</div></div>
  <div><button class=addcal title="Add this game to your calendar" aria-label="Add to calendar" onclick="addCal('${x.gid}')">＋📅</button>
  <div class=dv>${esc(x.division)}${x.champ?' <span class="badge champ">🏆 FINAL</span>':''}<span class=gbadge></span></div><div class=mt>${esc(x.team1)} <small class=hint>vs</small> ${esc(x.team2)}</div></div></div>`}
function show(t){for(const s of ['sched','route']){const v=document.getElementById('view-'+s);v.hidden=(s!=t);
  const b=document.getElementById('tab-'+s);b.classList.toggle('on',s==t);b.setAttribute('aria-pressed',s==t)}}
const fDay=document.getElementById('fDay'),fDiv=document.getElementById('fDiv'),fField=document.getElementById('fField'),fSearch=document.getElementById('fSearch');
fDay.innerHTML='<option value="">All days</option>'+D.days.map(d=>`<option value="${d[0]}">${esc(d[1])}</option>`).join('');
fDiv.innerHTML='<option value="">All divisions</option>'+D.divisions.map(d=>`<option>${esc(d)}</option>`).join('');
fField.innerHTML='<option value="">All fields</option>'+D.fields.map(d=>`<option>${esc(d)}</option>`).join('');
{const tn=nowMtn();fDay.value=(tn&&D.days.some(d=>d[0]===tn.date))?tn.date:D.days[0][0];}
function render(){
  const dy=fDay.value,dv=fDiv.value,fl=fField.value,q=fSearch.value.toLowerCase();
  let gs=D.games.filter(x=>(!dy||x.date==dy)&&(!dv||x.division==dv)&&(!fl||x.field==fl)
     &&(!q||(x.team1+' '+x.team2).toLowerCase().includes(q)));
  let out='',curDay='',curField='';
  for(const x of gs){
    if(x.date!=curDay){curDay=x.date;curField='';out+=`<h2 style="margin:18px 0 4px;font-size:16px">${esc(x.dlabel)}</h2>`}
    if(x.field!=curField){curField=x.field;const c={vms:'vms',ford:'ford',athletic:'ath',edwards:'edw'}[loc(x.field).toLowerCase()]||'edw';
      out+=`<div class="fld" style="border-left-color:var(--${c})">${esc(x.field)} — ${esc(x.venue)}</div>`}
    out+=gcard(x);
  }
  document.getElementById('schedout').innerHTML=out||'<p class=sub>No games match.</p>';
  updateLive();
}
[fDay,fDiv,fField].forEach(e=>e.onchange=render); fSearch.oninput=render; render();
setInterval(updateLive,30000);
// ---- My Route: multi-day, switchable ----
function routeStepsHTML(steps){
  let ro='';
  for(const r of steps){
    if(r.type=='game'){ro+=`<div class="routestep ${loc(r.field)}" data-date="${r.date}" data-t="${r.t}">
      <div><div class=tm>${esc(r.time).replace(' ','')}</div></div>
      <div>${r.gid?`<button class=addcal title="Add this game to your calendar" aria-label="Add to calendar" onclick="addCal('${r.gid}')">＋📅</button>`:''}<div class=dv>${esc(r.division)} · ${esc(r.field)}${r.champ?' <span class="badge champ">🏆 FINAL</span>':''}<span class=gbadge></span></div><div class=mt>${esc(r.team1)} <small class=hint>vs</small> ${esc(r.team2)}</div>
      ${r.focus?`<div class=focus>${r.focus}</div>`:''}</div></div>`}
    else if(r.type=='lunch'){ro+=`<div class=lunch>${r.instr}</div>`}
    else if(r.type=='walk'){ro+=`<div class=travel style="border-style:dotted">${r.instr}</div>`}
    else {ro+=`<div class=travel>${r.instr}</div>`}
  }
  return ro;
}
const ROUTES=D.routes;
function renderRoute(i){
  const R=ROUTES[i];
  document.querySelectorAll('#dayswitch button').forEach((b,j)=>b.classList.toggle('on',j===i));
  document.getElementById('rStat').innerHTML=R.stat.map(s=>`<div><b>${esc(s[0])}</b>${esc(s[1])}</div>`).join('');
  document.getElementById('rIntro').innerHTML=R.intro;
  document.getElementById('rDl').innerHTML=R.dl.map(d=>`<a href="${d[0]}" download>${d[1]}</a>`).join('');
  document.getElementById('routeout').innerHTML=routeStepsHTML(R.steps);
  document.getElementById('missnote').innerHTML=R.missnote;
  document.getElementById('rLogistics').innerHTML=R.logistics;
  document.getElementById('covchips').innerHTML=R.covered.map(t=>`<span class=chip>${esc(t)}</span>`).join('');
  updateLive();
}
document.getElementById('dayswitch').innerHTML=ROUTES.map((R,i)=>`<button type=button onclick="renderRoute(${i})">${esc(R.tab)}</button>`).join('');
{let di=ROUTES.findIndex(R=>{const tn=nowMtn();return tn&&R.key===tn.date}); if(di<0)di=0; renderRoute(di);}
if('serviceWorker' in navigator && location.protocol.startsWith('http')){
  addEventListener('load',()=>navigator.serviceWorker.register('sw.js').catch(()=>{}));
}
</script></body></html>"""

HTML=HTML.replace("__DATA__",json.dumps(DATA)).replace("__NGAMES__",str(len(g))).replace("__VERIFIED__",TRANSIT_VERIFIED)

# ---- PWA: manifest + offline service worker (installable, works offline on-site) ----
MANIFEST=json.dumps({
  "name":"Vail Lacrosse Shootout 2026","short_name":"Vail Lax",
  "description":"Schedule & photo-route plan for the Vail Lacrosse Shootout 2026.",
  "start_url":".","scope":".","display":"standalone","orientation":"portrait",
  "background_color":"#0f1720","theme_color":"#0f1720",
  "icons":[{"src":"icon-192.png","sizes":"192x192","type":"image/png","purpose":"any maskable"},
           {"src":"icon-512.png","sizes":"512x512","type":"image/png","purpose":"any maskable"}]
}, indent=2)
# Bump CACHE when assets change so clients pick up the new build.
SW=r"""const CACHE='vail-lax-v2';
const ASSETS=['./','index.html','manifest.webmanifest','vail_day1_route.ics','vail_day2_route.ics','vail_full_schedule.ics','icon-192.png','icon-512.png','icon-180.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{
  const req=e.request; if(req.method!=='GET') return;
  const isHTML = req.mode==='navigate' || (req.headers.get('accept')||'').includes('text/html');
  if(isHTML){ // network-first so a fresh schedule wins when online; cached page when offline
    e.respondWith(fetch(req).then(r=>{const c=r.clone();caches.open(CACHE).then(x=>x.put('index.html',c));return r}).catch(()=>caches.match('index.html')));
  } else { // cache-first for static assets
    e.respondWith(caches.match(req,{ignoreSearch:true}).then(r=>r||fetch(req).then(resp=>{const c=resp.clone();caches.open(CACHE).then(x=>x.put(req,c));return resp})));
  }
});
"""
open(os.path.join(OUT,"manifest.webmanifest"),"w").write(MANIFEST)
open(os.path.join(OUT,"sw.js"),"w").write(SW)

open(os.path.join(REPO,"index.html"),"w").write(HTML)
print(f"Wrote index.html + manifest.webmanifest + sw.js + 5 .ics files -> {REPO}")
print(f"games={len(g)} route_games={len(gameobjs)} covered={len(covered)} missed={missed}")
print("focus notes:")
for r in gameobjs:
    if r.get('focus'): print("  ",r['time'],r['field'],"->",re.sub('<[^>]+>','',r['focus']))
print("route .ics events:",route_ics.count("BEGIN:VEVENT"),"| full .ics events:",full_ics.count("BEGIN:VEVENT"))
print("transit feasibility:")
for ok,msg in FEAS:
    print(("  ✓ " if ok else "  ⚠ TIGHT — ")+msg)

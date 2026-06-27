#!/usr/bin/env python3
import json, re, datetime

g = json.load(open("games.json"))
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
PH=re.compile(r'(Pool|Bracket|Conference|Place|Winner|Loser|Seed|TBD|^\d+(st|nd|rd|th))',re.I)
def tbd(t): return bool(PH.search(t)) if t else True
for x in g:
    x['t']=t24(x['time']); x['venue']=venue(x['field']); x['dlabel']=dlabel(x['date'])
    x['tbd']=tbd(x['team1']) or tbd(x['team2'])

def game(tm,fld):
    return next((x for x in g if x['date']=='20260627' and x['t']==t24(tm) and x['field']==fld),None)

# ---- Day 1 CAR-FREE shorter-day route ----
STEPS=[
 ("travel","🚌 <b>7:43a · Sun Vail → Ford Field.</b> Catch the <b>Sandstone</b> bus (7:43a) → <b>Vail Transportation Center</b> (~7:45a). From there it's a <b>~12-min walk east</b> to Ford Field (along the frontage/Gore Valley Trail) — you'll reach the field right around the 8:00 faceoff.<br><small>It's tight; if you'd rather not rush, the 8:45 game is an easy backup (you'd give up either Silverbacks or Mr Boh).</small>"),
 ("game","8:00 AM","Ford - Ford 2"),
 ("walk","↔ 2-min walk between the two Ford Park fields"),
 ("game","8:45 AM","Ford - Field 1"),
 ("game","9:30 AM","Ford - Field 1"),
 ("game","10:30 AM","Ford - Ford 2"),
 ("travel","🚶 <b>~7-min walk</b> Ford Park → Athletic Field (along Vail Valley Dr)."),
 ("game","11:15 AM","Athletic"),
 ("travel","🚶 <b>~7-min walk</b> back Athletic → Ford Park."),
 ("game","12:00 PM","Ford - Field 1"),
 ("game","12:45 PM","Ford - Field 1"),
 ("lunch","🍔 <b>Lunch — grab-and-go ~1:20p.</b> Your games run back-to-back, so your meal break is the ride to East Vail. Easiest: grab food in <b>Vail Village at the Transportation Center while you transfer</b>, or pack a sandwich to eat on the bus. (The Village, which you pass through, has by far the most options.)"),
 ("travel","🚌 <b>~1:20p · Ford Park → Vail Mountain School (East Vail).</b> Leave right after the 12:45 game. <b>In-Town Shuttle</b> from Ford Park (every 7–10 min) → <b>Vail Transportation Center</b> (~10 min). Transfer to the <b>East Vail</b> route (every ~15 min) → <b>Booth Falls</b> stop → 3-min walk to the school. ~35–40 min; arrive ~2:00p, just ahead of the 2:15 game."),
 ("game","2:15 PM","Vail Mountain School"),
 ("game","3:00 PM","Vail Mountain School"),
 ("travel","🚌 <b>~3:35p · Vail Mtn School → Sun Vail.</b> Walk to the Booth Falls stop → <b>East Vail</b> route → <b>Vail Transportation Center</b> → transfer to the <b>Sandstone</b> bus → Sun Vail. ~40 min. <b>Home by ~4:15p.</b>"),
]
route=[]
for s in STEPS:
    if s[0]=="game":
        x=game(s[1],s[2])
        if x: route.append({'type':'game',**x})
    else:
        route.append({'type':s[0],'instr':s[1]})

# ---- focus notes: per route game, prioritise the team you'll catch fewer times today ----
rgames=[r for r in route if r['type']=='game']
def appearances(team):  # times (mins) this team appears across the ROUTE
    return sorted(r['t'] for r in rgames if team in (r['team1'],r['team2']))
for r in rgames:
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

gameobjs=rgames
covered=sorted(set(t for r in gameobjs for t in (r['team1'],r['team2'])))
alld1=sorted(set(t for x in g if x['date']=='20260627' for t in (x['team1'],x['team2'])))
missed=[t for t in alld1 if t not in covered]

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
full_ics =calendar([vevent(x) for x in sorted(g,key=lambda r:(r['date'],r['t']))],"Vail Lax Shootout 2026 — Full Schedule")
open("/Volumes/Photography/vail_day1_route.ics","w",newline="").write(route_ics)
open("/Volumes/Photography/vail_full_schedule.ics","w",newline="").write(full_ics)

DATA={'games':sorted(g,key=lambda r:(r['date'],r['venue'],r['field'],r['t'])),
      'route':route,'covered':covered,'missed':missed,
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
nav button.on{background:var(--accent)}
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
.focus{margin-top:6px;font-size:13px;color:#ffd9a8;background:#2a2113;border:1px solid #4a3a1a;border-radius:8px;padding:5px 8px}
.Ford{border-left:4px solid var(--ford)}.Athletic{border-left:4px solid var(--ath)}
.VMS{border-left:4px solid var(--vms)}.Edwards{border-left:4px solid var(--edw)}
.legend{display:flex;gap:12px;flex-wrap:wrap;font-size:12px;color:var(--mut);margin:4px 0 10px}
.dot{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:4px;vertical-align:middle}
.routestep{display:grid;grid-template-columns:64px 1fr;gap:10px;padding:10px;border:1px solid var(--line);border-radius:10px;margin:7px 0;background:var(--card)}
.routestep .tm{font-weight:800;color:#fff}
.travel{border:1px dashed var(--bus);background:#13202b;border-radius:10px;padding:10px 12px;margin:7px 0;font-size:14px;color:#cfe8f3;line-height:1.5}
.travel small{color:var(--mut)}
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
<nav><button id=tab-sched class=on aria-pressed=true onclick="show('sched')">📋 Schedule</button>
<button id=tab-route aria-pressed=false onclick="show('route')">📷 My Route · Day 1</button></nav>

<main class=wrap id=view-sched>
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
 <div id=schedout></div>
</main>

<main class=wrap id=view-route hidden>
 <div class=stat>
   <div><b id=rTeams></b>teams covered</div>
   <div><b>~3:30p</b>last shot · home ~4:15</div>
   <div><b>$0</b>all buses free</div>
 </div>
 <p class=sub>🚌 <b>Car-free · shorter day</b> from Sun Vail · full Ford Park morning, out to East Vail after lunch, done by ~3:30p · ~35 min per game · Sat Jun 27. All Town of Vail buses are <b>free</b>.</p>
 <div class=dl>
   <a href="vail_day1_route.ics" download>📅 Add my Day 1 route to Calendar</a>
 </div>
 <div id=routeout></div>
 <div class=note id=missnote></div>
 <details><summary>🚌 Car-free logistics & alternatives</summary>
 <ul>
  <li><b>All Town of Vail buses are free.</b> Hub is the <b>Vail Transportation Center</b> (Vail Village) — every route meets there to transfer.</li>
  <li><b>In-Town Shuttle</b>: every 7–10 min; reaches <b>Ford Park</b> (via Vail Valley Dr) only <b>9a–9p</b>.</li>
  <li><b>Golf Course route</b>: serves Ford Park/Athletic; first bus 7:40a, hourly 8:10a–5:10p — an alternate early-AM ride if you skip the walk.</li>
  <li><b>East Vail route</b>: serves the <b>Booth Falls</b> stop by Vail Mountain School; ~15-min service from 6a.</li>
  <li><b>Sandstone route</b>: your home stop at Sun Vail ↔ Transportation Center.</li>
  <li><b>Easier morning (–1 team):</b> skip the 8:00 game and start at 8:45 — you'd miss either Silverbacks or Mr Boh.</li>
  <li><b>Fuller day (+1 team, ends ~5p):</b> stay at Ford for the 1:30 game (adds 10th Mtn Whiskey, 18 teams), then ride to VMS for the 3:45 &amp; 4:30 games.</li>
  <li>⚠️ Bus times are estimates from published frequencies. Confirm live departures on the <b>Transit app</b>, <a href="https://ride.vail.gov">ride.vail.gov</a>, or ☎ 970-477-3456.</li>
 </ul></details>
 <p class=fld>Teams you'll photograph</p><div class=chips id=covchips></div>
</main>

<script>
const D=__DATA__;
function loc(f){return f.startsWith('Ford')?'Ford':f=='Athletic'?'Athletic':f.includes('Mountain')?'VMS':f.startsWith('EDW')?'Edwards':'x'}
function esc(s){return String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
function gcard(x){return `<div class="g ${loc(x.field)} ${x.tbd?'tbd':''}">
  <div><div class=tm>${esc(x.time).replace(' ','')}</div></div>
  <div><div class=dv>${esc(x.division)}</div><div class=mt>${esc(x.team1)} <small class=hint>vs</small> ${esc(x.team2)}</div></div></div>`}
function show(t){for(const s of ['sched','route']){const v=document.getElementById('view-'+s);v.hidden=(s!=t);
  const b=document.getElementById('tab-'+s);b.classList.toggle('on',s==t);b.setAttribute('aria-pressed',s==t)}}
const fDay=document.getElementById('fDay'),fDiv=document.getElementById('fDiv'),fField=document.getElementById('fField'),fSearch=document.getElementById('fSearch');
fDay.innerHTML='<option value="">All days</option>'+D.days.map(d=>`<option value="${d[0]}">${esc(d[1])}</option>`).join('');
fDiv.innerHTML='<option value="">All divisions</option>'+D.divisions.map(d=>`<option>${esc(d)}</option>`).join('');
fField.innerHTML='<option value="">All fields</option>'+D.fields.map(d=>`<option>${esc(d)}</option>`).join('');
fDay.value=D.days[0][0];
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
}
[fDay,fDiv,fField].forEach(e=>e.onchange=render); fSearch.oninput=render; render();
document.getElementById('rTeams').textContent=D.covered.length;
let ro='';
for(const r of D.route){
  if(r.type=='game'){ro+=`<div class="routestep ${loc(r.field)}">
    <div><div class=tm>${esc(r.time).replace(' ','')}</div></div>
    <div><div class=dv>${esc(r.division)} · ${esc(r.field)}</div><div class=mt>${esc(r.team1)} <small class=hint>vs</small> ${esc(r.team2)}</div>
    ${r.focus?`<div class=focus>${r.focus}</div>`:''}</div></div>`}
  else if(r.type=='lunch'){ro+=`<div class=lunch>${r.instr}</div>`}
  else if(r.type=='walk'){ro+=`<div class=travel style="border-style:dotted">${r.instr}</div>`}
  else {ro+=`<div class=travel>${r.instr}</div>`}
}
document.getElementById('routeout').innerHTML=ro;
document.getElementById('covchips').innerHTML=D.covered.map(t=>`<span class=chip>${esc(t)}</span>`).join('');
document.getElementById('missnote').innerHTML=`<b>${D.missed.length} of 20 teams not covered:</b> ${D.missed.map(esc).join(', ')}.<br>`+
 `• <b>10th Mtn Whiskey</b> — skipped by choice for the shorter day (only plays the 1:30 &amp; 2:15 Ford games). Want it? Use the <i>Fuller day</i> option below.<br>`+
 `• <b>Old Big Green</b> &amp; <b>Team 41</b> — boxed out by the 10:30–12:00 Grandmasters crunch (8 teams across 3 parallel fields). To grab them you'd field-hop (≈15–20 min/game): Old Big Green on Ford Field 1, Team 41 on the Athletic field.`;
</script></body></html>"""

HTML=HTML.replace("__DATA__",json.dumps(DATA)).replace("__NGAMES__",str(len(g)))
open("/Volumes/Photography/vail_tournament.html","w").write(HTML)
print("Wrote vail_tournament.html + 2 .ics files")
print(f"games={len(g)} route_games={len(gameobjs)} covered={len(covered)} missed={missed}")
print("focus notes:")
for r in gameobjs:
    if r.get('focus'): print("  ",r['time'],r['field'],"->",re.sub('<[^>]+>','',r['focus']))
print("route .ics events:",route_ics.count("BEGIN:VEVENT"),"| full .ics events:",full_ics.count("BEGIN:VEVENT"))

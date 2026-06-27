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
def venue(f):
    if f.startswith("Ford"): return "Ford Park (Vail)"
    if f=="Athletic": return "Athletic Field (Vail)"
    if "Mountain School" in f: return "Vail Mtn School (E. Vail)"
    if f.startswith("EDW"): return "Edwards (down-valley)"
    return f
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

# ---- Day 1 CAR-FREE route: interleave bus/walk legs (travel) with games ----
STEPS=[
 ("travel","🚌 <b>~7:05a · Sun Vail → Ford Park.</b> Free <b>Sandstone</b> bus from the stop outside Sun Vail → <b>Vail Transportation Center</b> (~10 min). Transfer to the <b>Golf Course</b> route — <b>first bus 7:40a</b> — to the Ford Park / Athletic Fields stop (~10 min). Arrive ~7:50a.<br><small>Why so early: the In-Town Shuttle doesn't reach Ford Park until 9a, so the 7:40 Golf Course bus is the only ride that makes the 8:00 game. Miss it? It's a ~12–15 min walk east from Vail Village.</small>"),
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
 ("game","1:30 PM","Ford - Field 1"),
 ("travel","🚌 <b>~2:05p · Ford Park → Vail Mountain School (East Vail).</b> <b>In-Town Shuttle</b> from Ford Park (every 7–10 min) → <b>Vail Transportation Center</b> (~10 min). Transfer to the <b>East Vail</b> route (every ~15 min) → <b>Booth Falls</b> stop → 3-min walk to the school. ~35–40 min door-to-door; arrive ~2:45p.<br><small>You'll arrive before the 3:00 game — catch it too (Laxgear vs Domewood) to fill the gap; the three VMS games below cover all four Supermasters teams there.</small>"),
 ("game","3:45 PM","Vail Mountain School"),
 ("game","4:30 PM","Vail Mountain School"),
 ("travel","🚌 <b>~5:05p · Vail Mtn School → Sun Vail.</b> Walk to the Booth Falls stop → <b>East Vail</b> route → <b>Vail Transportation Center</b> → transfer to the <b>Sandstone</b> bus → Sun Vail. ~40 min."),
]
route=[]
for s in STEPS:
    if s[0]=="game":
        x=game(s[1],s[2])
        if x: route.append({'type':'game',**x})
    else:
        route.append({'type':s[0],'instr':s[1]})
gameobjs=[r for r in route if r['type']=='game']
covered=sorted(set(t for r in gameobjs for t in (r['team1'],r['team2'])))
alld1=sorted(set(t for x in g if x['date']=='20260627' for t in (x['team1'],x['team2'])))
missed=[t for t in alld1 if t not in covered]

DATA={'games':sorted(g,key=lambda r:(r['date'],r['venue'],r['field'],r['t'])),
      'route':route,'covered':covered,'missed':missed,
      'days':sorted(set((x['date'],x['dlabel']) for x in g)),
      'divisions':sorted(set(x['division'] for x in g)),
      'fields':sorted(set(x['field'] for x in g))}

HTML = r"""<!DOCTYPE html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Vail Lacrosse Shootout 2026 — Schedule & Photo Route</title>
<style>
:root{--bg:#0f1720;--card:#1b2430;--ink:#e7edf3;--mut:#93a4b3;--line:#2c3a4a;
--ford:#3b82f6;--ath:#10b981;--vms:#f59e0b;--edw:#a855f7;--accent:#ef4444;--bus:#38bdf8}
*{box-sizing:border-box}body{margin:0;font:15px/1.45 -apple-system,system-ui,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--ink)}
header{padding:14px 16px;background:linear-gradient(120deg,#16202b,#0f1720);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
h1{font-size:18px;margin:0 0 2px}.sub{color:var(--mut);font-size:12px}
nav{display:flex;gap:6px;padding:8px 12px;background:var(--card);position:sticky;top:54px;z-index:4;border-bottom:1px solid var(--line)}
nav button{flex:1;padding:9px;border:0;border-radius:8px;background:#23303d;color:var(--ink);font-weight:600;font-size:13px}
nav button.on{background:var(--accent)}
.wrap{padding:12px;max-width:780px;margin:0 auto}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px}
.filters select,.filters input{background:#23303d;color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:8px;font-size:14px}
.filters input{flex:1;min-width:120px}
.fld{margin:14px 0 6px;font-weight:700;font-size:13px;letter-spacing:.3px;text-transform:uppercase;color:var(--mut);border-left:4px solid var(--line);padding-left:8px}
.g{display:grid;grid-template-columns:62px 1fr;gap:10px;padding:9px 10px;border:1px solid var(--line);border-radius:10px;margin:6px 0;background:var(--card)}
.g .tm{font-weight:700;color:var(--accent);font-size:14px}
.g .dv{font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:.3px}
.g .mt{font-weight:600}.g.tbd .mt{color:var(--mut);font-weight:500;font-style:italic}
.Ford{border-left:4px solid var(--ford)}.Athletic{border-left:4px solid var(--ath)}
.VMS{border-left:4px solid var(--vms)}.Edwards{border-left:4px solid var(--edw)}
.legend{display:flex;gap:12px;flex-wrap:wrap;font-size:12px;color:var(--mut);margin:4px 0 10px}
.dot{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:4px;vertical-align:middle}
.routestep{display:grid;grid-template-columns:64px 1fr;gap:10px;padding:10px;border:1px solid var(--line);border-radius:10px;margin:7px 0;background:var(--card)}
.routestep .tm{font-weight:800;color:#fff}
.travel{border:1px dashed var(--bus);background:#13202b;border-radius:10px;padding:10px 12px;margin:7px 0;font-size:13px;color:#cfe8f3;line-height:1.5}
.travel small{color:var(--mut)}
.chips{display:flex;flex-wrap:wrap;gap:5px;margin:8px 0}
.chip{background:#23303d;border:1px solid var(--line);border-radius:20px;padding:3px 9px;font-size:12px}
.note{background:#1d2733;border:1px solid var(--line);border-left:4px solid var(--vms);border-radius:8px;padding:10px 12px;margin:10px 0;font-size:13px;color:#cdd9e3;line-height:1.5}
.stat{display:flex;gap:14px;margin:8px 0;flex-wrap:wrap}
.stat div{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:8px 12px;font-size:13px}
.stat b{font-size:20px;display:block;color:#fff}
small.hint{color:var(--mut)}
details{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin:10px 0;font-size:13px}
details summary{font-weight:700;cursor:pointer}
details ul{margin:8px 0 0;padding-left:18px;line-height:1.6}
a{color:var(--bus)}
</style></head><body>
<header><h1>Vail Lacrosse Shootout 2026</h1>
<div class=sub>Jun 27 – Jul 5 · 8 divisions · 7 fields · __NGAMES__ games · built __TODAY__</div></header>
<nav><button id=tab-sched class=on onclick="show('sched')">📋 Schedule</button>
<button id=tab-route onclick="show('route')">📷 My Route · Day 1</button></nav>

<div class=wrap id=view-sched>
 <div class=legend>
   <span><i class="dot" style="background:var(--ford)"></i>Ford Park</span>
   <span><i class="dot" style="background:var(--ath)"></i>Athletic</span>
   <span><i class="dot" style="background:var(--vms)"></i>Vail Mtn School</span>
   <span><i class="dot" style="background:var(--edw)"></i>Edwards</span>
 </div>
 <div class=filters>
   <select id=fDay></select><select id=fDiv></select><select id=fField></select>
   <input id=fSearch placeholder="search team…">
 </div>
 <div id=schedout></div>
</div>

<div class=wrap id=view-route style=display:none>
 <div class=stat>
   <div><b id=rTeams></b>teams covered</div>
   <div><b>~52</b>min on buses</div>
   <div><b>$0</b>all buses free</div>
 </div>
 <p class=sub>🚌 <b>Car-free plan</b> from Sun Vail · maximizes distinct teams, minimizes travel · ~35 min per game · Sat Jun 27. All Town of Vail buses are <b>free</b>.</p>
 <div id=routeout></div>
 <div class=note id=missnote></div>

 <details><summary>🚌 Car-free logistics & alternatives</summary>
 <ul>
  <li><b>All Town of Vail buses are free.</b> Hub is the <b>Vail Transportation Center</b> (Vail Village) — every route meets there to transfer.</li>
  <li><b>In-Town Shuttle</b>: every 7–10 min; reaches <b>Ford Park</b> (via Vail Valley Dr) only <b>9a–9p</b>.</li>
  <li><b>Golf Course route</b>: serves Ford Park/Athletic; <b>first bus 7:40a</b>, then hourly 8:10a–5:10p — your early-morning ride.</li>
  <li><b>East Vail route</b>: serves the <b>Booth Falls</b> stop by Vail Mountain School; ~15-min service from 6a.</li>
  <li><b>Sandstone route</b>: your home stop at Sun Vail ↔ Transportation Center.</li>
  <li><b>Easier morning (–1 team):</b> skip the 8:00 game and start at 8:45 — but you'd miss either Silverbacks or Mr Boh (the two early Zenmasters split across the 8:00 Ford 1 & Ford 2 games).</li>
  <li><b>Shorter day (–1 team, done ~3:35p):</b> leave Ford after the 12:45 game, ride to VMS for the 2:15 & 3:00 games. You'd drop only <b>10th Mtn Whiskey</b> and skip the late-afternoon wait.</li>
  <li>⚠️ Times are estimates from published frequencies (the live timetable wasn't machine-readable). Confirm departures on the <b>Transit app</b>, <a href="https://ride.vail.gov">ride.vail.gov</a>, or ☎ 970-477-3456.</li>
 </ul></details>

 <p class=fld>Teams you'll photograph</p><div class=chips id=covchips></div>
</div>

<script>
const D=__DATA__;
function loc(f){return f.startsWith('Ford')?'Ford':f=='Athletic'?'Athletic':f.includes('Mountain')?'VMS':f.startsWith('EDW')?'Edwards':'x'}
function gcard(x){return `<div class="g ${loc(x.field)} ${x.tbd?'tbd':''}">
  <div><div class=tm>${x.time.replace(' ','')}</div></div>
  <div><div class=dv>${x.division}</div><div class=mt>${x.team1} <small class=hint>vs</small> ${x.team2}</div></div></div>`}
function show(t){for(const s of ['sched','route']){document.getElementById('view-'+s).style.display=s==t?'':'none';
  document.getElementById('tab-'+s).classList.toggle('on',s==t)}}
const fDay=document.getElementById('fDay'),fDiv=document.getElementById('fDiv'),fField=document.getElementById('fField'),fSearch=document.getElementById('fSearch');
fDay.innerHTML='<option value="">All days</option>'+D.days.map(d=>`<option value="${d[0]}">${d[1]}</option>`).join('');
fDiv.innerHTML='<option value="">All divisions</option>'+D.divisions.map(d=>`<option>${d}</option>`).join('');
fField.innerHTML='<option value="">All fields</option>'+D.fields.map(d=>`<option>${d}</option>`).join('');
fDay.value=D.days[0][0];
function render(){
  const dy=fDay.value,dv=fDiv.value,fl=fField.value,q=fSearch.value.toLowerCase();
  let gs=D.games.filter(x=>(!dy||x.date==dy)&&(!dv||x.division==dv)&&(!fl||x.field==fl)
     &&(!q||(x.team1+' '+x.team2).toLowerCase().includes(q)));
  let out='',curDay='',curField='';
  for(const x of gs){
    if(x.date!=curDay){curDay=x.date;curField='';out+=`<h2 style="margin:18px 0 4px;font-size:16px">${x.dlabel}</h2>`}
    if(x.field!=curField){curField=x.field;const L=loc(x.field).toLowerCase();const c=L=='vms'?'vms':L=='ford'?'ford':L=='athletic'?'ath':'edw';
      out+=`<div class="fld" style="border-left-color:var(--${c})">${x.field} — ${x.venue}</div>`}
    out+=gcard(x);
  }
  document.getElementById('schedout').innerHTML=out||'<p class=sub>No games match.</p>';
}
[fDay,fDiv,fField].forEach(e=>e.onchange=render); fSearch.oninput=render; render();
// route
document.getElementById('rTeams').textContent=D.covered.length;
let ro='';
for(const r of D.route){
  if(r.type=='game'){ro+=`<div class="routestep ${loc(r.field)}">
    <div><div class=tm>${r.time.replace(' ','')}</div></div>
    <div><div class=dv>${r.division} · ${r.field}</div><div class=mt>${r.team1} <small class=hint>vs</small> ${r.team2}</div></div></div>`}
  else if(r.type=='walk'){ro+=`<div class=travel style="border-style:dotted">${r.instr}</div>`}
  else {ro+=`<div class=travel>${r.instr}</div>`}
}
document.getElementById('routeout').innerHTML=ro;
document.getElementById('covchips').innerHTML=D.covered.map(t=>`<span class=chip>${t}</span>`).join('');
document.getElementById('missnote').innerHTML=`<b>${D.missed.length} teams not reachable today:</b> ${D.missed.join(', ')}. `+
 `They're boxed out by the 10:30–12:00 Grandmasters crunch (8 teams across 3 parallel fields). `+
 `To grab them you'd field-hop (≈15–20 min/game) during that window: <b>Old Big Green</b> is on Ford Field 1, <b>Team 41</b> on the Athletic field (10:30, or the 12:00 Team 8 vs Team 41 game).`;
</script></body></html>"""

HTML=HTML.replace("__DATA__",json.dumps(DATA)).replace("__NGAMES__",str(len(g))).replace("__TODAY__","2026-06-26")
open("/Volumes/Photography/vail_tournament.html","w").write(HTML)
print("Wrote /Volumes/Photography/vail_tournament.html")
print(f"games={len(g)} routesteps={len(route)} games_in_route={len(gameobjs)} covered={len(covered)} missed={missed}")

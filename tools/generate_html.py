#!/usr/bin/env python3
import json, re

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
    if "Mountain School" in f: return "Vail Mtn School (Vail)"
    if f.startswith("EDW"): return "Edwards (down-valley)"
    return f
DOW={0:"Mon",1:"Tue",2:"Wed",3:"Thu",4:"Fri",5:"Sat",6:"Sun"}
import datetime
def dlabel(d):
    dt=datetime.date(int(d[0:4]),int(d[4:6]),int(d[6:8]))
    return f"{DOW[dt.weekday()]} {d[4:6]}/{d[6:8]}"
PH=re.compile(r'(Pool|Bracket|Conference|Place|Winner|Loser|Seed|TBD|^\d+(st|nd|rd|th))',re.I)
def tbd(t): return bool(PH.search(t)) if t else True

for x in g:
    x['t']=t24(x['time']); x['venue']=venue(x['field']); x['dlabel']=dlabel(x['date'])
    x['tbd']=tbd(x['team1']) or tbd(x['team2'])

# ---- Day1 route (recompute, mirrors route_day1.py optimum) ----
ROUTE=[ # (time24, field, note)
 (480,"Ford - Ford 2",""),(525,"Ford - Field 1","stay"),(570,"Ford - Field 1","stay"),
 (630,"Ford - Ford 2","stay"),(675,"Athletic","walk 5 min from Ford"),
 (720,"Ford - Field 1","walk back 5 min"),(765,"Ford - Field 1","stay"),(810,"Ford - Field 1","stay"),
 (855,"Vail Mountain School","drive 8 min"),(900,"Vail Mountain School","stay")]
day1={ (x['t'],x['field']):x for x in g if x['date']=='20260627' }
route=[]
for tt,fld,note in ROUTE:
    x=day1.get((tt,fld))
    if x: route.append({**x,'note':note})
covered=sorted(set(t for r in route for t in (r['team1'],r['team2'])))
alld1=sorted(set(t for x in g if x['date']=='20260627' for t in (x['team1'],x['team2'])))
missed=[t for t in alld1 if t not in covered]

DATA={'games':sorted(g,key=lambda r:(r['date'],r['venue'],r['field'],r['t'])),
      'route':route,'covered':covered,'missed':missed,
      'days':sorted(set((x['date'],x['dlabel']) for x in g)),
      'divisions':sorted(set(x['division'] for x in g)),
      'fields':sorted(set(x['field'] for x in g))}

HTML = """<!DOCTYPE html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Vail Lacrosse Shootout 2026 — Schedule & Photo Route</title>
<style>
:root{--bg:#0f1720;--card:#1b2430;--ink:#e7edf3;--mut:#93a4b3;--line:#2c3a4a;
--ford:#3b82f6;--ath:#10b981;--vms:#f59e0b;--edw:#a855f7;--accent:#ef4444}
*{box-sizing:border-box}body{margin:0;font:15px/1.4 -apple-system,system-ui,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--ink)}
header{padding:14px 16px;background:linear-gradient(120deg,#16202b,#0f1720);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
h1{font-size:18px;margin:0 0 2px}.sub{color:var(--mut);font-size:12px}
nav{display:flex;gap:6px;padding:8px 12px;background:var(--card);position:sticky;top:54px;z-index:4;border-bottom:1px solid var(--line)}
nav button{flex:1;padding:9px;border:0;border-radius:8px;background:#23303d;color:var(--ink);font-weight:600;font-size:14px}
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
.pill{display:inline-block;font-size:10px;padding:1px 6px;border-radius:20px;margin-left:6px;vertical-align:middle}
.Ford{border-left:4px solid var(--ford)}.Athletic{border-left:4px solid var(--ath)}
.VMS{border-left:4px solid var(--vms)}.Edwards{border-left:4px solid var(--edw)}
.legend{display:flex;gap:12px;flex-wrap:wrap;font-size:12px;color:var(--mut);margin:4px 0 10px}
.dot{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:4px;vertical-align:middle}
.routestep{display:grid;grid-template-columns:64px 1fr;gap:10px;padding:10px;border:1px solid var(--line);border-radius:10px;margin:7px 0;background:var(--card)}
.routestep .tm{font-weight:800;color:#fff}
.move{font-size:11px;color:var(--vms);margin-top:3px}
.chips{display:flex;flex-wrap:wrap;gap:5px;margin:8px 0}
.chip{background:#23303d;border:1px solid var(--line);border-radius:20px;padding:3px 9px;font-size:12px}
.chip.miss{border-color:var(--accent);color:#ffd2d2}
.note{background:#1d2733;border:1px solid var(--line);border-left:4px solid var(--vms);border-radius:8px;padding:10px 12px;margin:10px 0;font-size:13px;color:#cdd9e3}
.stat{display:flex;gap:14px;margin:8px 0;flex-wrap:wrap}
.stat div{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:8px 12px;font-size:13px}
.stat b{font-size:20px;display:block;color:#fff}
small.hint{color:var(--mut)}
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
   <div><b id=rGames></b>games</div>
   <div><b>~18</b>min travel</div>
 </div>
 <p class=sub>Optimized for <b>max distinct teams, minimal travel</b> · ~35 min per game · Sat Jun 27. All Vail-core venues (no Edwards drive today).</p>
 <div id=routeout></div>
 <div class=note id=missnote></div>
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
// filters
const fDay=document.getElementById('fDay'),fDiv=document.getElementById('fDiv'),fField=document.getElementById('fField'),fSearch=document.getElementById('fSearch');
fDay.innerHTML='<option value="">All days</option>'+D.days.map(d=>`<option value="${d[0]}">${d[1]}</option>`).join('');
fDiv.innerHTML='<option value="">All divisions</option>'+D.divisions.map(d=>`<option>${d}</option>`).join('');
fField.innerHTML='<option value="">All fields</option>'+D.fields.map(d=>`<option>${d}</option>`).join('');
fDay.value=D.days[0][0]; // default first day
function render(){
  const dy=fDay.value,dv=fDiv.value,fl=fField.value,q=fSearch.value.toLowerCase();
  let gs=D.games.filter(x=>(!dy||x.date==dy)&&(!dv||x.division==dv)&&(!fl||x.field==fl)
     &&(!q||(x.team1+' '+x.team2).toLowerCase().includes(q)));
  // group by day then field
  let out='',curDay='',curField='';
  for(const x of gs){
    if(x.date!=curDay){curDay=x.date;curField='';out+=`<h2 style="margin:18px 0 4px;font-size:16px">${x.dlabel}</h2>`}
    if(x.field!=curField){curField=x.field;out+=`<div class="fld ${loc(x.field)}" style="border-left-color:var(--${loc(x.field).toLowerCase()=='vms'?'vms':loc(x.field).toLowerCase()=='ford'?'ford':loc(x.field).toLowerCase()=='athletic'?'ath':'edw'})">${x.field} — ${x.venue}</div>`}
    out+=gcard(x);
  }
  document.getElementById('schedout').innerHTML=out||'<p class=sub>No games match.</p>';
}
[fDay,fDiv,fField].forEach(e=>e.onchange=render); fSearch.oninput=render; render();
// route
document.getElementById('rTeams').textContent=D.covered.length;
document.getElementById('rGames').textContent=D.route.length;
let ro='';for(const r of D.route){ro+=`<div class="routestep ${loc(r.field)}">
  <div><div class=tm>${r.time.replace(' ','')}</div></div>
  <div><div class=dv>${r.division} · ${r.field}</div><div class=mt>${r.team1} <small class=hint>vs</small> ${r.team2}</div>
  ${r.note&&r.note!='stay'?`<div class=move>↪ ${r.note}</div>`:''}</div></div>`}
document.getElementById('routeout').innerHTML=ro;
document.getElementById('covchips').innerHTML=D.covered.map(t=>`<span class=chip>${t}</span>`).join('');
document.getElementById('missnote').innerHTML=`<b>2 teams not reachable at 35 min/game:</b> ${D.missed.join(', ')}. `+
 `They're trapped in the 10:30–12:00 Grandmasters crunch (8 teams across 3 parallel fields). `+
 `<u>Optional sprint to bag them:</u> Ford F1 &amp; F2 are side-by-side and Athletic is a 5-min walk — `+
 `during 10:30–12:00 you can split slots (≈15–20 min each) to also catch <b>Old Big Green</b> (Ford F1) and <b>Team 41</b> (Athletic, 10:30 or the 12:00 Team 8 vs Team 41 game).`;
</script></body></html>"""

import datetime as _dt
HTML=HTML.replace("__DATA__",json.dumps(DATA)).replace("__NGAMES__",str(len(g))).replace("__TODAY__","2026-06-26")
open("/Volumes/Photography/vail_tournament.html","w").write(HTML)
print("Wrote /Volumes/Photography/vail_tournament.html")
print(f"games={len(g)} route={len(route)} covered={len(covered)} missed={missed}")

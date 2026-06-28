const CACHE='vail-lax-v2';
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

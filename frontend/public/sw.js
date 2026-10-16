const CACHE = "cnizos-v1";
const ASSETS = ["/", "/manifest.json"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(()=>self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  // Network first for API, cache first for assets
  if (url.pathname.startsWith("/api") || url.pathname.startsWith("/ws")) return;
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request).then(resp => {
      if (resp.ok && e.request.method==="GET") {
        const clone = resp.clone();
        caches.open(CACHE).then(c=>c.put(e.request, clone));
      }
      return resp;
    }).catch(()=>caches.match("/")))
  );
});

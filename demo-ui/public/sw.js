const CACHE_NAME = 'alim-pwa-v1';
const ASSETS = [
  '/',
  '/public/manifest.json',
  '/public/custom.css'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  const sameOrigin = url.origin === self.location.origin;
  const isPublicAsset = sameOrigin && (url.pathname.startsWith('/public/') ||
    ['style', 'script', 'image', 'font'].includes(req.destination));

  if (!isPublicAsset) return;

  event.respondWith(
    caches.match(req).then((cached) =>
      cached || fetch(req).then((resp) => {
        const clone = resp.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(req, clone));
        return resp;
      })
    )
  );
});

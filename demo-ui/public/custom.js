// Inject PWA manifest and register a minimal service worker.
(function registerPWA() {
  try {
    const existing = document.querySelector('link[rel="manifest"]');
    if (!existing) {
      const link = document.createElement('link');
      link.rel = 'manifest';
      link.href = '/public/manifest.json';
      document.head.appendChild(link);
    }

    const isLocalhost = Boolean(
      window.location.hostname === 'localhost' ||
        window.location.hostname === '127.0.0.1'
    );
    const isSecure = window.location.protocol === 'https:' || isLocalhost;

    if ('serviceWorker' in navigator && isSecure) {
      navigator.serviceWorker
        .register('/public/sw.js')
        .catch((err) => console.warn('PWA: service worker registration failed', err));
    }
  } catch (err) {
    console.warn('PWA bootstrap failed', err);
  }
})();

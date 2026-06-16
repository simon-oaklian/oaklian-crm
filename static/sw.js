// CRM Shell Service Worker - enables PWA install
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(clients.claim()));
// Pass all requests through; caching handled by server versioned URLs
self.addEventListener('fetch', () => {});

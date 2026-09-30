
self.addEventListener('install', (e) => {
  console.log('[PWA] Service Worker Installed');
});
self.addEventListener('fetch', (e) => {
  // Pass-through for PWA installability
});

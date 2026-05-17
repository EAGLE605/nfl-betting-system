// NFL Betting Card Service Worker
const CACHE_NAME = 'nfl-betting-card-v1';
const STATIC_CACHE = 'nfl-static-v1';
const API_CACHE = 'nfl-api-v1';

// Static assets to cache on install
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/football.svg'
];

// API routes to cache with network-first strategy
const API_ROUTES = [
  '/api/betting-card',
  '/api/picks',
  '/api/parlays',
  '/api/player-props',
  '/api/performance'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Install');
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
      .catch((err) => {
        console.error('[SW] Install failed:', err);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activate');
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => {
              return name !== STATIC_CACHE &&
                     name !== API_CACHE &&
                     name !== CACHE_NAME;
            })
            .map((name) => {
              console.log('[SW] Deleting old cache:', name);
              return caches.delete(name);
            })
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch event - handle requests
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Handle API requests with network-first strategy
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirst(request, API_CACHE));
    return;
  }

  // Handle static assets with cache-first strategy
  event.respondWith(cacheFirst(request, STATIC_CACHE));
});

// Network-first strategy for API calls
async function networkFirst(request, cacheName) {
  try {
    const networkResponse = await fetch(request);

    // Cache successful responses
    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log('[SW] Network failed, trying cache:', request.url);

    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    // Return offline response for API calls
    return new Response(
      JSON.stringify({
        error: 'Offline',
        message: 'You appear to be offline. Showing cached data.',
        offline: true
      }),
      {
        status: 503,
        statusText: 'Service Unavailable',
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

// Cache-first strategy for static assets
async function cacheFirst(request, cacheName) {
  const cachedResponse = await caches.match(request);

  if (cachedResponse) {
    // Update cache in background
    fetch(request)
      .then((response) => {
        if (response.ok) {
          caches.open(cacheName).then((cache) => {
            cache.put(request, response);
          });
        }
      })
      .catch(() => {
        // Ignore network errors for background refresh
      });

    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log('[SW] Network failed for static asset:', request.url);

    // For navigation requests, return the cached index.html
    if (request.mode === 'navigate') {
      const cachedIndex = await caches.match('/index.html');
      if (cachedIndex) {
        return cachedIndex;
      }
    }

    // Return a basic offline page
    return new Response(
      `<!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Offline - NFL Betting Card</title>
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0f;
            color: #fff;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            text-align: center;
            padding: 20px;
          }
          h1 { color: #ffd700; }
          p { color: #a0a0b0; }
          button {
            margin-top: 20px;
            padding: 12px 24px;
            background: #ffd700;
            color: #0a0a0f;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
          }
        </style>
      </head>
      <body>
        <div>
          <h1>You're Offline</h1>
          <p>Please check your internet connection and try again.</p>
          <button onclick="window.location.reload()">Retry</button>
        </div>
      </body>
      </html>`,
      {
        status: 503,
        statusText: 'Service Unavailable',
        headers: { 'Content-Type': 'text/html' }
      }
    );
  }
}

// Handle messages from the main thread
self.addEventListener('message', (event) => {
  if (event.data === 'skipWaiting') {
    self.skipWaiting();
  }

  if (event.data === 'clearCache') {
    caches.keys().then((names) => {
      names.forEach((name) => caches.delete(name));
    });
  }
});

// Background sync for offline actions (future enhancement)
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-picks') {
    console.log('[SW] Background sync triggered');
    // Could sync user preferences or favorites here
  }
});

// Push notifications (future enhancement)
self.addEventListener('push', (event) => {
  if (event.data) {
    const data = event.data.json();

    event.waitUntil(
      self.registration.showNotification(data.title || 'NFL Betting Card', {
        body: data.body || 'New picks are available!',
        icon: '/icon-192.png',
        badge: '/icon-192.png',
        vibrate: [100, 50, 100],
        data: { url: data.url || '/' }
      })
    );
  }
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  const url = event.notification.data?.url || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window' }).then((clientList) => {
      // Focus existing window if open
      for (const client of clientList) {
        if (client.url === url && 'focus' in client) {
          return client.focus();
        }
      }
      // Open new window
      return clients.openWindow(url);
    })
  );
});

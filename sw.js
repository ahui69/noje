// Service Worker for Mordzix AI PWA
const CACHE_NAME = 'mordzix-ai-v1.0.0';
const urlsToCache = [
  '/',
  '/app',
  '/dist/index.html',
  '/dist/assets/index.css',
  '/dist/assets/index.js',
  '/manifest.webmanifest'
];

// Install event
self.addEventListener('install', (event) => {
  console.log('[SW] Installing Service Worker...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Caching app shell');
        return cache.addAll(urlsToCache);
      })
      .catch((err) => console.error('[SW] Cache error:', err))
  );
  self.skipWaiting();
});

// Activate event
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating Service Worker...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch event - Network First, fallback to Cache
self.addEventListener('fetch', (event) => {
  const { request } = event;
  
  // Skip non-GET requests
  if (request.method !== 'GET') return;
  
  // Skip API calls (always go to network)
  if (request.url.includes('/api/')) {
    return fetch(request);
  }
  
  event.respondWith(
    fetch(request)
      .then((response) => {
        // Clone response to cache
        const responseToCache = response.clone();
        
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(request, responseToCache);
        });
        
        return response;
      })
      .catch(() => {
        // Network failed, try cache
        return caches.match(request).then((cachedResponse) => {
          if (cachedResponse) {
            console.log('[SW] Serving from cache:', request.url);
            return cachedResponse;
          }
          
          // Return offline page if available
          return caches.match('/offline.html');
        });
      })
  );
});

// Background Sync (for offline actions)
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync:', event.tag);
  
  if (event.tag === 'sync-messages') {
    event.waitUntil(syncMessages());
  }
});

// Push Notifications
self.addEventListener('push', (event) => {
  console.log('[SW] Push received:', event);
  
  const data = event.data ? event.data.json() : {};
  const title = data.title || 'Mordzix AI';
  const options = {
    body: data.body || 'Masz nową wiadomość',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    vibrate: [200, 100, 200],
    data: {
      url: data.url || '/'
    }
  };
  
  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Notification Click
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification click:', event);
  event.notification.close();
  
  event.waitUntil(
    clients.openWindow(event.notification.data.url || '/')
  );
});

// Helper: Sync messages when back online
async function syncMessages() {
  const db = await openDB();
  const messages = await db.getAll('pending-messages');
  
  for (const msg of messages) {
    try {
      await fetch('/api/chat/assistant', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + msg.token
        },
        body: JSON.stringify(msg.data)
      });
      
      await db.delete('pending-messages', msg.id);
    } catch (err) {
      console.error('[SW] Sync failed:', err);
    }
  }
}

// Helper: Open IndexedDB
function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('mordzix-ai', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('pending-messages')) {
        db.createObjectStore('pending-messages', { keyPath: 'id', autoIncrement: true });
      }
    };
  });
}

console.log('[SW] Service Worker loaded');

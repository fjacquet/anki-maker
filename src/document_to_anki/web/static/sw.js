/**
 * Service Worker for Document to Anki Converter
 * Provides offline support and caching for better performance
 */

const CACHE_NAME = 'document-to-anki-v1';
const STATIC_ASSETS = [
    '/',
    '/static/style.css',
    '/static/app.js'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Service Worker: Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .catch((error) => {
                console.error('Service Worker: Failed to cache static assets', error);
            })
    );
    
    // Force the waiting service worker to become the active service worker
    self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Service Worker: Deleting old cache', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    
    // Claim control of all clients
    self.clients.claim();
});

// Fetch event - serve from cache when possible
self.addEventListener('fetch', (event) => {
    // Only handle GET requests
    if (event.request.method !== 'GET') {
        return;
    }

    // Skip API requests and file uploads
    if (event.request.url.includes('/api/')) {
        return;
    }

    event.respondWith(
        caches.match(event.request)
            .then((cachedResponse) => {
                // Return cached version if available
                if (cachedResponse) {
                    return cachedResponse;
                }

                // Otherwise fetch from network
                return fetch(event.request)
                    .then((response) => {
                        // Don't cache non-successful responses
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }

                        // Clone the response for caching
                        const responseToCache = response.clone();

                        caches.open(CACHE_NAME)
                            .then((cache) => {
                                cache.put(event.request, responseToCache);
                            });

                        return response;
                    })
                    .catch((error) => {
                        console.error('Service Worker: Fetch failed', error);
                        
                        // Return a fallback response for navigation requests
                        if (event.request.mode === 'navigate') {
                            return caches.match('/');
                        }
                        
                        throw error;
                    });
            })
    );
});

// Background sync for failed uploads (if supported)
self.addEventListener('sync', (event) => {
    if (event.tag === 'background-sync-upload') {
        event.waitUntil(
            // Handle background upload retry logic here
            console.log('Service Worker: Background sync triggered for uploads')
        );
    }
});

// Push notifications (for future enhancement)
self.addEventListener('push', (event) => {
    if (event.data) {
        const data = event.data.json();
        
        const options = {
            body: data.body || 'Your flashcards are ready!',
            icon: '/static/icon-192.png',
            badge: '/static/badge-72.png',
            tag: 'flashcard-notification',
            requireInteraction: true,
            actions: [
                {
                    action: 'view',
                    title: 'View Flashcards'
                },
                {
                    action: 'dismiss',
                    title: 'Dismiss'
                }
            ]
        };

        event.waitUntil(
            self.registration.showNotification(data.title || 'Document to Anki', options)
        );
    }
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    if (event.action === 'view') {
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// Message handling for communication with main thread
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});
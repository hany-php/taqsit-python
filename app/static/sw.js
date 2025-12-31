/**
 * نظام تقسيط - Service Worker
 * PWA Support
 */

const CACHE_NAME = 'taqsit-cache-v1';
const STATIC_CACHE = 'taqsit-static-v1';
const DYNAMIC_CACHE = 'taqsit-dynamic-v1';

// الملفات الثابتة للتخزين المؤقت
const STATIC_ASSETS = [
    '/',
    '/login',
    '/static/css/style.css',
    '/static/js/app.js',
    '/static/manifest.json',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
    'https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700&display=swap',
    'https://fonts.googleapis.com/icon?family=Material+Icons+Round'
];

// تثبيت Service Worker
self.addEventListener('install', (event) => {
    console.log('[SW] Installing Service Worker...');
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('[SW] Caching static assets...');
                return cache.addAll(STATIC_ASSETS);
            })
            .catch((err) => {
                console.log('[SW] Error caching:', err);
            })
    );
    self.skipWaiting();
});

// تفعيل Service Worker
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating Service Worker...');
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.filter((key) => key !== STATIC_CACHE && key !== DYNAMIC_CACHE)
                    .map((key) => caches.delete(key))
            );
        })
    );
    self.clients.claim();
});

// استراتيجية الشبكة أولاً مع التخزين المؤقت
self.addEventListener('fetch', (event) => {
    const request = event.request;
    
    // تجاهل طلبات غير GET
    if (request.method !== 'GET') {
        return;
    }
    
    // تجاهل طلبات API
    if (request.url.includes('/api/')) {
        event.respondWith(
            fetch(request)
                .catch(() => {
                    return new Response(JSON.stringify({ error: 'أنت غير متصل بالإنترنت' }), {
                        headers: { 'Content-Type': 'application/json' }
                    });
                })
        );
        return;
    }
    
    // الملفات الثابتة - Cache First
    if (request.url.includes('/static/')) {
        event.respondWith(
            caches.match(request)
                .then((cachedResponse) => {
                    if (cachedResponse) {
                        return cachedResponse;
                    }
                    return fetch(request).then((response) => {
                        if (!response || response.status !== 200) {
                            return response;
                        }
                        const responseClone = response.clone();
                        caches.open(STATIC_CACHE).then((cache) => {
                            cache.put(request, responseClone);
                        });
                        return response;
                    });
                })
        );
        return;
    }
    
    // صفحات HTML - Network First
    event.respondWith(
        fetch(request)
            .then((response) => {
                if (!response || response.status !== 200 || response.type !== 'basic') {
                    return response;
                }
                const responseClone = response.clone();
                caches.open(DYNAMIC_CACHE).then((cache) => {
                    cache.put(request, responseClone);
                });
                return response;
            })
            .catch(() => {
                return caches.match(request).then((cachedResponse) => {
                    if (cachedResponse) {
                        return cachedResponse;
                    }
                    // صفحة offline
                    if (request.headers.get('accept').includes('text/html')) {
                        return caches.match('/');
                    }
                });
            })
    );
});

// معالجة الإشعارات
self.addEventListener('push', (event) => {
    if (event.data) {
        const data = event.data.json();
        const options = {
            body: data.body,
            icon: '/static/icons/icon-192x192.png',
            badge: '/static/icons/icon-72x72.png',
            vibrate: [100, 50, 100],
            data: {
                url: data.url || '/'
            },
            dir: 'rtl',
            lang: 'ar'
        };
        
        event.waitUntil(
            self.registration.showNotification(data.title, options)
        );
    }
});

// النقر على الإشعار
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});

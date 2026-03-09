// sw.js - Service Worker للتطبيق
const CACHE_NAME = 'jewel-app-v1';
const API_CACHE_NAME = 'jewel-api-v1';

// الملفات التي سيتم تخزينها مؤقتاً عند التثبيت
const urlsToCache = [
    '/',
    '/dashboard',
    '/employees',
    '/attendance',
    '/evaluations',
    '/static/css/style.css',
    '/static/js/app.js',
    '/static/js/db.js',
    '/static/js/sync.js',
    '/manifest.json'
];

// 📦 التثبيت - تخزين الملفات الأساسية
self.addEventListener('install', event => {
    console.log('✅ Service Worker installing...');

    // Force activation
    self.skipWaiting();

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('📦 Caching app shell...');
                return cache.addAll(urlsToCache);
            })
            .catch(error => {
                console.error('❌ Cache failed:', error);
            })
    );
});

// 🔄 التفعيل - تنظيف الكاش القديم
self.addEventListener('activate', event => {
    console.log('✅ Service Worker activated');

    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME) {
                        console.log('🗑️ Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            // التحكم فوراً في جميع الصفحات المفتوحة
            return self.clients.claim();
        })
    );
});

// 🌐 التعامل مع الطلبات
self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // تجاهل طلبات المتصفح الداخلية
    if (event.request.url.includes('chrome-extension')) {
        return;
    }

    // استراتيجية Cache First للملفات الثابتة
    if (url.pathname.startsWith('/static/') ||
        url.pathname.endsWith('.js') ||
        url.pathname.endsWith('.css')) {

        event.respondWith(
            caches.match(event.request)
                .then(response => {
                    if (response) {
                        return response; // من الكاش
                    }
                    return fetch(event.request).then(networkResponse => {
                        // تخزين النسخة الجديدة
                        const responseClone = networkResponse.clone();
                        caches.open(CACHE_NAME).then(cache => {
                            cache.put(event.request, responseClone);
                        });
                        return networkResponse;
                    });
                })
                .catch(() => {
                    // فشل كل شيء - إرجاع صفحة خطأ بسيطة
                    return new Response('Network error happened', {
                        status: 408,
                        headers: { 'Content-Type': 'text/plain' }
                    });
                })
        );
        return;
    }

    // استراتيجية Network First لصفحات HTML
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    // تخزين نسخة من الصفحة
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, responseClone);
                    });
                    return response;
                })
                .catch(() => {
                    // إذا فشل الاتصال، أرجع الصفحة المخزنة
                    return caches.match(event.request).then(cachedResponse => {
                        if (cachedResponse) {
                            return cachedResponse;
                        }
                        // إذا لم توجد صفحة مخزنة، أرجع الصفحة الرئيسية
                        return caches.match('/');
                    });
                })
        );
        return;
    }

    // استراتيجية خاصة لطلبات API
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    // تخزين نسخة من استجابة API
                    const responseClone = response.clone();
                    caches.open(API_CACHE_NAME).then(cache => {
                        cache.put(event.request, responseClone);
                    });
                    return response;
                })
                .catch(() => {
                    // إذا فشل الاتصال، أرجع آخر نسخة مخزنة
                    return caches.match(event.request).then(cachedResponse => {
                        if (cachedResponse) {
                            return cachedResponse;
                        }
                        // إذا لم توجد، أرجع رسالة خطأ منسقة
                        return new Response(JSON.stringify({
                            success: false,
                            message: 'أنت غير متصل بالإنترنت',
                            offline: true
                        }), {
                            status: 503,
                            headers: { 'Content-Type': 'application/json' }
                        });
                    });
                })
        );
        return;
    }

    // استراتيجية افتراضية للملفات الأخرى
    event.respondWith(
        fetch(event.request)
            .catch(() => caches.match(event.request))
    );
});

// 🔄 المزامنة في الخلفية
self.addEventListener('sync', event => {
    console.log('🔄 Background sync triggered:', event.tag);

    if (event.tag === 'sync-data') {
        event.waitUntil(syncData());
    }
});

// 📨 استقبال الرسائل من الصفحة
self.addEventListener('message', event => {
    console.log('📨 Message received:', event.data);

    if (event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }

    if (event.data.type === 'SYNC_NOW') {
        event.waitUntil(syncData());
    }
});

// 🔄 دالة المزامنة الفعلية
async function syncData() {
    console.log('🔄 Starting background sync...');

    try {
        // فتح قاعدة البيانات المحلية
        const db = await openDB();

        // جلب التغييرات غير المتزامنة
        const pendingChanges = await getPendingChanges(db);

        if (pendingChanges.length === 0) {
            console.log('✅ No pending changes to sync');
            return;
        }

        console.log(`📤 Syncing ${pendingChanges.length} changes...`);

        // إرسال التغييرات للخادم
        const response = await fetch('/api/sync/push', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ changes: pendingChanges })
        });

        const result = await response.json();

        if (result.success) {
            // حذف التغييرات المتزامنة
            await clearSyncedChanges(db, result.results.synced);

            console.log('✅ Sync completed successfully');

            // إرسال إشعار للمستخدم
            self.registration.showNotification('تمت المزامنة', {
                body: `تمت مزامنة ${result.results.synced.length} تغيير بنجاح`,
                icon: '/static/img/icon-192.png',
                badge: '/static/img/badge-72.png',
                vibrate: [200, 100, 200]
            });

            // إعلام جميع الصفحات المفتوحة
            const clients = await self.clients.matchAll();
            clients.forEach(client => {
                client.postMessage({
                    type: 'SYNC_COMPLETED',
                    count: result.results.synced.length
                });
            });
        }
    } catch (error) {
        console.error('❌ Sync failed:', error);

        // محاولة إعادة المزامنة لاحقاً
        self.registration.sync.register('sync-data');
    }
}

// 📁 دوال مساعدة للتعامل مع IndexedDB في Service Worker
function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('JewelAppDB', 1);

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);

        request.onupgradeneeded = (event) => {
            const db = event.target.result;

            if (!db.objectStoreNames.contains('pending_changes')) {
                const store = db.createObjectStore('pending_changes', {
                    keyPath: 'local_id',
                    autoIncrement: true
                });
                store.createIndex('synced', 'synced', { unique: false });
            }
        };
    });
}

function getPendingChanges(db) {
    return new Promise((resolve, reject) => {
        const tx = db.transaction('pending_changes', 'readonly');
        const store = tx.objectStore('pending_changes');
        const index = store.index('synced');
        const request = index.getAll(IDBKeyRange.only(false));

        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

function clearSyncedChanges(db, syncedItems) {
    return new Promise((resolve, reject) => {
        const tx = db.transaction('pending_changes', 'readwrite');
        const store = tx.objectStore('pending_changes');

        syncedItems.forEach(item => {
            if (item.local_id) {
                store.delete(item.local_id);
            }
        });

        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error);
    });
}

// 📱 التعامل مع الإشعارات
self.addEventListener('notificationclick', event => {
    console.log('🔔 Notification clicked:', event.notification.tag);

    event.notification.close();

    // فتح التطبيق عند النقر على الإشعار
    event.waitUntil(
        clients.openWindow('/')
    );
});

// 📦 التعامل مع الدفع (Push Notifications) - اختياري
self.addEventListener('push', event => {
    console.log('📨 Push received:', event.data ? event.data.text() : 'no data');

    const data = event.data.json();

    const options = {
        body: data.body || 'تحديث جديد في التطبيق',
        icon: '/static/img/icon-192.png',
        badge: '/static/img/badge-72.png',
        vibrate: [200, 100, 200],
        data: {
            url: data.url || '/'
        }
    };

    event.waitUntil(
        self.registration.showNotification(data.title || 'أرض الجوهرة', options)
    );
});
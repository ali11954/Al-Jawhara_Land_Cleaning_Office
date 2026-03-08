// static/js/sync.js
class SyncManager {
    constructor() {
        this.isSyncing = false;
    }

    async addPendingChange(type, data, action = 'create') {
        if (!offlineDB.db) await offlineDB.init();

        return new Promise((resolve, reject) => {
            const tx = offlineDB.db.transaction('pending_changes', 'readwrite');
            const store = tx.objectStore('pending_changes');

            const change = {
                type: type,
                action: action,
                data: data,
                timestamp: new Date().toISOString(),
                synced: false
            };

            const request = store.add(change);

            request.onsuccess = () => {
                console.log(`✅ Added to sync queue: ${type}`);
                resolve(request.result);
            };
            request.onerror = () => reject(request.error);
        });
    }

    async sync() {
        if (this.isSyncing) return;
        if (!navigator.onLine) {
            this.showNotification('warning', 'لا يوجد اتصال بالإنترنت');
            return;
        }

        this.isSyncing = true;
        this.showSyncIndicator('جاري المزامنة...');

        try {
            // جلب التغييرات المحلية
            const tx = offlineDB.db.transaction('pending_changes', 'readonly');
            const store = tx.objectStore('pending_changes');
            const index = store.index('synced');

            const pendingChanges = await new Promise((resolve, reject) => {
                const request = index.getAll(IDBKeyRange.only(false));
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
            });

            if (pendingChanges.length > 0) {
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
                    const deleteTx = offlineDB.db.transaction('pending_changes', 'readwrite');
                    const deleteStore = deleteTx.objectStore('pending_changes');

                    result.results.synced.forEach(item => {
                        if (item.local_id) {
                            deleteStore.delete(item.local_id);
                        }
                    });

                    this.showNotification('success', `تمت مزامنة ${result.results.synced.length} تغيير`);
                }
            } else {
                this.showNotification('info', 'لا توجد تغييرات للمزامنة');
            }
        } catch (error) {
            console.error('Sync error:', error);
            this.showNotification('error', 'فشلت المزامنة');
        } finally {
            this.isSyncing = false;
            this.hideSyncIndicator();
        }
    }

    showSyncIndicator(message) {
        let indicator = document.getElementById('sync-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'sync-indicator';
            indicator.className = 'sync-indicator';
            document.body.appendChild(indicator);
        }
        indicator.innerHTML = `
            <div class="spinner"></div>
            <span>${message}</span>
        `;
        indicator.style.display = 'flex';
    }

    hideSyncIndicator() {
        const indicator = document.getElementById('sync-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }

    showNotification(type, message) {
        const notification = document.createElement('div');
        notification.className = `sync-notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span>${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span>
                <span>${message}</span>
            </div>
        `;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }
}

const syncManager = new SyncManager();
// static/js/app.js
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 تطبيق أرض الجوهرة - النسخة غير المتصلة');

    // تهيئة التخزين المحلي
    await offlineDB.init();

    // مراقبة حالة الاتصال
    updateConnectionStatus(navigator.onLine);

    window.addEventListener('online', () => {
        console.log('📶 تم الاتصال بالإنترنت');
        updateConnectionStatus(true);
        syncManager.sync();
    });

    window.addEventListener('offline', () => {
        console.log('📴 انقطع الاتصال');
        updateConnectionStatus(false);
    });

    // تسجيل Service Worker
    if ('serviceWorker' in navigator) {
        try {
            const registration = await navigator.serviceWorker.register('/sw.js');
            console.log('✅ Service Worker registered');
        } catch (error) {
            console.log('❌ Service Worker registration failed:', error);
        }
    }
});

function updateConnectionStatus(isOnline) {
    let statusBar = document.getElementById('connection-status');
    if (!statusBar) {
        statusBar = document.createElement('div');
        statusBar.id = 'connection-status';
        document.body.appendChild(statusBar);
    }

    if (isOnline) {
        statusBar.className = 'online';
        statusBar.innerHTML = `
            <span>📶 متصل بالإنترنت</span>
            <button onclick="syncManager.sync()">مزامنة</button>
        `;
    } else {
        statusBar.className = 'offline';
        statusBar.innerHTML = '📴 وضع عدم الاتصال - التغييرات محفوظة محلياً';
    }
}

// دوال مساعدة لحفظ البيانات محلياً
async function saveEmployeeLocally(employeeData) {
    const localId = await syncManager.addPendingChange('employee', employeeData);
    await offlineDB.save('employees', {
        ...employeeData,
        id: employeeData.id || `local_${localId}`,
        _local_id: localId
    });
    return localId;
}

async function saveAttendanceLocally(attendanceData) {
    const localId = await syncManager.addPendingChange('attendance', attendanceData);
    await offlineDB.save('attendance', {
        ...attendanceData,
        id: attendanceData.id || `local_${localId}`,
        _local_id: localId
    });
    return localId;
}
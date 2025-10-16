from app import app, db
from models import create_tables, initialize_default_data
import os

# تهيئة قاعدة البيانات عند التشغيل
with app.app_context():
    print("🚀 بدء تهيئة التطبيق...")

    # 1. إنشاء الجداول
    create_tables()

    # 2. إنشاء البيانات الافتراضية
    initialize_default_data()

    print("✅ تم تهيئة التطبيق بنجاح")

# هذا هو المتغير الذي يبحث عنه Gunicorn
application = app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
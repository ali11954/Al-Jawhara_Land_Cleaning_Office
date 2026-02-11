from app import app, db
# من الأفضل ترك الاستيراد لتجنّب الخطأ عند التنفيذ
# from models import create_tables, initialize_default_data
import os

with app.app_context():
    print("🚀 بدء تشغيل التطبيق بدون إنشاء جداول جديدة...")

    # ❌ علّق الأسطر التالية بعد النشر
    # create_tables()
    # initialize_default_data()

    print("✅ تم تشغيل التطبيق بنجاح")

application = app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)

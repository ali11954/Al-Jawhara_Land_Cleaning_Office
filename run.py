from app import app, db
from models import User
import os

with app.app_context():
    print("🚀 بدء تشغيل التطبيق...")

    # ✅ إنشاء الجداول تلقائياً
    db.create_all()
    print("✅ تم إنشاء الجداول بنجاح")

    # ✅ إنشاء المستخدم الافتراضي
    if not User.query.filter_by(username='owner').first():
        owner = User(
            username='owner',
            email='owner@aljwahrh.com',
            role='owner',
            is_active=True
        )
        owner.set_password('admin123')
        db.session.add(owner)
        db.session.commit()
        print("✅ تم إنشاء مستخدم owner/admin123")
    else:
        print("✅ المستخدم owner موجود مسبقاً")

application = app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
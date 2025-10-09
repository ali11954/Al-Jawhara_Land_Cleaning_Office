from app import app, initialize_database

if __name__ == '__main__':
    # Initialize database
    initialize_database()

    print("=" * 60)
    print("🚀 بدء تشغيل تطبيق أرض الجوهرة للنظافة...")
    print("📊 يمكنك الوصول للتطبيق على: http://localhost:5000")
    print("👤 اسم المستخدم: owner")
    print("🔑 كلمة المرور: admin123")
    print("=" * 60)

    # تشغيل التطبيق
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        threaded=True
    )
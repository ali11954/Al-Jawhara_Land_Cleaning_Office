from app import app #initialize_database
import os

#def initialize_app():
 #   """تهيئة التطبيق للنشر على Render"""
  #  print("=" * 60)
   # print("🔄 جاري تحميل تطبيق أرض الجوهرة للنظافة...")
    #print(f"🌐 بيئة: {'Production' if not app.config['DEBUG'] else 'Development'}")
    #print(
    #    f"📊 قاعدة البيانات: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[-1] if '@' in app.config['SQLALCHEMY_DATABASE_URI'] else 'SQLite'}"
    #)
    #print("=" * 60)

    # محاولة تهيئة قاعدة البيانات
    #try:
     #   print("🔧 جاري تهيئة قاعدة البيانات...")
        #success = initialize_database()
        #if success:
         #   print("✅ تم تهيئة النظام بنجاح")
        #else:
         #   print("⚠️ تم تحميل التطبيق مع تحذيرات")
    #except Exception as e:
     #   print(f"⚠️ ملاحظة: {e}")
      #  print("🔁 النظام جاهز، سيتم إنشاء الجداول عند الحاجة")

# تهيئة التطبيق
#initialize_app()

# ✅ تصحيح: استخدام application لـ Gunicorn على Render
application = app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 التشغيل على المنفذ: {port}")
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])

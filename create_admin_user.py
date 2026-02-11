# create_admin_user.py
from app import app
from models import db, User, Employee, Company, Area, Location, Place
from datetime import date
from werkzeug.security import generate_password_hash
import os

def create_initial_data():
    """إنشاء البيانات الأساسية للنظام"""
    with app.app_context():
        try:
            print("=" * 60)
            print("🔧 بدء إنشاء البيانات الأساسية...")
            print("=" * 60)

            # 1️⃣ حذف قاعدة البيانات القديمة إذا كانت موجودة
            db_path = 'instance/cleaning_company.db'
            if os.path.exists(db_path):
                print(f"🗑️  حذف قاعدة البيانات القديمة...")
                os.remove(db_path)
                print("✅ تم حذف قاعدة البيانات القديمة")

            # 2️⃣ إنشاء جميع الجداول
            print("📦 إنشاء جداول قاعدة البيانات...")
            db.create_all()
            print("✅ تم إنشاء الجداول بنجاح")

            # 3️⃣ إنشاء شركة افتراضية
            print("\n🏢 إنشاء الشركة...")
            company = Company(
                name="شركة أرض الجوهرة للنظافة",
                address="الرياض، المملكة العربية السعودية",
                contact_person="الإدارة العامة",
                phone="+966500000000",
                email="info@ard-aljawharah.com",
                is_active=True
            )
            db.session.add(company)
            db.session.flush()
            print(f"✅ تم إنشاء الشركة: {company.name} (ID: {company.id})")

            # 4️⃣ إنشاء المستخدمين والموظفين
            print("\n👥 إنشاء المستخدمين والموظفين...")

            # --- المالك (owner) ---
            owner_user = User(
                username="owner",
                email="owner@ard-aljawharah.com",
                role="owner",
                is_active=True
            )
            owner_user.set_password("admin123")  # ✅ كلمة المرور: admin123
            db.session.add(owner_user)
            db.session.flush()
            print(f"✅ تم إنشاء مستخدم المالك: {owner_user.username} / admin123")

            owner_employee = Employee(
                user_id=owner_user.id,
                full_name="مالك النظام",
                phone="+966500000001",
                position="owner",
                salary=15000.0,
                hire_date=date.today(),
                is_active=True
            )
            db.session.add(owner_employee)
            print("✅ تم إنشاء ملف الموظف للمالك")

            # --- المشرف (supervisor) ---
            supervisor_user = User(
                username="supervisor",
                email="supervisor@ard-aljawharah.com",
                role="supervisor",
                is_active=True
            )
            supervisor_user.set_password("supervisor123")
            db.session.add(supervisor_user)
            db.session.flush()
            print(f"✅ تم إنشاء مستخدم المشرف: supervisor / supervisor123")

            supervisor_employee = Employee(
                user_id=supervisor_user.id,
                full_name="أحمد محمد",
                phone="+966500000002",
                position="supervisor",
                salary=8000.0,
                hire_date=date.today(),
                is_active=True
            )
            db.session.add(supervisor_employee)
            db.session.flush()
            print("✅ تم إنشاء ملف الموظف للمشرف")

            # --- المراقب (monitor) ---
            monitor_user = User(
                username="monitor",
                email="monitor@ard-aljawharah.com",
                role="monitor",
                is_active=True
            )
            monitor_user.set_password("monitor123")
            db.session.add(monitor_user)
            db.session.flush()
            print(f"✅ تم إنشاء مستخدم المراقب: monitor / monitor123")

            monitor_employee = Employee(
                user_id=monitor_user.id,
                full_name="خالد سعيد",
                phone="+966500000003",
                position="monitor",
                salary=5000.0,
                hire_date=date.today(),
                is_active=True
            )
            db.session.add(monitor_employee)
            db.session.flush()
            print("✅ تم إنشاء ملف الموظف للمراقب")

            # --- العامل (worker) ---
            worker_user = User(
                username="worker",
                email="worker@ard-aljawharah.com",
                role="worker",
                is_active=True
            )
            worker_user.set_password("worker123")
            db.session.add(worker_user)
            db.session.flush()
            print(f"✅ تم إنشاء مستخدم العامل: worker / worker123")

            worker_employee = Employee(
                user_id=worker_user.id,
                full_name="علي حسن",
                phone="+966500000004",
                position="worker",
                salary=3000.0,
                hire_date=date.today(),
                is_active=True
            )
            db.session.add(worker_employee)
            print("✅ تم إنشاء ملف الموظف للعامل")

            # 5️⃣ إنشاء المناطق والمواقع والأماكن
            print("\n📍 إنشاء الهيكل التنظيمي...")

            # منطقة رئيسية
            main_area = Area(
                name="المنطقة الرئيسية",
                company_id=company.id,
                supervisor_id=supervisor_employee.id,
                is_active=True
            )
            db.session.add(main_area)
            db.session.flush()
            print(f"✅ تم إنشاء المنطقة: {main_area.name}")

            # موقع إداري
            admin_location = Location(
                name="المبنى الإداري",
                area_id=main_area.id,
                monitor_id=monitor_employee.id,
                is_active=True
            )
            db.session.add(admin_location)
            db.session.flush()
            print(f"✅ تم إنشاء الموقع: {admin_location.name}")

            # أماكن متنوعة
            places_list = [
                "المكتب الرئيسي",
                "قاعة الاجتماعات",
                "المطبخ",
                "دورات المياه",
                "الممرات",
                "المدخل الرئيسي",
                "غرفة الأرشيف",
                "المستودع"
            ]

            for place_name in places_list:
                place = Place(
                    name=place_name,
                    location_id=admin_location.id,
                    worker_id=worker_employee.id,
                    is_active=True
                )
                db.session.add(place)

            print(f"✅ تم إنشاء {len(places_list)} مكان")

            # 6️⃣ حفظ جميع التغييرات
            db.session.commit()
            print("\n" + "=" * 60)
            print("✅✅✅ تم إنشاء جميع البيانات بنجاح! ✅✅✅")
            print("=" * 60)
            print("\n📋 ملخص البيانات:")
            print(f"   👤 المستخدمين: 4")
            print(f"   🏢 الشركات: 1")
            print(f"   📍 المناطق: 1")
            print(f"   📌 المواقع: 1")
            print(f"   🏠 الأماكن: {len(places_list)}")
            print("\n🔑 معلومات تسجيل الدخول:")
            print("   ┌─────────────────┬─────────────────┐")
            print("   │    اسم المستخدم │    كلمة المرور │")
            print("   ├─────────────────┼─────────────────┤")
            print("   │           owner │       admin123 │")
            print("   │      supervisor │   supervisor123 │")
            print("   │         monitor │      monitor123 │")
            print("   │          worker │       worker123 │")
            print("   └─────────────────┴─────────────────┘")
            print("\n🌐 يمكنك الآن تسجيل الدخول على: http://localhost:5000")
            print("=" * 60)

        except Exception as e:
            db.session.rollback()
            print(f"\n❌❌❌ خطأ: {str(e)}")
            import traceback
            print(f"🔍 تفاصيل الخطأ: {traceback.format_exc()}")
            return False

        return True

if __name__ == "__main__":
    create_initial_data()
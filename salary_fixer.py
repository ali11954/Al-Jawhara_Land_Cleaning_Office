# salary_fixer.py
from app import app
from models import db, Employee, Salary
from sqlalchemy import event


def fix_salary(salary):
    """تحديث راتب واحد بالقيم الصحيحة حسب نوع الموظف"""
    try:
        emp = Employee.query.get(salary.employee_id)
        if not emp:
            return False

        # للمشرفين - حساب بسيط
        if emp.employee_type != 'worker':
            if salary.attendance_days and salary.attendance_days > 0:
                daily_rate = (emp.salary or 60000) / 30
                salary.attendance_amount = daily_rate * salary.attendance_days
                salary.total_salary = salary.attendance_amount
                salary.basic_salary_amount = salary.attendance_amount
                print(f'   ✅ {emp.name} (مشرف): {salary.total_salary:,.0f} ريال')
            return True

        # للعمال
        if not salary.attendance_days or salary.attendance_days == 0:
            return False

        # ========== المبالغ الثابتة الصحيحة ==========
        MONTHLY_DAYS = 30
        BASE_WORKER = 60000  # المبلغ المستحق للعامل لـ 30 يوم

        # القيم اليومية
        DAILY_RATE = BASE_WORKER / MONTHLY_DAYS  # 2,000 ريال/يوم
        DAILY_RESIDENT = 500  # بدل السكن اليومي للساكنين

        # البدلات السنوية
        CLOTHING_YEARLY = 24400  # 24,400 ريال سنوياً
        HEALTH_YEARLY = 15000  # 15,000 ريال سنوياً
        INSURANCE_MONTHLY = 10800  # 10,800 ريال شهرياً

        days = salary.attendance_days
        ratio = days / MONTHLY_DAYS

        # حساب التوزيع
        basic = DAILY_RATE * days  # الراتب الأساسي

        # بدل السكن - فقط للساكنين
        if emp.is_resident:
            resident = DAILY_RESIDENT * days  # 500 ريال × عدد الأيام
        else:
            resident = 0

        cash = basic + resident  # المبلغ النقدي للعامل

        # البدلات (تحسب نسبياً حسب الأيام)
        clothing = (CLOTHING_YEARLY / 12) * ratio  # بدل الملابس شهرياً
        health = (HEALTH_YEARLY / 12) * ratio  # بطاقة صحية شهرياً
        insurance = INSURANCE_MONTHLY * ratio  # تأمين شهرياً

        # ربح المتعهد
        diff = emp.salary - BASE_WORKER
        profit = (diff * ratio) - (clothing + health + insurance)

        # تحديث الراتب - التأكد من عدم وجود None
        salary.basic_salary_amount = basic or 0
        salary.resident_allowance_amount = resident or 0
        salary.clothing_allowance_amount = clothing or 0
        salary.health_card_amount = health or 0
        salary.insurance_amount = insurance or 0
        salary.contractor_profit = profit or 0
        salary.attendance_amount = cash or 0
        salary.total_salary = cash or 0

        print(f'   ✅ {emp.name} (عامل): {cash:,.0f} ريال')
        print(f'      أساسي: {basic:,.0f} + سكن: {resident:,.0f}')
        print(f'      بدل ملابس: {clothing:,.0f} | بطاقة صحية: {health:,.0f} | تأمين: {insurance:,.0f}')
        print(f'      ربح المتعهد: {profit:,.0f} ريال')
        return True

    except Exception as e:
        print(f'   ❌ خطأ في تحديث راتب الموظف ID {salary.employee_id}: {str(e)}')
        return False


# استماع للأحداث - عند إضافة راتب جديد
@event.listens_for(Salary, 'before_insert')
def before_salary_insert(mapper, connection, target):
    print(f'\n🔧 إصلاح راتب جديد تلقائياً...')
    fix_salary(target)


# استماع للأحداث - عند تحديث راتب موجود
@event.listens_for(Salary, 'before_update')
def before_salary_update(mapper, connection, target):
    # فقط إذا كان الراتب لم يتم توزيعه بعد
    if target.basic_salary_amount == 0 or target.basic_salary_amount is None:
        print(f'\n🔧 إصلاح راتب محدث تلقائياً...')
        fix_salary(target)


def fix_all_existing_salaries():
    """تحديث جميع الرواتب الموجودة حالياً"""
    with app.app_context():
        print('\n' + '=' * 60)
        print('🔧 تحديث جميع الرواتب الموجودة...')
        print('=' * 60)

        salaries = Salary.query.all()
        count = 0
        for salary in salaries:
            if fix_salary(salary):
                count += 1
                db.session.add(salary)

        db.session.commit()
        print('=' * 60)
        print(f'✅ تم تحديث {count} راتب بنجاح')
        print('=' * 60)


def init_salary_fixer():
    """تهيئة مصحح الرواتب - يستدعى عند بدء التشغيل"""
    with app.app_context():
        print("\n" + "=" * 60)
        print("🚀 تهيئة نظام تصحيح الرواتب")
        print("=" * 60)

        # تحديث الرواتب الموجودة
        fix_all_existing_salaries()

        print("\n✅ نظام تصحيح الرواتب جاهز!")
        print("   - سيتم تصحيح أي راتب جديد تلقائياً")
        print("   - سيتم تحديث الرواتب المعدلة تلقائياً")
        print("=" * 60)


# تشغيل التهيئة عند تحميل الملف
if __name__ == "__main__":
    init_salary_fixer()
else:
    # عند استيراد الملف كوحدة، نقوم بالتهيئة التلقائية
    with app.app_context():
        # تحديث سريع للرواتب الموجودة (بدون طباعة كثيرة)
        salaries = Salary.query.filter(
            (Salary.basic_salary_amount == 0) | (Salary.basic_salary_amount.is_(None))
        ).all()

        if salaries:
            print(f"\n🔧 تصحيح {len(salaries)} راتب موجود...")
            for salary in salaries:
                fix_salary(salary)
            db.session.commit()
            print(f"✅ تم تصحيح {len(salaries)} راتب")
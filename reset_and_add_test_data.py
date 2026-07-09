# add_test_data_fixed.py
from app import app, db
from models import (
    User, Employee, Company, Contract, Invoice, Salary,
    MealDeduction, Penalty, EmployeeLoan, Overtime
)
from datetime import date
import random

with app.app_context():
    print("=" * 70)
    print("📦 إضافة بيانات تجريبية (نسخة آمنة)")
    print("=" * 70)

    # 1. إنشاء شركات (إذا لم تكن موجودة)
    print("\n1️⃣ إنشاء الشركات:")

    company1 = Company.query.filter_by(name="الشركة اليمنية لتكرير السكر").first()
    if not company1:
        company1 = Company(
            name="الشركة اليمنية لتكرير السكر",
            address="الحديدة",
            contact_person="أحمد علي",
            phone="123456789",
            company_type="customer",
            is_active=True
        )
        db.session.add(company1)
        print(f"   ✅ {company1.name}")
    else:
        print(f"   ⚠️ {company1.name} موجود مسبقاً")

    company2 = Company.query.filter_by(name="مؤسسة المواد الغذائية").first()
    if not company2:
        company2 = Company(
            name="مؤسسة المواد الغذائية",
            address="صنعاء",
            contact_person="محمد عبدالله",
            phone="987654321",
            company_type="supplier",
            is_active=True
        )
        db.session.add(company2)
        print(f"   ✅ {company2.name}")
    else:
        print(f"   ⚠️ {company2.name} موجود مسبقاً")

    db.session.flush()

    # 2. إنشاء موظفين (بتوليد رموز فريدة)
    print("\n2️⃣ إنشاء الموظفين:")

    # جلب آخر رقم مستخدم
    last_emp = Employee.query.order_by(Employee.id.desc()).first()
    next_num = 1
    if last_emp and last_emp.code and last_emp.code.startswith('EMP'):
        try:
            next_num = int(last_emp.code[3:]) + 1
        except:
            next_num = 1

    employees_data = [
        {"name": "أحمد محمد", "position": "supervisor", "salary": 80000, "resident": False},
        {"name": "خالد علي", "position": "worker", "salary": 60000, "resident": True},
        {"name": "سعيد أحمد", "position": "worker", "salary": 60000, "resident": False},
    ]

    emp_objects = []
    for i, data in enumerate(employees_data):
        code = f"EMP{next_num + i:03d}"
        emp = Employee.query.filter_by(full_name=data["name"]).first()

        if not emp:
            emp = Employee(
                code=code,
                full_name=data["name"],
                position=data["position"],
                salary=data["salary"],
                hire_date=date.today(),
                is_active=True,
                is_resident=data["resident"]
            )
            db.session.add(emp)
            print(f"   ✅ {emp.full_name} ({emp.position}) - كود: {emp.code}")
        else:
            print(f"   ⚠️ {emp.full_name} موجود مسبقاً")

        emp_objects.append(emp)

    db.session.flush()

    # 3. إنشاء سلف (إذا لم تكن موجودة)
    print("\n3️⃣ إنشاء السلف:")

    for emp in emp_objects:
        if emp.position == "worker":
            existing_loan = EmployeeLoan.query.filter_by(employee_id=emp.id).first()
            if not existing_loan:
                loan = EmployeeLoan(
                    employee_id=emp.id,
                    loan_date=date.today(),
                    amount=3000,
                    installments=3,
                    monthly_installment=1000,
                    paid_amount=0,
                    remaining=3000,
                    reason="سلفة شخصية",
                    status="active"
                )
                loan.calculate_installment()
                db.session.add(loan)
                print(f"   ✅ {emp.full_name}: 3000 ريال")
            else:
                print(f"   ⚠️ {emp.full_name}: سلفة موجودة مسبقاً")

    # 4. إنشاء جزاءات (إذا لم تكن موجودة)
    print("\n4️⃣ إنشاء الجزاءات:")

    for emp in emp_objects:
        if emp.position == "worker":
            existing_penalty = Penalty.query.filter_by(employee_id=emp.id).first()
            if not existing_penalty:
                penalty = Penalty(
                    employee_id=emp.id,
                    penalty_date=date.today(),
                    year=date.today().year,
                    month=date.today().month,
                    amount=random.choice([150, 200, 250]),
                    reason="تأخير",
                    is_deducted=False
                )
                db.session.add(penalty)
                print(f"   ✅ {emp.full_name}: {penalty.amount} ريال")
            else:
                print(f"   ⚠️ {emp.full_name}: جزاء موجود مسبقاً")

    # 5. إنشاء خصميات بوفية
    print("\n5️⃣ إنشاء خصميات البوفية:")

    for emp in emp_objects:
        if emp.position == "worker":
            existing_meal = MealDeduction.query.filter_by(employee_id=emp.id).first()
            if not existing_meal:
                meal = MealDeduction(
                    employee_id=emp.id,
                    deduction_type="cafeteria",
                    amount=random.choice([100, 150, 200]),
                    deduction_date=date.today(),
                    description="وجبات بوفية",
                    is_transferred=False
                )
                db.session.add(meal)
                print(f"   ✅ {emp.full_name}: {meal.amount} ريال (بوفية)")
            else:
                print(f"   ⚠️ {emp.full_name}: خصم بوفية موجود مسبقاً")

    # 6. إنشاء ساعات إضافية
    print("\n6️⃣ إنشاء الساعات الإضافية:")

    for emp in emp_objects:
        if emp.position == "worker":
            existing_overtime = Overtime.query.filter_by(employee_id=emp.id).first()
            if not existing_overtime:
                hours = random.choice([2, 3, 4, 5])
                cost = hours * 25
                overtime = Overtime(
                    employee_id=emp.id,
                    overtime_date=date.today(),
                    year=date.today().year,
                    month=date.today().month,
                    hours=hours,
                    rate=25,
                    cost=cost,
                    reason="عمل إضافي",
                    is_transferred=False
                )
                db.session.add(overtime)
                print(f"   ✅ {emp.full_name}: {hours} ساعات = {cost} ريال")
            else:
                print(f"   ⚠️ {emp.full_name}: ساعات إضافية موجودة مسبقاً")

    db.session.commit()

    print("\n" + "=" * 70)
    print("🎉 تم إضافة البيانات التجريبية بنجاح!")
    print("=" * 70)
    print("\n📌 ملاحظات:")
    print("   - جميع الخصومات غير مرحلة (is_transferred=False)")
    print("   - جميع السلف نشطة (status='active')")
    print("   - يمكنك الآن حساب الرواتب")
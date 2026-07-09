import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, date, time, timedelta
import random

from app import create_app
from models import (
    db, User, Employee, Attendance, Evaluation, Company, Region, Location,
    Contract, Invoice, FinancialTransaction, Account, Supplier, JournalEntry,
    JournalEntryDetail, Salary
)

def seed():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        # ── Accounts (Chart of Accounts) ──
        accounts = []
        account_data = [
            ('1000', 'Cash', 'الصندوق', 'asset', 'debit'),
            ('1010', 'Petty Cash', 'الصندوق الصغير', 'asset', 'debit'),
            ('1020', 'Bank Account', 'الحساب البنكي', 'asset', 'debit'),
            ('1030', 'Accounts Receivable', 'العملاء', 'asset', 'debit'),
            ('1100', 'Suppliers Payable', 'الموردون', 'liability', 'credit'),
            ('1110', 'Tax Payable', 'الضرائب المستحقة', 'liability', 'credit'),
            ('1200', 'Capital', 'رأس المال', 'equity', 'credit'),
            ('1210', 'Retained Earnings', 'الأرباح المحتجزة', 'equity', 'credit'),
            ('2000', 'Revenue - Cleaning Services', 'إيرادات خدمات النظافة', 'revenue', 'credit'),
            ('2010', 'Revenue - Contracts', 'إيرادات العقود', 'revenue', 'credit'),
            ('2020', 'Revenue - Other', 'إيرادات أخرى', 'revenue', 'credit'),
            ('3000', 'Salaries Expense', 'مصاريف الرواتب', 'expense', 'debit'),
            ('3010', 'Materials Expense', 'مصاريف المواد', 'expense', 'debit'),
            ('3020', 'Transportation Expense', 'مصاريف النقل', 'expense', 'debit'),
            ('3030', 'Utilities Expense', 'مصاريف المرافق', 'expense', 'debit'),
            ('3040', 'Rent Expense', 'مصاريف الإيجار', 'expense', 'debit'),
            ('3050', 'Insurance Expense', 'مصاريف التأمين', 'expense', 'debit'),
            ('3060', 'Miscellaneous Expense', 'مصاريف متنوعة', 'expense', 'debit'),
        ]
        for code, name, name_ar, atype, nature in account_data:
            a = Account(code=code, name=name, name_ar=name_ar, account_type=atype, nature=nature)
            db.session.add(a)
            accounts.append(a)
        db.session.flush()

        acc = {a.code: a.id for a in accounts}

        # ── Companies ──
        companies_data = [
            ('شركة النظافة المتحدة', 'محمد أحمد السالم', '771234567', 'united@example.com'),
            ('مؤسسة النقاء', 'عبدالله حسين المرزوق', '773456789', 'nqaa@example.com'),
            ('شركة التميز للخدمات', 'علي سالم الحمادي', '775678901', 'tamayuz@example.com'),
        ]
        companies = []
        for name, cp, phone, email in companies_data:
            c = Company(name=name, contact_person=cp, phone=phone, email=email)
            db.session.add(c)
            companies.append(c)
        db.session.flush()

        # ── Regions ──
        regions_data = [
            ('مدينة الحديدة', companies[0].id),
            ('المنطقة الصناعية', companies[0].id),
            ('حي السلام', companies[1].id),
            ('حي الزهراء', companies[1].id),
            ('منطقة الكدسة', companies[2].id),
            ('حي النصر', companies[2].id),
        ]
        regions = []
        for name, cid in regions_data:
            r = Region(name=name, company_id=cid)
            db.session.add(r)
            regions.append(r)
        db.session.flush()

        # ── Locations ──
        locations_data = [
            ('المبنى الرئيسي', regions[0].id, 'شارع الملك عبدالله'),
            ('المستشفى المركزي', regions[0].id, 'شارع الزرقاء'),
            ('مبنى البلدية', regions[1].id, 'المنطقة الصناعية'),
            ('المدرسة الثانوية', regions[2].id, 'حي السلام'),
            ('المسكن السكني 1', regions[3].id, 'حي الزهراء'),
            ('المبنى التجاري', regions[4].id, 'منطقة الكدسة'),
            ('نادي المدينة', regions[5].id, 'حي النصر'),
        ]
        locations = []
        for name, rid, addr in locations_data:
            l = Location(name=name, region_id=rid, address=addr)
            db.session.add(l)
            locations.append(l)
        db.session.flush()

        # ── Employees ──
        employees_data = [
            ('EMP001', 'أحمد محمد الهرملي', '771112233', 'الحديدة', 'supervisor', 120000, 120000, date(2023, 1, 15), regions[0].id, companies[0].id, None),
            ('EMP002', 'محمد عبدالله الجرمي', '772223344', 'الحديدة', 'عامل نظافة', 60000, 60000, date(2023, 3, 1), regions[0].id, companies[0].id, 1),
            ('EMP003', 'سعيد علي المعمري', '773334455', 'حي السلام', 'عامل نظافة', 60000, 60000, date(2023, 5, 10), regions[2].id, companies[0].id, 1),
            ('EMP004', 'عبدالرحمن حسين الدوسري', '774445566', 'المنطقة الصناعية', 'supervisor', 130000, 130000, date(2023, 2, 20), regions[1].id, companies[0].id, None),
            ('EMP005', 'ياسر سالم الشميري', '775556677', 'حي الزهراء', 'عامل نظافة', 55000, 55000, date(2024, 1, 5), regions[3].id, companies[1].id, 4),
            ('EMP006', 'حسن محمد البكري', '776667788', 'حي النصر', 'عامل نظافة', 58000, 58000, date(2024, 2, 15), regions[5].id, companies[2].id, None),
            ('EMP007', 'عمر عبدالله العتيبي', '777778899', 'منطقة الكدسة', 'supervisor', 125000, 125000, date(2023, 6, 1), regions[4].id, companies[2].id, None),
            ('EMP008', 'خالد أحمد الفضلي', '778889900', 'الحديدة', 'عامل نظافة', 57000, 57000, date(2024, 3, 1), regions[0].id, companies[0].id, 1),
            ('EMP009', 'يوسف علي الحارثي', '779990011', 'حي السلام', 'عامل نظافة', 60000, 60000, date(2024, 4, 10), regions[2].id, companies[1].id, 4),
            ('EMP010', 'فهد محمد الزهراني', '770001122', 'المنطقة الصناعية', 'عامل نظافة', 55000, 55000, date(2024, 5, 20), regions[1].id, companies[0].id, 4),
            ('EMP011', 'طارق سالم الملا', '771113344', 'حي الزهراء', 'supervisor', 128000, 128000, date(2023, 7, 1), regions[3].id, companies[1].id, None),
            ('EMP012', 'وائل عبدالله القحطاني', '772224455', 'حي النصر', 'عامل نظافة', 56000, 56000, date(2025, 1, 1), regions[5].id, companies[2].id, 7),
            ('EMP013', 'نبيل أحمد العمراني', '773335566', 'منطقة الكدسة', 'عامل نظافة', 59000, 59000, date(2025, 2, 15), regions[4].id, companies[2].id, 7),
            ('EMP014', 'ماجد علي الشمري', '774446677', 'الحديدة', 'عامل نظافة', 62000, 62000, date(2023, 8, 1), regions[0].id, companies[0].id, 1),
            ('EMP015', 'سلطان حسين الدوسري', '775557788', 'حي السلام', 'supervisor', 135000, 135000, date(2023, 4, 1), regions[2].id, companies[1].id, None),
        ]
        employees = []
        for code, name, phone, addr, pos, sal, tsal, hdate, rid, cid, sid in employees_data:
            e = Employee(
                code=code, full_name=name, phone=phone, address=addr,
                position=pos, salary=sal, total_salary=tsal, hire_date=hdate,
                region_id=rid, company_id=cid, supervisor_id=sid,
                is_active=True, worker_type='permanent', daily_allowance=500,
                basic_salary=2000, clothing_allowance=24480,
                health_card_allowance=15000, monthly_insurance=10800,
            )
            db.session.add(e)
            employees.append(e)
        db.session.flush()

        # ── Users ──
        users = [
            User(username='admin', password='admin123', full_name='المدير العام', role='admin', is_active=True),
            User(username='accountant', password='acc123', full_name='محاسب النظام', role='accountant', is_active=True),
            User(username='supervisor1', password='sup123', full_name='مشرف الموقع', role='supervisor', is_active=True, employee_id=employees[0].id),
        ]
        for u in users:
            db.session.add(u)
        db.session.flush()

        # ── Attendance (2 weeks for all employees) ──
        start_date = date(2026, 7, 1)
        statuses = ['present', 'present', 'present', 'present', 'late', 'absent']
        for emp in employees:
            for day_offset in range(14):
                d = start_date + timedelta(days=day_offset)
                if d.weekday() >= 5:  # skip Fri/Sat
                    continue
                status = random.choice(statuses)
                late = random.randint(5, 30) if status == 'late' else 0
                ci = time(7, random.randint(0, 30)) if status != 'absent' else None
                co = time(15, random.randint(0, 30)) if status != 'absent' else None
                att = Attendance(
                    employee_id=emp.id, date=d, attendance_status=status,
                    late_minutes=late, check_in_time=ci, check_out_time=co,
                    sick_leave=(status == 'absent'),
                    sick_leave_days=1 if status == 'absent' and random.random() < 0.3 else 0,
                )
                db.session.add(att)
        db.session.flush()

        # ── Evaluations ──
        eval_types = ['أداء عام', 'تقييم دوري', 'تقييم ميداني']
        for emp in employees:
            score = random.randint(5, 10)
            ev = Evaluation(
                employee_id=emp.id, evaluation_type=random.choice(eval_types),
                score=score, comments='تقييم جيد' if score >= 7 else 'يحتاج تحسين',
                date=date(2026, 7, random.randint(1, 15)),
                region_id=emp.region_id,
            )
            db.session.add(ev)
        db.session.flush()

        # ── Contracts ──
        contracts_data = [
            ('CON-2026-001', companies[0].id, 'annual', 4800000, 400000, date(2026, 1, 1), date(2026, 12, 31), 2400000, 2400000),
            ('CON-2026-002', companies[1].id, 'annual', 3600000, 300000, date(2026, 3, 1), date(2027, 2, 28), 1800000, 1800000),
            ('CON-2026-003', companies[2].id, 'monthly', 600000, 600000, date(2026, 6, 1), date(2026, 6, 30), 600000, 0),
        ]
        contracts = []
        for cnum, cid, ctype, cv, mv, sd, ed, ar, ra in contracts_data:
            c = Contract(
                contract_number=cnum, company_id=cid, contract_type=ctype,
                contract_value=cv, monthly_value=mv, start_date=sd, end_date=ed,
                amount_received=ar, remaining_amount=ra, status='active', is_active=True,
            )
            db.session.add(c)
            contracts.append(c)
        db.session.flush()

        # ── Invoices ──
        invoices_data = [
            (contracts[0].id, 'INV-2026-001', 400000, date(2026, 7, 1), date(2026, 7, 15), True, date(2026, 7, 10), 400000, 'تحويل بنكي', 'فترة يوليو - العقد 001'),
            (contracts[0].id, 'INV-2026-002', 400000, date(2026, 7, 15), date(2026, 7, 30), False, None, 0, None, 'فترة أغسطس - العقد 001'),
            (contracts[1].id, 'INV-2026-003', 300000, date(2026, 7, 1), date(2026, 7, 20), True, date(2026, 7, 5), 300000, 'نقدي', 'فترة يوليو - العقد 002'),
            (contracts[2].id, 'INV-2026-004', 600000, date(2026, 6, 1), date(2026, 6, 15), True, date(2026, 6, 12), 600000, 'شيك', 'فترة يونيو - العقد 003'),
        ]
        for cid, inum, amt, idt, ddt, paid, pddt, pamt, pm, desc in invoices_data:
            inv = Invoice(
                contract_id=cid, invoice_number=inum, amount=amt,
                invoice_date=idt, due_date=ddt, is_paid=paid,
                paid_date=pddt, paid_amount=pamt, payment_method=pm, description=desc,
            )
            db.session.add(inv)
        db.session.flush()

        # ── Suppliers ──
        suppliers_data = [
            ('Al-Huda Cleaning Supplies', 'شركة النظافة المتحدة للمواد', 'محمد عبدالمجيد', '771001001', 'chemicals', 'شارع صنعاء'),
            ('Gulf Materials Trading', 'شركة خليج المواد التجارية', 'حسن أحمد', '772002002', 'general', 'شارع الحديدة'),
            ('National Equipment Co', 'شركة المعدات الوطنية', 'علي محمد', '773003003', 'equipment', 'شارع التحرير'),
        ]
        suppliers = []
        for name, name_ar, cp, phone, stype, addr in suppliers_data:
            s = Supplier(name=name, name_ar=name_ar, contact_person=cp, phone=phone, supplier_type=stype, address=addr)
            db.session.add(s)
            suppliers.append(s)
        db.session.flush()

        # ── Journal Entries & Financial Transactions ──
        journal_entries_data = [
            ('JE-2026-001', date(2026, 7, 1), 'إيراد خدمات نظافة يوليو - شركة النظافة المتحدة'),
            ('JE-2026-002', date(2026, 7, 5), 'إيراد خدمات نظافة يوليو - مؤسسة النقاء'),
            ('JE-2026-003', date(2026, 7, 10), 'صرف رواتب يونيو 2026'),
            ('JE-2026-004', date(2026, 7, 12), 'شراء مواد تنظيف'),
            ('JE-2026-005', date(2026, 7, 15), 'إيراد خدمات نظافة - شركة التميز'),
            ('JE-2026-006', date(2026, 7, 20), 'مصاريف نقل وأجور'),
            ('JE-2026-007', date(2026, 7, 25), 'إيراد عقد شهري - شركة التميز'),
        ]
        entries = []
        for enum, edate, edesc in journal_entries_data:
            je = JournalEntry(entry_number=enum, date=edate, description=edesc, is_posted=True)
            db.session.add(je)
            entries.append(je)
        db.session.flush()

        # Journal Entry Details
        details_data = [
            (entries[0].id, acc['1030'], 0, 400000, 'عملاء - شركة النظافة المتحدة'),
            (entries[0].id, acc['2000'], 400000, 0, 'إيرادات خدمات النظافة'),
            (entries[1].id, acc['1030'], 0, 300000, 'عملاء - مؤسسة النقاء'),
            (entries[1].id, acc['2000'], 300000, 0, 'إيرادات خدمات النظافة'),
            (entries[2].id, acc['3000'], 500000, 0, 'مصاريف الرواتب - يونيو'),
            (entries[2].id, acc['1000'], 0, 500000, 'الصندوق - دفع رواتب'),
            (entries[3].id, acc['3010'], 75000, 0, 'مصاريف المواد - شركة النظافة المتحدة'),
            (entries[3].id, acc['1000'], 0, 75000, 'الصندوق - شراء مواد'),
            (entries[4].id, acc['1000'], 600000, 0, 'الصندوق - إيراد عقد شهري'),
            (entries[4].id, acc['2010'], 0, 600000, 'إيرادات العقود'),
            (entries[5].id, acc['3020'], 45000, 0, 'مصاريف النقل'),
            (entries[5].id, acc['1000'], 0, 45000, 'الصندوق - مصاريف نقل'),
            (entries[6].id, acc['1000'], 600000, 0, 'الصندوق - إيراد عقد شهري'),
            (entries[6].id, acc['2010'], 0, 600000, 'إيرادات العقود'),
        ]
        for eid, aid, dr, cr, desc in details_data:
            jed = JournalEntryDetail(entry_id=eid, account_id=aid, debit=dr, credit=cr, description=desc)
            db.session.add(jed)
        db.session.flush()

        # Financial Transactions
        ft_data = [
            (employees[0].id, 'income', 400000, date(2026, 7, 1), 'إيراد خدمات نظافة - شركة النظافة المتحدة', True, date(2026, 7, 1), 'تحويل بنكي'),
            (employees[0].id, 'income', 300000, date(2026, 7, 5), 'إيراد خدمات نظافة - مؤسسة النقاء', True, date(2026, 7, 5), 'نقدي'),
            (employees[0].id, 'expense', 500000, date(2026, 7, 10), 'صرف رواتب يونيو 2026', True, date(2026, 7, 10), 'تحويل بنكي'),
            (employees[0].id, 'expense', 75000, date(2026, 7, 12), 'شراء مواد تنظيف من شركة النظافة المتحدة', True, date(2026, 7, 12), 'نقدي'),
            (employees[0].id, 'expense', 45000, date(2026, 7, 15), 'مصاريف نقل وأجور', True, date(2026, 7, 15), 'نقدي'),
            (employees[0].id, 'income', 600000, date(2026, 7, 20), 'إيراد عقد شهري - شركة التميز', True, date(2026, 7, 20), 'شيك'),
            (employees[0].id, 'expense', 30000, date(2026, 7, 22), 'مصاريف متنوعة', False, None, 'نقدي'),
            (employees[0].id, 'expense', 25000, date(2026, 7, 25), 'فواتير كهرباء وماء', True, date(2026, 7, 25), 'تحويل بنكي'),
            (employees[0].id, 'income', 200000, date(2026, 7, 28), 'دفعة مقدمة من مؤسسة النقاء', True, date(2026, 7, 28), 'نقدي'),
            (employees[0].id, 'expense', 15000, date(2026, 7, 29), 'صيانة معدات التنظيف', False, None, 'نقدي'),
            (employees[0].id, 'expense', 12000, date(2026, 7, 30), 'مصاريف اتصالات', True, date(2026, 7, 30), 'تحويل بنكي'),
            (employees[0].id, 'income', 50000, date(2026, 7, 31), 'إيراد خدمات إضافية', False, None, 'نقدي'),
        ]
        for eid, ttype, amt, dt, desc, settled, sd, pm in ft_data:
            ft = FinancialTransaction(
                employee_id=eid, transaction_type=ttype, amount=amt,
                date=dt, description=desc, is_settled=settled,
                settled_date=sd, payment_method=pm,
            )
            db.session.add(ft)
        db.session.flush()

        # ── Salaries ──
        for emp in employees:
            sal = Salary(
                employee_id=emp.id, month_year='07-2026',
                base_salary=emp.salary, attendance_days=22,
                attendance_amount=emp.salary,
                daily_allowance_amount=500 * 22,
                total_salary=emp.salary + 500 * 22,
                is_paid=True, paid_date=date(2026, 7, 10),
                payment_method='تحويل بنكي',
                is_calculated=True, calculated_at=datetime.now(),
            )
            db.session.add(sal)
        db.session.flush()

        db.session.commit()

        # ── Summary ──
        counts = {
            'Users': User.query.count(),
            'Employees': Employee.query.count(),
            'Companies': Company.query.count(),
            'Regions': Region.query.count(),
            'Locations': Location.query.count(),
            'Attendance': Attendance.query.count(),
            'Evaluations': Evaluation.query.count(),
            'Contracts': Contract.query.count(),
            'Invoices': Invoice.query.count(),
            'Suppliers': Supplier.query.count(),
            'Accounts': Account.query.count(),
            'Journal Entries': JournalEntry.query.count(),
            'Journal Entry Details': JournalEntryDetail.query.count(),
            'Financial Transactions': FinancialTransaction.query.count(),
            'Salaries': Salary.query.count(),
        }

        print('\n[OK] Database seeded successfully!')
        print('=' * 50)
        for table, count in counts.items():
            print(f'  {table:30s} {count:4d} rows')
        print('=' * 50)


if __name__ == '__main__':
    seed()

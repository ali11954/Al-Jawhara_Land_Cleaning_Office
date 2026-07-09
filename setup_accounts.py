# setup_accounts.py
from app import app, db
from models import Account


def create_accounts():
    accounts = [
        # الأصول (Assets)
        ('110001', 'Cash', 'الصندوق', 'asset', 'debit', 0),
        ('110002', 'Bank Account', 'البنك', 'asset', 'debit', 0),
        ('120001', 'Customers', 'العملاء', 'asset', 'debit', 0),
        ('130001', 'Advances', 'السلف', 'asset', 'debit', 0),
        ('130003', 'Cafeteria Deduction Receivable', 'مستحق خصم البوفية', 'asset', 'debit', 0),
        ('130004', 'Restaurant Deduction Receivable', 'مستحق خصم المطعم', 'asset', 'debit', 0),

        # الخصوم (Liabilities)
        ('210001', 'Salaries Payable', 'الرواتب المستحقة', 'liability', 'credit', 0),
        ('210002', 'Overtime Payable', 'مستحقات الإضافي', 'liability', 'credit', 0),
        ('220001', 'Suppliers', 'الدائنون - موردين', 'liability', 'credit', 0),
        ('220002', 'Tax Payable', 'ضريبة مستحقة', 'liability', 'credit', 0),
        ('220003', 'Zakat Payable', 'زكاة مستحقة', 'liability', 'credit', 0),
        ('220006', 'Cafeteria Supplier', 'دائن البوفية', 'liability', 'credit', 0),
        ('220007', 'Restaurant Supplier', 'دائن المطعم', 'liability', 'credit', 0),
        ('221001', 'Clothing Allowance Payable', 'مستحق بدل ملابس العمال', 'liability', 'credit', 0),
        ('221002', 'Health Cards Payable', 'مستحق بطائق صحية للعمال', 'liability', 'credit', 0),
        ('221003', 'Insurance Payable', 'مستحق تأمين العمال', 'liability', 'credit', 0),
        ('230001', 'Accrued Revenue', 'إيرادات مستحقة', 'liability', 'credit', 0),

        # حقوق الملكية (Equity)
        ('310001', 'Capital', 'رأس المال', 'equity', 'credit', 0),
        ('320001', 'Retained Earnings', 'الأرباح المحتجزة', 'equity', 'credit', 0),

        # الإيرادات (Revenue)
        ('410001', 'Annual Contract Revenue', 'إيرادات العقود السنوية', 'revenue', 'credit', 0),
        ('410002', 'Monthly Contract Revenue', 'إيرادات العقود الشهرية', 'revenue', 'credit', 0),
        ('410003', 'Quarterly Contract Revenue', 'إيرادات العقود الربع سنوية', 'revenue', 'credit', 0),
        ('410004', 'Additional Invoices Revenue', 'إيرادات الفواتير الإضافية', 'revenue', 'credit', 0),
        ('411001', 'Contractor Profit', 'ربح المتعهد', 'revenue', 'credit', 0),

        # المصروفات (Expenses)
        ('510001', 'Salaries Expense', 'مصروف الرواتب', 'expense', 'debit', 0),
        ('510002', 'Deductions Expense', 'مصروف الخصومات والجزاءات', 'expense', 'debit', 0),
        ('510003', 'Overtime Expense', 'مصروف الإضافي', 'expense', 'debit', 0),
        ('511001', 'Labor Basic Salary', 'مصروف رواتب العمال الأساسية', 'expense', 'debit', 0),
        ('511002', 'Labor Resident Allowance', 'مصروف بدل سكن العمال', 'expense', 'debit', 0),
        ('511003', 'Labor Insurance', 'مصروف تأمين العمال', 'expense', 'debit', 0),
        ('511004', 'Labor Clothing Allowance', 'مصروف بدل ملابس العمال', 'expense', 'debit', 0),
        ('511005', 'Labor Health Cards', 'مصروف بطائق صحية للعمال', 'expense', 'debit', 0),
        ('511009', 'Cafeteria Expense', 'مصروف وجبات البوفية للعمال', 'expense', 'debit', 0),
        ('511010', 'Restaurant Expense', 'مصروف وجبات المطعم للعمال', 'expense', 'debit', 0),
        ('520001', 'Company Services Expense', 'مصروف خدمات الشركات', 'expense', 'debit', 0),
        ('521001', 'Contractor Tax', 'مصروف ضريبة المتعهدين', 'expense', 'debit', 0),
        ('521002', 'Contractor Zakat', 'مصروف زكاة المتعهدين', 'expense', 'debit', 0),
        ('530001', 'Utilities Expense', 'كهرباء وماء', 'expense', 'debit', 0),
        ('530002', 'Rent Expense', 'إيجار', 'expense', 'debit', 0),
        ('530003', 'Office Supplies', 'مستلزمات مكتبية', 'expense', 'debit', 0),
        ('530004', 'Equipment Expense', 'معدات وأدوات', 'expense', 'debit', 0),
        ('530005', 'General Expense', 'مصروفات عامة', 'expense', 'debit', 0),
    ]

    with app.app_context():
        created = 0
        for code, name, name_ar, account_type, nature, opening_balance in accounts:
            if not Account.query.filter_by(code=code).first():
                account = Account(
                    code=code, name=name, name_ar=name_ar,
                    account_type=account_type, nature=nature,
                    opening_balance=opening_balance, is_active=True
                )
                db.session.add(account)
                created += 1
        db.session.commit()
        print(f"✅ تم إنشاء {created} حساب محاسبي")


if __name__ == '__main__':
    create_accounts()
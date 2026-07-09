from app import app, db
from models import Account, Company

with app.app_context():
    print("="*60)
    print("💰 الكشف المالي")
    print("="*60)

    # البنك
    bank = Account.query.filter_by(code='110002').first()
    if bank:
        print(f"\n🏦 البنك: {bank.get_balance():,.2f} ر.ي")

    # العملاء العام
    customers = Account.query.filter_by(code='120001').first()
    if customers:
        print(f"👥 العملاء (حساب عام): {customers.get_balance():,.2f} ر.ي")

    # الحسابات الفرعية للشركات
    print(f"\n🏢 حسابات الشركات الفرعية:")
    companies = Company.query.all()
    total = 0
    for company in companies:
        if company.receivable_account_id:
            acc = Account.query.get(company.receivable_account_id)
            balance = acc.get_balance()
            total += balance
            print(f"   {company.name}: {balance:,.2f} ر.ي ({acc.code})")

    print(f"   إجمالي المستحقات: {total:,.2f} ر.ي")

    # الإيرادات
    print(f"\n💰 الإيرادات:")
    revenues = Account.query.filter(Account.account_type == 'revenue').all()
    for rev in revenues:
        balance = rev.get_balance()
        if balance != 0:
            print(f"   {rev.name_ar}: {balance:,.2f} ر.ي ({rev.code})")
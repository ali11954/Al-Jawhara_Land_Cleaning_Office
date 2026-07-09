#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# استيراد من التطبيق نفسه (هذا يحل المشكلة)
from app import app, db
from models import Account, JournalEntry, JournalEntryDetail, Contract, Company, Supplier

def main():
    with app.app_context():
        print("="*60)
        print("🔍 فحص القيود المحاسبية القديمة")
        print("="*60)

        # 1. فحص حساب العملاء العام
        general_cust = Account.query.filter_by(code='120001').first()
        if general_cust:
            details = JournalEntryDetail.query.filter(
                JournalEntryDetail.account_id == general_cust.id,
                JournalEntryDetail.debit > 0
            ).all()
            print(f"\n📌 قيود على حساب العملاء العام (120001): {len(details)}")
            
            for d in details[:10]:
                entry = JournalEntry.query.get(d.entry_id)
                if entry:
                    print(f"  - قيد: {entry.entry_number} | التاريخ: {entry.date} | النوع: {entry.reference_type}")
        else:
            print("\n❌ حساب العملاء العام (120001) غير موجود")

        # 2. فحص الشركات
        companies = Company.query.all()
        print(f"\n📌 عدد الشركات الكلي: {len(companies)}")
        
        companies_without_sub = [c for c in companies if not c.receivable_account_id]
        print(f"شركات بدون حساب فرعي: {len(companies_without_sub)}")
        for c in companies_without_sub[:5]:
            print(f"  - {c.name} (ID: {c.id})")

        # 3. فحص العقود
        contracts = Contract.query.all()
        print(f"\n📌 عدد العقود الكلي: {len(contracts)}")
        
        for contract in contracts[:10]:
            company = contract.company
            if company:
                has_sub = "✅" if company.receivable_account_id else "❌"
                print(f"  {has_sub} عقد: {contract.contract_number} | شركة: {company.name} | حساب فرعي: {company.receivable_account_id}")

        # 4. فحص القيود المرتبطة بالعقود
        entries = JournalEntry.query.filter_by(reference_type='contract').all()
        print(f"\n📌 عدد القيود المرتبطة بالعقود: {len(entries)}")
        
        for entry in entries[:10]:
            contract = Contract.query.get(entry.reference_id)
            if contract and contract.company:
                company = contract.company
                print(f"  - قيد: {entry.entry_number} | شركة: {company.name} | حساب الشركة الفرعي: {company.receivable_account_id}")

        print("\n✅ اكتمل الفحص")

if __name__ == '__main__':
    main()
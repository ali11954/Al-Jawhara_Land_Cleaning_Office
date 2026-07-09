#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# استخدام نفس قاعدة البيانات الموجودة في المشروع
database_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'cleaning_company.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# استيراد النماذج من ملف models.py
from models import Account, JournalEntry, JournalEntryDetail, Contract, Company, Supplier, SupplierInvoice

with app.app_context():
    print("=" * 60)
    print("🔍 فحص القيود المحاسبية القديمة")
    print("=" * 60)

    # 1. فحص حسابات العملاء
    general_cust = Account.query.filter_by(code='120001').first()
    if general_cust:
        details = JournalEntryDetail.query.filter(
            JournalEntryDetail.account_id == general_cust.id,
            JournalEntryDetail.debit > 0
        ).all()
        print(f"\n📌 قيود على حساب العملاء العام (120001): {len(details)}")

        problematic = 0
        for d in details[:20]:
            entry = JournalEntry.query.get(d.entry_id)
            if entry and entry.reference_type == 'contract':
                contract = Contract.query.get(entry.reference_id)
                if contract and contract.company:
                    company = contract.company
                    if company.receivable_account_id:
                        problematic += 1
                        print(f"  ⚠️ عقد {contract.contract_number} | شركة {company.name} | قيد {entry.entry_number}")
        if problematic > 0:
            print(f"  → منها تحتاج تصحيح: {problematic}")
        else:
            print("  ✅ لا توجد عقود تحتاج تصحيح")
    else:
        print("❌ حساب العملاء العام غير موجود")

    # 2. فحص الشركات بدون حسابات فرعية
    companies_no_sub = Company.query.filter(
        (Company.receivable_account_id == None) | (Company.receivable_account_id == 0)
    ).all()
    print(f"\n📌 شركات بدون حساب فرعي: {len(companies_no_sub)}")
    for c in companies_no_sub[:10]:
        print(f"  - {c.name} (ID: {c.id})")

    # 3. فحص فواتير الموردين
    general_supp = Account.query.filter_by(code='220001').first()
    if general_supp:
        details = JournalEntryDetail.query.filter(
            JournalEntryDetail.account_id == general_supp.id,
            JournalEntryDetail.credit > 0
        ).all()
        print(f"\n📌 قيود على حساب الدائنون العام (220001): {len(details)}")
    else:
        print("\n❌ حساب الدائنون العام غير موجود")

    # 4. إحصائية عامة
    total_entries = JournalEntry.query.count()
    total_contracts = Contract.query.count()
    total_companies = Company.query.count()

    print("\n" + "=" * 60)
    print("📊 إحصائيات عامة")
    print("=" * 60)
    print(f"إجمالي القيود المحاسبية: {total_entries}")
    print(f"إجمالي العقود: {total_contracts}")
    print(f"إجمالي الشركات: {total_companies}")

    print("\n✅ اكتمل الفحص")
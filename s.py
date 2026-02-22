@app.route('/fix-monthly-summary-table')
@login_required
def fix_monthly_summary_table():
    """إصلاح جدول الملخص الشهري بإضافة الأعمدة المفقودة"""
    if current_user.role != 'owner':
        return "غير مصرح", 403

    try:
        from sqlalchemy import inspect, text

        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('monthly_financial_summary')]

        added_columns = []

        # إضافة عمود company_id إذا لم يكن موجوداً
        if 'company_id' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text(
                    "ALTER TABLE monthly_financial_summary ADD COLUMN company_id INTEGER REFERENCES clean_companies(id)"))
                conn.commit()
            added_columns.append('company_id')
            print("✅ تم إضافة عمود company_id")

        # التحقق من وجود أعمدة أخرى قد تكون مفقودة
        expected_columns = [
            'total_base_salaries', 'total_overtime', 'total_penalties',
            'total_loan_deductions', 'gross_profit'
        ]

        for col in expected_columns:
            if col not in columns:
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text(f"ALTER TABLE monthly_financial_summary ADD COLUMN {col} FLOAT DEFAULT 0"))
                        conn.commit()
                    added_columns.append(col)
                    print(f"✅ تم إضافة عمود {col}")
                except Exception as e:
                    print(f"⚠️ خطأ في إضافة {col}: {str(e)}")

        if added_columns:
            return f"""
            <div style='direction: rtl; padding: 20px;'>
                <div style='background: #d4edda; color: #155724; padding: 20px; border-radius: 10px;'>
                    <h2>✅ تم تحديث قاعدة البيانات بنجاح</h2>
                    <p>تم إضافة الأعمدة التالية:</p>
                    <ul>{''.join([f'<li>{col}</li>' for col in added_columns])}</ul>
                    <a href="/financial/monthly-closing" style="background: #4e73df; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 20px;">
                        العودة للإغلاق الشهري
                    </a>
                </div>
            </div>
            """
        else:
            return """
            <div style='direction: rtl; padding: 20px;'>
                <div style='background: #fff3cd; color: #856404; padding: 20px; border-radius: 10px;'>
                    <h2>ℹ️ جميع الأعمدة موجودة بالفعل</h2>
                    <p>لم يتم إضافة أي أعمدة جديدة.</p>
                    <a href="/financial/monthly-closing" style="background: #4e73df; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 20px;">
                        العودة للإغلاق الشهري
                    </a>
                </div>
            </div>
            """

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return f"""
        <div style='direction: rtl; padding: 20px;'>
            <div style='background: #f8d7da; color: #721c24; padding: 20px; border-radius: 10px;'>
                <h2>❌ خطأ في تحديث قاعدة البيانات</h2>
                <p>{str(e)}</p>
                <pre style='background: #fff; padding: 10px; border-radius: 5px; overflow: auto;'>{error_details}</pre>
            </div>
        </div>
        """, 500
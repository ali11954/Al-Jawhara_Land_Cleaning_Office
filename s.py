# أضف هذا المسار المؤقت في app.py
@app.route('/reset-db')
@login_required
def reset_database():
    """إعادة تعيين قاعدة البيانات (للبيئة التطويرية فقط)"""
    if current_user.role != 'owner':
        flash('غير مصرح بهذا الإجراء', 'error')
        return redirect(url_for('dashboard'))

    try:
        # حذف جميع الجداول
        db.drop_all()
        # إنشاء الجداول من جديد
        db.create_all()
        # إعادة إنشاء البيانات الافتراضية
        from models import initialize_default_data
        initialize_default_data()

        flash('✅ تم إعادة تعيين قاعدة البيانات بنجاح', 'success')
    except Exception as e:
        flash(f'❌ خطأ: {str(e)}', 'error')

    return redirect(url_for('dashboard'))
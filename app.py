from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Employee, Company, Area, Location, Place, CleaningEvaluation, Attendance ,SupervisorEvaluation, Payroll, Penalty,MonthlyFinancialSummary,OtherIncome,CompanyInvoice,LoanInstallment,EmployeeLoan
from config import Config
from datetime import datetime, date, timedelta
import json
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest
import os
import humanize
from babel.dates import format_timedelta
import arabic_reshaper
from bidi.algorithm import get_display
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response
# تفعيل العربية في humanize

# ✅ تصحيح: إنشاء تطبيق واحد فقط واستخدام config.py
app = Flask(__name__)
app.config.from_object(Config)
from flask_migrate import Migrate
migrate = Migrate(app, db)

from datetime import datetime, date
from flask import Flask
import humanize
from babel.dates import format_timedelta
import arabic_reshaper
from bidi.algorithm import get_display

from functools import wraps  # أضف هذا السطر مع الاستيرادات

import traceback
import sys


@app.errorhandler(500)
def handle_500_error(e):
    """معالج مخصص لأخطاء 500"""
    print("\n" + "=" * 70)
    print("❌ حدث خطأ 500 في السيرفر!")
    print("=" * 70)
    print("🔍 تفاصيل الخطأ:")
    print(f"   نوع الخطأ: {type(e).__name__}")
    print(f"   رسالة الخطأ: {str(e)}")
    print("-" * 70)
    print("📋 traceback الكامل:")
    traceback.print_exc()
    print("=" * 70 + "\n")

    # إعادة الخطأ مع تفاصيل أكثر
    return jsonify({
        'success': False,
        'error': str(e),
        'error_type': type(e).__name__,
        'message': 'حدث خطأ داخلي في السيرفر'
    }), 500

# دوال التحقق من الصلاحيات
def check_permission(permission_name):
    """التحقق من صلاحية المستخدم الحالي"""
    if not current_user.is_authenticated:
        return False
    if current_user.role == 'owner':
        return True
    return getattr(current_user, permission_name, False)


def permission_required(permission_name):
    """ديكوريتور للتحقق من الصلاحية"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('يجب تسجيل الدخول أولاً', 'error')
                return redirect(url_for('login'))

            if not check_permission(permission_name):
                flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
                return redirect(url_for('dashboard'))

            return f(*args, **kwargs)

        return decorated_function

    return decorator


@app.route('/force-fix-permissions')
@login_required
def force_fix_permissions():
    """إصلاح قوي للصلاحيات - يعيد تعيين جلسة المستخدم"""
    if current_user.role != 'owner':
        flash('غير مصرح', 'error')
        return redirect(url_for('dashboard'))

    # البحث عن المستخدم abdaullah
    user = User.query.filter_by(username='abdaullah').first()
    if not user:
        return "المستخدم abdaullah غير موجود"

    # تعيين جميع الصلاحيات يدوياً
    user.can_view_employees = True
    user.can_edit_employees = True
    user.can_add_employees = True
    user.can_delete_employees = True
    user.can_view_attendance = True
    user.can_record_attendance = True
    user.can_view_attendance_reports = True
    user.can_view_evaluations = True
    user.can_add_evaluations = True
    user.can_view_evaluation_reports = True
    user.can_view_detailed_evaluations = True
    user.can_view_performance = True
    user.can_view_top_employees = True
    user.can_view_employee_efficiency = True
    user.can_view_companies = True
    user.can_view_company_stats = True
    user.can_view_zones = True
    user.can_view_salaries = True
    user.can_view_salary_reports = True
    user.can_view_financial = True
    user.can_view_invoices = True
    user.can_view_penalties = True
    user.can_view_dashboard = True
    user.can_view_kpis = True
    user.can_view_heatmap = True
    user.can_manage_users = True
    user.can_manage_roles = True

    db.session.commit()

    # إعادة تحميل المستخدم في الجلسة
    from flask_login import login_user
    login_user(user)

    return f"""
    <div style='direction: rtl; padding: 20px; font-family: Arial;'>
        <div style='background: #d4edda; color: #155724; padding: 20px; border-radius: 10px;'>
            <h2>✅ تم إصلاح الصلاحيات بنجاح للمستخدم {user.username}</h2>
            <p>جميع الصلاحيات مفعلة الآن.</p>
            <p>المستخدم: {user.username}</p>
            <p>الدور: {user.role}</p>
            <p>معرف الموظف المرتبط: {user.employee_profile.id if user.employee_profile else 'غير مرتبط'}</p>
            <br>
            <a href="/employees" style="background: #4e73df; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-left: 10px;">الذهاب للموظفين</a>
            <a href="/logout" style="background: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">تسجيل خروج وإعادة دخول</a>
        </div>
    </div>
    """


@app.route('/my-permissions')
@login_required
def my_permissions():
    """عرض صلاحيات المستخدم الحالي"""
    permissions = {}
    perm_list = [
        'can_view_employees', 'can_edit_employees', 'can_add_employees', 'can_delete_employees',
        'can_view_attendance', 'can_record_attendance', 'can_view_attendance_reports',
        'can_view_evaluations', 'can_add_evaluations',
        'can_view_salaries', 'can_view_financial'
    ]

    for perm in perm_list:
        permissions[perm] = getattr(current_user, perm, False)

    return jsonify({
        'user': current_user.username,
        'role': current_user.role,
        'permissions': permissions
    })

def register_template_filters(app):
    """تسجيل الفلاتر المخصصة في Jinja2"""


    @app.template_filter('time_ago')
    def time_ago_filter(value):
        """تحويل التاريخ إلى صيغة 'منذ وقت'"""
        if not value:
            return ""

        try:
            now = datetime.now()
            if isinstance(value, date):
                value = datetime.combine(value, datetime.min.time())

            diff = now - value

            # استخدام humanize للترجمة العربية
            try:
                # تثبيت: pip install humanize
                humanize.activate('ar')
                return humanize.naturaltime(diff)
            except:
                # بديل إذا لم يكن humanize متوفراً
                if diff.days > 365:
                    years = diff.days // 365
                    return f"منذ {years} سنة" if years > 1 else "منذ سنة"
                elif diff.days > 30:
                    months = diff.days // 30
                    return f"منذ {months} شهر" if months > 1 else "منذ شهر"
                elif diff.days > 0:
                    return f"منذ {diff.days} يوم" if diff.days > 1 else "منذ يوم"
                elif diff.seconds > 3600:
                    hours = diff.seconds // 3600
                    return f"منذ {hours} ساعة" if hours > 1 else "منذ ساعة"
                elif diff.seconds > 60:
                    minutes = diff.seconds // 60
                    return f"منذ {minutes} دقيقة" if minutes > 1 else "منذ دقيقة"
                else:
                    return "الآن"

        except Exception as e:
            app.logger.error(f"Error in time_ago filter: {str(e)}")
            return str(value)

    @app.template_filter('arabic_date')
    def arabic_date_filter(value, format='%Y-%m-%d'):
        """تنسيق التاريخ مع دعم العربية"""
        if not value:
            return ""
        try:
            if isinstance(value, str):
                value = datetime.strptime(value, '%Y-%m-%d')
            return value.strftime(format)
        except Exception:
            return str(value)

    @app.template_filter('format_time')
    def format_time_filter(value):
        """تنسيق الوقت"""
        if not value:
            return "-"
        try:
            if isinstance(value, str):
                return value
            return value.strftime('%H:%M')
        except Exception:
            return str(value)

    @app.template_filter('status_badge')
    def status_badge_filter(status):
        """عرض حالة الحضور كبادجة"""
        badges = {
            'present': '<span class="badge bg-success">حاضر</span>',
            'absent': '<span class="badge bg-danger">غائب</span>',
            'late': '<span class="badge bg-warning">متأخر</span>',
            'active': '<span class="badge bg-success">نشط</span>',
            'inactive': '<span class="badge bg-secondary">غير نشط</span>'
        }
        return badges.get(status, f'<span class="badge bg-secondary">{status}</span>')

    @app.template_filter('shift_name')
    def shift_name_filter(shift_type):
        """تحويل نوع الوردية إلى اسم عربي"""
        names = {
            'morning': 'صباحية',
            'evening': 'مسائية'
        }
        return names.get(shift_type, shift_type)

    @app.template_filter('date')
    def date_filter(value, format='%Y-%m-%d'):
        """تنسيق التاريخ"""
        if not value:
            return ""
        try:
            if isinstance(value, str):
                from datetime import datetime
                value = datetime.strptime(value, '%Y-%m-%d')
            elif hasattr(value, 'strftime'):
                return value.strftime(format)
            return str(value)
        except Exception as e:
            app.logger.error(f"Error in date filter: {str(e)}")
            return str(value)

    # أضف هذا مع باقي الفلاتر في دالة register_template_filters
    @app.template_filter('time')
    def time_filter(value):
        """تنسيق الوقت"""
        if not value:
            return "-"
        try:
            if isinstance(value, str):
                return value
            return value.strftime('%H:%M')
        except Exception:
            return str(value)


# دالة مساعدة لإنشاء PDF (موحدة لجميع التقارير)
def generate_pdf_from_html(html_content, filename_prefix):
    """
    دالة موحدة لإنشاء PDF من محتوى HTML
    """
    from flask import make_response
    from datetime import datetime

    try:
        # الطريقة الصحيحة لـ WeasyPrint 60.2
        html = HTML(string=html_content)
        pdf = html.write_pdf()

        today = datetime.now()
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers[
            'Content-Disposition'] = f'attachment; filename={filename_prefix}_{today.strftime("%Y%m%d_%H%M%S")}.pdf'
        return response

    except Exception as e:
        app.logger.error(f"PDF Generation Error: {str(e)}")
        return None

@app.route('/create-owner-employee')
@login_required
def create_owner_employee():
    """إنشاء ملف موظف للمالك"""
    if current_user.role != 'owner':
        flash('غير مصرح', 'error')
        return redirect(url_for('dashboard'))

    try:
        # التحقق من وجود ملف موظف للمالك
        employee = Employee.query.filter_by(user_id=current_user.id).first()

        if employee:
            flash('✅ ملف الموظف للمالك موجود بالفعل', 'success')
        else:
            # إنشاء ملف موظف للمالك
            employee = Employee(
                user_id=current_user.id,
                full_name='المالك',
                position='owner',
                hire_date=date.today(),
                is_active=True
            )
            db.session.add(employee)
            db.session.commit()
            flash('✅ تم إنشاء ملف موظف للمالك بنجاح', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'❌ خطأ: {str(e)}', 'error')

    return redirect(url_for('dashboard'))

# ✅ تصحيح: تهيئة الإضافات مرة واحدة
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'يجب تسجيل الدخول للوصول إلى هذه الصفحة'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ✅ بقية الكود يبقى كما هو بدون تغيير...
# [جميع الدوال والروابط الموجودة حالياً تبقى كما هي]


#def initialize_database():
 #   """تهيئة قاعدة البيانات والبيانات الأولية"""
  #  with app.app_context():
        #db.create_all()

        # Create default owner if not exists
       # if not User.query.filter_by(role='owner').first():
        #    owner = User(
         #       username='owner',
          #      email='owner@jewel-land.com',
           #     role='owner',
            #    is_active=True
          #  )
           # owner.set_password('admin123')
            #db.session.add(owner)

            # Create sample supervisor
            #supervisor_user = User(
             #   username='supervisor1',
              #  email='supervisor@jewel-land.com',
               # role='supervisor',
                #is_active=True
           # )
            #supervisor_user.set_password('supervisor123')
            #db.session.add(supervisor_user)
           # db.session.flush()

            #supervisor = Employee(
             #   user_id=supervisor_user.id,
              #  full_name='محمد أحمد',
               # phone='+966500000001',
                #position='supervisor',
                #salary=8000.0,
                #hire_date=date.today(),
                #is_active=True
           # )
            #db.session.add(supervisor)

            # Create sample monitor
            #monitor_user = User(
             #   username='monitor1',
              #  email='monitor@jewel-land.com',
               # role='monitor',
                #is_active=True
            #)
            #monitor_user.set_password('monitor123')
            #db.session.add(monitor_user)
            #db.session.flush()

            #monitor = Employee(
             #   user_id=monitor_user.id,
              #  full_name='خالد سعيد',
               # phone='+966500000002',
                #position='monitor',
                #salary=5000.0,
                #hire_date=date.today(),
                #is_active=True
            #)
            #db.session.add(monitor)

            # Create sample worker
            #worker_user = User(
             #   username='worker1',
              #  email='worker@jewel-land.com',
               # role='worker',
                #is_active=True
            #)
            #worker_user.set_password('worker123')
            #db.session.add(worker_user)
            #db.session.flush()

            #worker = Employee(
             #   user_id=worker_user.id,
              #  full_name='علي حسن',
               # phone='+966500000003',
               # position='worker',
               # salary=3000.0,
                #hire_date=date.today(),
                #is_active=True
            #)
            #db.session.add(worker)

            # Create sample company and areas
            #company = Company(
             #   name='شركة النظافة المثاليه',
             #   address='الرياض - المملكة العربية السعودية',
             #   contact_person='أحمد محمد',
             #   phone='+966500000000',
             #   email='info@example.com',
             #   is_active=True
            #)
            #db.session.add(company)
            #db.session.flush()

            # Create sample area
            #area = Area(
             #   name='المنطقة الرئيسية',
              #  company_id=company.id,
              #  is_active=True
            #)
            #db.session.add(area)
            #db.session.flush()

            # Create sample location
            #location = Location(
             #   name='المبنى الإداري',
              #  area_id=area.id,
              #  is_active=True
            #)
            #db.session.add(location)
            #db.session.flush()

            # Create sample place
            #place = Place(
             #   name='الطابق الأرضي',
              #  location_id=location.id,
               # is_active=True
            #)
            #db.session.add(place)

            #db.session.commit()

            #print("✅ تم تهيئة قاعدة البيانات والبيانات الأولية بنجاح")
            #print("👥 تم إنشاء 3 موظفين تجريبيين:")
            #print("   - مشرف: supervisor1 / supervisor123")
            #print("   - مراقب: monitor1 / monitor123")
            #print("   - عامل: worker1 / worker123")
            #print("   - مالك: owner / admin123")




# سجل الفلاتر بعد إنشاء التطبيق
register_template_filters(app)
@app.context_processor
def inject_stats():
    """حقن الإحصائيات والدوال في جميع القوالب"""
    try:
        # حساب الإحصائيات الفعلية
        total_employees = Employee.query.count()
        active_employees = Employee.query.filter_by(is_active=True).count()
        total_companies = Company.query.filter_by(is_active=True).count()
        total_areas = Area.query.filter_by(is_active=True).count()

        # إحصائيات التقييمات
        total_evaluations_today = CleaningEvaluation.query.filter_by(date=date.today()).count()
        avg_score_today = db.session.query(db.func.avg(CleaningEvaluation.overall_score)) \
                              .filter(CleaningEvaluation.date == date.today()).scalar() or 0

        # إحصائيات الأسبوع
        week_ago = date.today() - timedelta(days=7)
        evaluations_this_week = CleaningEvaluation.query.filter(
            CleaningEvaluation.date >= week_ago
        ).count()

        stats = {
            'total_employees': total_employees,
            'active_employees': active_employees,
            'inactive_employees': total_employees - active_employees,
            'total_companies': total_companies,
            'total_areas': total_areas,
            'total_evaluations_today': total_evaluations_today,
            'evaluations_this_week': evaluations_this_week,
            'avg_score_today': float(avg_score_today)
        }
    except Exception as e:
        print(f"Error calculating stats: {e}")
        # قيم افتراضية في حالة الخطأ
        stats = {
            'total_employees': 0,
            'active_employees': 0,
            'inactive_employees': 0,
            'total_companies': 0,
            'total_areas': 0,
            'total_evaluations_today': 0,
            'evaluations_this_week': 0,
            'avg_score_today': 0.0
        }

    # ✅ إضافة now إلى context processor
    from datetime import datetime
    return dict(stats=stats, now=datetime.now)

# ============================================
# ✅ دالة مركزية لتصدير التقارير إلى Excel و PDF
# ============================================

def export_report(export_type, report_name, headers, rows, filename_prefix=None, orientation='landscape'):
    """
    دالة مركزية لتصدير التقارير إلى Excel أو PDF

    المعاملات:
    - export_type: 'excel' أو 'pdf'
    - report_name: اسم التقرير (للعرض)
    - headers: قائمة بأسماء الأعمدة
    - rows: قائمة من القواميس تحتوي على بيانات التقرير
    - filename_prefix: بادئة اسم الملف (اختياري)
    - orientation: اتجاه الصفحة للـ PDF ('portrait' أو 'landscape')

    تعيد: كائن Response يحتوي على الملف للتحميل
    """
    try:
        from io import BytesIO
        from datetime import datetime
        import pandas as pd
        from flask import send_file, jsonify, request, make_response
        from weasyprint import HTML
        from flask import render_template_string

        # اسم الملف الأساسي
        if not filename_prefix:
            filename_prefix = report_name.replace(' ', '_')

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{filename_prefix}_{timestamp}"

        # تحويل البيانات إلى DataFrame
        df = pd.DataFrame(rows)

        # إعادة تسمية الأعمدة إذا تم تمرير headers
        if headers and len(headers) == len(df.columns):
            df.columns = headers

        # ============================================
        # تصدير Excel
        # ============================================
        if export_type == 'excel':
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=report_name[:30], index=False)

                # تنسيق الخلايا
                worksheet = writer.sheets[report_name[:30]]

                # ضبط عرض الأعمدة تلقائياً
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

            output.seek(0)

            return send_file(
                output,
                as_attachment=True,
                download_name=f"{filename}.xlsx",
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

        # ============================================
        # تصدير PDF
        # ============================================
        elif export_type == 'pdf':
            # إنشاء HTML للتقرير
            html_template = """
            <!DOCTYPE html>
            <html dir="rtl" lang="ar">
            <head>
                <meta charset="UTF-8">
                <style>
                    @page {
                        size: A4 {{ orientation }};
                        margin: 1cm;
                    }
                    body {
                        font-family: 'DejaVu Sans', Arial, sans-serif;
                        font-size: 10px;
                    }
                    .header {
                        text-align: center;
                        margin-bottom: 20px;
                        border-bottom: 2px solid #333;
                        padding-bottom: 10px;
                    }
                    .header h1 {
                        font-size: 18px;
                        margin: 0 0 5px 0;
                        color: #333;
                    }
                    .header p {
                        font-size: 12px;
                        margin: 5px 0;
                        color: #666;
                    }
                    table {
                        width: 100%;
                        border-collapse: collapse;
                        margin: 20px 0;
                    }
                    th {
                        background-color: #2196F3;
                        color: white;
                        font-weight: bold;
                        text-align: center;
                        padding: 8px;
                        font-size: 10px;
                    }
                    td {
                        border: 1px solid #ddd;
                        padding: 6px;
                        text-align: center;
                    }
                    tr:nth-child(even) {
                        background-color: #f9f9f9;
                    }
                    .footer {
                        margin-top: 30px;
                        text-align: center;
                        font-size: 9px;
                        color: #666;
                        border-top: 1px solid #ccc;
                        padding-top: 10px;
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{{ report_name }}</h1>
                    <p>تاريخ التقرير: {{ today.strftime('%Y-%m-%d %H:%M') }}</p>
                </div>

                <table>
                    <thead>
                        <tr>
                            {% for header in headers %}
                            <th>{{ header }}</th>
                            {% endfor %}
                        </tr>
                    </thead>
                    <tbody>
                        {% for row in rows %}
                        <tr>
                            {% for key in row.keys() %}
                            <td>{{ row[key] }}</td>
                            {% endfor %}
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>

                <div class="footer">
                    <p>تم إنشاء هذا التقرير بواسطة نظام إدارة الموارد البشرية - جميع الحقوق محفوظة © {{ today.year }}</p>
                </div>
            </body>
            </html>
            """

            # تجهيز البيانات للقالب
            context = {
                'report_name': report_name,
                'headers': headers,
                'rows': rows,
                'today': datetime.now(),
                'orientation': orientation
            }

            # إنشاء HTML
            html = render_template_string(html_template, **context)

            # إنشاء PDF باستخدام الدالة الذكية
            try:
                # محاولة استخدام الدالة الذكية أولاً
                response = export_pdf(html, filename_prefix)
                if response:
                    return response
                else:
                    # إذا فشلت، استخدم WeasyPrint مباشرة
                    pdf = HTML(string=html, base_url=request.base_url).write_pdf()
                    response = make_response(pdf)
                    response.headers['Content-Type'] = 'application/pdf'
                    response.headers['Content-Disposition'] = f'attachment; filename={filename}.pdf'
                    return response
            except:
                # إذا فشل كل شيء، استخدم WeasyPrint مباشرة
                pdf = HTML(string=html, base_url=request.base_url).write_pdf()
                response = make_response(pdf)
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = f'attachment; filename={filename}.pdf'
                return response

        else:
            return jsonify({
                'success': False,
                'message': 'نوع التصدير غير مدعوم'
            }), 400

    except Exception as e:
        app.logger.error(f"❌ Error in export_report: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'حدث خطأ في التصدير: {str(e)}'
        }), 500


def export_pdf(html_content, filename_prefix):
    """
    دالة ذكية لتصدير PDF:
    - محلياً: تستخدم WeasyPrint
    - على السيرفر: تستخدم wkhtmltopdf عبر PDFKit
    """
    import os
    from flask import make_response
    from datetime import datetime

    # التحقق من البيئة
    is_production = os.environ.get('FLASK_ENV') == 'production'

    try:
        if is_production:
            # على السيرفر: استخدام PDFKit مع wkhtmltopdf
            import pdfkit
            import tempfile
            import subprocess

            # طريقة بديلة باستخدام الأمر المباشر
            with tempfile.NamedTemporaryFile(suffix='.html', mode='w', encoding='utf-8', delete=False) as f:
                f.write(html_content)
                temp_html = f.name

            temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_pdf.close()

            # استخدام wkhtmltopdf مباشرة
            cmd = [
                'wkhtmltopdf',
                '--page-size', 'A4',
                '--orientation', 'Landscape',
                '--encoding', 'UTF-8',
                '--margin-top', '20',
                '--margin-right', '15',
                '--margin-bottom', '20',
                '--margin-left', '15',
                '--enable-local-file-access',
                temp_html,
                temp_pdf.name
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                app.logger.error(f"wkhtmltopdf error: {result.stderr}")
                return None

            with open(temp_pdf.name, 'rb') as f:
                pdf = f.read()

            # تنظيف الملفات المؤقتة
            os.unlink(temp_html)
            os.unlink(temp_pdf.name)

        else:
            # محلياً: استخدام WeasyPrint
            from weasyprint import HTML
            html = HTML(string=html_content)
            pdf = html.write_pdf()

        # تجهيز الاستجابة
        today = datetime.now()
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers[
            'Content-Disposition'] = f'attachment; filename={filename_prefix}_{today.strftime("%Y%m%d_%H%M%S")}.pdf'
        return response

    except Exception as e:
        app.logger.error(f"PDF Generation Error: {str(e)}")
        return None

def export_pdf_with_pdfkit(html_content, filename_prefix):
    """
    دالة لإنشاء PDF باستخدام PDFKit مع تحديد المسار الكامل
    """
    import pdfkit
    from flask import make_response
    from datetime import datetime
    import os

    try:
        # المسار الكامل لـ wkhtmltopdf (تأكد من وجوده)
        path_to_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'

        # التحقق من وجود الملف
        if not os.path.exists(path_to_wkhtmltopdf):
            app.logger.error(f"الملف غير موجود: {path_to_wkhtmltopdf}")
            # جرب مساراً آخر
            path_to_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'

        # تكوين PDFKit مع المسار
        config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)

        # خيارات PDF
        options = {
            'page-size': 'A4',
            'orientation': 'Landscape',
            'encoding': 'UTF-8',
            'no-outline': None,
            'margin-top': '20mm',
            'margin-right': '15mm',
            'margin-bottom': '20mm',
            'margin-left': '15mm',
            'enable-local-file-access': None
        }

        # إنشاء PDF مع تحديد المسار
        pdf = pdfkit.from_string(html_content, False, options=options, configuration=config)

        # تجهيز الاستجابة
        today = datetime.now()
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers[
            'Content-Disposition'] = f'attachment; filename={filename_prefix}_{today.strftime("%Y%m%d_%H%M%S")}.pdf'
        return response

    except Exception as e:
        app.logger.error(f"PDFKit Error: {str(e)}")
        # طباعة تفاصيل أكثر للخطأ
        import traceback
        traceback.print_exc()
        return None
# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password) and user.is_active:
            login_user(user)
            flash('تم تسجيل الدخول بنجاح', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')

    return render_template('auth/login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('login'))


# User Management (Owner only)
@app.route('/users')
@login_required
def users_list():
    if current_user.role != 'owner':
        flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))

    users_list = User.query.all()
    return render_template('users/list.html', users=users_list)


@app.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    if current_user.role != 'owner':
        flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            # التحقق من عدم وجود مستخدم بنفس اسم المستخدم
            existing_user = User.query.filter_by(username=request.form['username']).first()
            if existing_user:
                flash('اسم المستخدم موجود مسبقاً', 'error')
                return render_template('users/add.html')

            # إنشاء مستخدم جديد
            user = User(
                username=request.form['username'],
                email=request.form['email'],
                role=request.form['role'],
                is_active=request.form.get('is_active') == 'on'
            )
            user.set_password(request.form['password'])
            db.session.add(user)
            db.session.commit()

            flash('تم إضافة المستخدم بنجاح', 'success')
            return redirect(url_for('users_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة المستخدم: {str(e)}', 'error')

    return render_template('users/add.html')


@app.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'owner':
        flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        try:
            user.username = request.form['username']
            user.email = request.form['email']
            user.role = request.form['role']
            user.is_active = request.form.get('is_active') == 'on'

            # تحديث كلمة المرور إذا تم تقديمها
            if request.form.get('password'):
                user.set_password(request.form['password'])

            db.session.commit()
            flash('تم تحديث المستخدم بنجاح', 'success')
            return redirect(url_for('users_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تحديث المستخدم: {str(e)}', 'error')

    return render_template('users/edit.html', user=user)


@app.route('/users/delete/<int:user_id>')
@login_required
def delete_user(user_id):
    if current_user.role != 'owner':
        flash('غير مصرح بهذا الإجراء', 'error')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)

    # منع حذف المستخدم الحالي
    if user.id == current_user.id:
        flash('لا يمكن حذف حسابك الشخصي', 'error')
        return redirect(url_for('users_list'))

    try:
        db.session.delete(user)
        db.session.commit()
        flash('تم حذف المستخدم بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف المستخدم: {str(e)}', 'error')

    return redirect(url_for('users_list'))


@app.route('/debug-routes')
def debug_routes():
    """عرض جميع المسارات المتاحة"""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append(f"{rule.endpoint} -> {rule.rule}")

    return "<br>".join(sorted(routes))


@app.route('/add-permissions-columns')
@login_required
def add_permissions_columns():
    """إضافة أعمدة الصلاحيات إلى جدول المستخدمين"""
    if current_user.role != 'owner':
        return "غير مصرح", 403

    try:
        from sqlalchemy import inspect, text

        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('clean_users')]

        added_columns = []
        messages = []

        # قائمة بجميع أعمدة الصلاحيات المراد إضافتها مع القيم الافتراضية
        permission_columns = [
            # تقارير الموظفين
            ('can_view_employees', 'BOOLEAN DEFAULT 1'),
            ('can_edit_employees', 'BOOLEAN DEFAULT 0'),
            ('can_add_employees', 'BOOLEAN DEFAULT 0'),
            ('can_delete_employees', 'BOOLEAN DEFAULT 0'),

            # تقارير الحضور
            ('can_view_attendance', 'BOOLEAN DEFAULT 1'),
            ('can_record_attendance', 'BOOLEAN DEFAULT 1'),
            ('can_view_attendance_reports', 'BOOLEAN DEFAULT 1'),
            ('can_view_overtime', 'BOOLEAN DEFAULT 0'),
            ('can_view_absence_rates', 'BOOLEAN DEFAULT 0'),

            # تقارير التقييمات
            ('can_view_evaluations', 'BOOLEAN DEFAULT 1'),
            ('can_add_evaluations', 'BOOLEAN DEFAULT 1'),
            ('can_view_evaluation_reports', 'BOOLEAN DEFAULT 0'),
            ('can_view_detailed_evaluations', 'BOOLEAN DEFAULT 0'),

            # تقارير الأداء
            ('can_view_performance', 'BOOLEAN DEFAULT 0'),
            ('can_view_top_employees', 'BOOLEAN DEFAULT 0'),
            ('can_view_employee_efficiency', 'BOOLEAN DEFAULT 0'),

            # تقارير الشركات والمناطق
            ('can_view_companies', 'BOOLEAN DEFAULT 1'),
            ('can_view_company_stats', 'BOOLEAN DEFAULT 0'),
            ('can_view_zones', 'BOOLEAN DEFAULT 0'),

            # تقارير مالية
            ('can_view_salaries', 'BOOLEAN DEFAULT 0'),
            ('can_view_salary_reports', 'BOOLEAN DEFAULT 0'),
            ('can_view_financial', 'BOOLEAN DEFAULT 0'),
            ('can_view_invoices', 'BOOLEAN DEFAULT 0'),
            ('can_view_penalties', 'BOOLEAN DEFAULT 0'),

            # لوحة التحكم
            ('can_view_dashboard', 'BOOLEAN DEFAULT 1'),
            ('can_view_kpis', 'BOOLEAN DEFAULT 0'),
            ('can_view_heatmap', 'BOOLEAN DEFAULT 0'),

            # إعدادات النظام
            ('can_manage_users', 'BOOLEAN DEFAULT 0'),
            ('can_manage_roles', 'BOOLEAN DEFAULT 0')
        ]

        with db.engine.connect() as conn:
            for col_name, col_type in permission_columns:
                if col_name not in columns:
                    try:
                        conn.execute(text(f"ALTER TABLE clean_users ADD COLUMN {col_name} {col_type}"))
                        added_columns.append(col_name)
                        messages.append(f"✅ تم إضافة عمود {col_name}")
                    except Exception as e:
                        messages.append(f"⚠️ خطأ في إضافة {col_name}: {str(e)}")

            conn.commit()

        # تحديث المستخدمين الحاليين حسب دورهم
        users = User.query.all()
        updated_users = 0

        for user in users:
            updated = False

            if user.role == 'owner':
                # المالك له كل الصلاحيات
                for col_name, _ in permission_columns:
                    if hasattr(user, col_name) and not getattr(user, col_name):
                        setattr(user, col_name, True)
                        updated = True
                messages.append(f"👑 تم تحديث صلاحيات المالك {user.username}")

            elif user.role == 'supervisor':
                # المشرف له صلاحيات محددة
                supervisor_permissions = {
                    'can_view_employees': True,
                    'can_edit_employees': False,
                    'can_add_employees': False,
                    'can_delete_employees': False,
                    'can_view_attendance': True,
                    'can_record_attendance': True,
                    'can_view_attendance_reports': True,
                    'can_view_overtime': False,
                    'can_view_absence_rates': True,
                    'can_view_evaluations': True,
                    'can_add_evaluations': True,
                    'can_view_evaluation_reports': True,
                    'can_view_detailed_evaluations': False,
                    'can_view_performance': True,
                    'can_view_top_employees': True,
                    'can_view_employee_efficiency': False,
                    'can_view_companies': True,
                    'can_view_company_stats': True,
                    'can_view_zones': True,
                    'can_view_salaries': False,
                    'can_view_salary_reports': False,
                    'can_view_financial': False,
                    'can_view_invoices': False,
                    'can_view_penalties': True,
                    'can_view_dashboard': True,
                    'can_view_kpis': True,
                    'can_view_heatmap': False,
                    'can_manage_users': False,
                    'can_manage_roles': False
                }

                for col_name, value in supervisor_permissions.items():
                    if hasattr(user, col_name):
                        setattr(user, col_name, value)
                        updated = True
                messages.append(f"👤 تم تحديث صلاحيات المشرف {user.username}")

            elif user.role == 'admin':
                # الإداري له صلاحيات إدارية
                admin_permissions = {
                    'can_view_employees': True,
                    'can_edit_employees': True,
                    'can_add_employees': True,
                    'can_delete_employees': False,
                    'can_view_attendance': True,
                    'can_record_attendance': False,
                    'can_view_attendance_reports': True,
                    'can_view_overtime': True,
                    'can_view_absence_rates': True,
                    'can_view_evaluations': True,
                    'can_add_evaluations': False,
                    'can_view_evaluation_reports': True,
                    'can_view_detailed_evaluations': True,
                    'can_view_performance': True,
                    'can_view_top_employees': True,
                    'can_view_employee_efficiency': True,
                    'can_view_companies': True,
                    'can_view_company_stats': True,
                    'can_view_zones': True,
                    'can_view_salaries': True,
                    'can_view_salary_reports': True,
                    'can_view_financial': True,
                    'can_view_invoices': True,
                    'can_view_penalties': True,
                    'can_view_dashboard': True,
                    'can_view_kpis': True,
                    'can_view_heatmap': True,
                    'can_manage_users': False,
                    'can_manage_roles': False
                }

                for col_name, value in admin_permissions.items():
                    if hasattr(user, col_name):
                        setattr(user, col_name, value)
                        updated = True
                messages.append(f"📊 تم تحديث صلاحيات الإداري {user.username}")

            elif user.role == 'monitor':
                # المراقب له صلاحيات محدودة
                monitor_permissions = {
                    'can_view_employees': True,
                    'can_edit_employees': False,
                    'can_add_employees': False,
                    'can_delete_employees': False,
                    'can_view_attendance': True,
                    'can_record_attendance': True,
                    'can_view_attendance_reports': False,
                    'can_view_overtime': False,
                    'can_view_absence_rates': False,
                    'can_view_evaluations': True,
                    'can_add_evaluations': True,
                    'can_view_evaluation_reports': False,
                    'can_view_detailed_evaluations': False,
                    'can_view_performance': False,
                    'can_view_top_employees': False,
                    'can_view_employee_efficiency': False,
                    'can_view_companies': True,
                    'can_view_company_stats': False,
                    'can_view_zones': False,
                    'can_view_salaries': False,
                    'can_view_salary_reports': False,
                    'can_view_financial': False,
                    'can_view_invoices': False,
                    'can_view_penalties': False,
                    'can_view_dashboard': True,
                    'can_view_kpis': False,
                    'can_view_heatmap': False,
                    'can_manage_users': False,
                    'can_manage_roles': False
                }

                for col_name, value in monitor_permissions.items():
                    if hasattr(user, col_name):
                        setattr(user, col_name, value)
                        updated = True
                messages.append(f"👁️ تم تحديث صلاحيات المراقب {user.username}")

            if updated:
                updated_users += 1

        db.session.commit()

        # إنشاء صفحة النتيجة
        result_html = f"""
        <div style='direction: rtl; padding: 20px; font-family: Arial; max-width: 800px; margin: 0 auto;'>
            <div style='background: #f8f9fc; border-radius: 10px; padding: 20px; box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.1);'>
                <h2 style='color: #4e73df; margin-bottom: 20px;'>
                    <i class='fas fa-database' style='margin-left: 10px;'></i>
                    نتيجة تحديث هيكل الصلاحيات
                </h2>

                <div style='background: #d4edda; color: #155724; padding: 15px; border-radius: 5px; margin-bottom: 20px;'>
                    <strong>✅ تمت العملية بنجاح</strong><br>
                    تم إضافة {len(added_columns)} عمود صلاحية جديد
                </div>

                <h4 style='color: #2c3e50; margin-top: 20px;'>الأعمدة المضافة:</h4>
                <ul style='list-style: none; padding: 0; display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;'>
        """

        for col in added_columns:
            result_html += f"<li style='background: #e8f4fd; padding: 8px 12px; border-radius: 5px;'><i class='fas fa-check-circle' style='color: #28a745; margin-left: 8px;'></i>{col}</li>"

        result_html += f"""
                </ul>

                <div style='background: #fff3cd; color: #856404; padding: 15px; border-radius: 5px; margin: 20px 0;'>
                    <strong>ℹ️ معلومات إضافية:</strong><br>
                    - تم تحديث صلاحيات {updated_users} مستخدم بناءً على أدوارهم<br>
                    - يمكنك الآن تعديل الصلاحيات يدوياً من صفحة المستخدمين
                </div>

                <div style='display: flex; gap: 10px; justify-content: center; margin-top: 30px;'>
                    <a href='/users' style='background: #4e73df; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;'>
                        <i class='fas fa-users-cog' style='margin-left: 8px;'></i>
                        الذهاب لإدارة المستخدمين
                    </a>
                    <a href='/dashboard' style='background: #858796; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;'>
                        <i class='fas fa-home' style='margin-left: 8px;'></i>
                        العودة للرئيسية
                    </a>
                </div>
            </div>
        </div>
        """

        return result_html

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return f"""
        <div style='direction: rtl; padding: 20px;'>
            <div style='background: #f8d7da; color: #721c24; padding: 20px; border-radius: 10px;'>
                <h2>❌ خطأ في تحديث قاعدة البيانات</h2>
                <p>{str(e)}</p>
                <pre style='background: #fff; padding: 10px; border-radius: 5px; overflow: auto;'>{error_details}</pre>
                <a href='/dashboard' style='background: #4e73df; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 20px;'>
                    العودة للرئيسية
                </a>
            </div>
        </div>
        """, 500


@app.route('/api/user-permissions/<int:user_id>')
@login_required
def get_user_permissions(user_id):
    """API للحصول على صلاحيات مستخدم معين"""
    if current_user.role != 'owner':
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403

    user = User.query.get_or_404(user_id)

    # قائمة بجميع الصلاحيات
    permission_columns = [
        'can_view_employees', 'can_edit_employees', 'can_add_employees', 'can_delete_employees',
        'can_view_attendance', 'can_record_attendance', 'can_view_attendance_reports',
        'can_view_overtime', 'can_view_absence_rates',
        'can_view_evaluations', 'can_add_evaluations', 'can_view_evaluation_reports',
        'can_view_detailed_evaluations',
        'can_view_performance', 'can_view_top_employees', 'can_view_employee_efficiency',
        'can_view_companies', 'can_view_company_stats', 'can_view_zones',
        'can_view_salaries', 'can_view_salary_reports', 'can_view_financial',
        'can_view_invoices', 'can_view_penalties',
        'can_view_dashboard', 'can_view_kpis', 'can_view_heatmap',
        'can_manage_users', 'can_manage_roles'
    ]

    permissions = {}
    for col in permission_columns:
        permissions[col] = getattr(user, col, False)

    # ترجمة الدور
    role_ar = {
        'owner': 'مالك',
        'supervisor': 'مشرف',
        'admin': 'إداري',
        'monitor': 'مراقب',
        'worker': 'عامل'
    }.get(user.role, user.role)

    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'role_ar': role_ar
        },
        'permissions': permissions
    })


@app.route('/api/update-user-permissions/<int:user_id>', methods=['POST'])
@login_required
def update_user_permissions(user_id):
    """تحديث صلاحيات مستخدم"""
    if current_user.role != 'owner':
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403

    user = User.query.get_or_404(user_id)

    # منع تعديل صلاحيات المالك
    if user.role == 'owner':
        return jsonify({'success': False, 'message': 'لا يمكن تعديل صلاحيات المالك'}), 403

    try:
        data = request.get_json()

        # قائمة بجميع الصلاحيات الممكنة
        permission_columns = [
            'can_view_employees', 'can_edit_employees', 'can_add_employees', 'can_delete_employees',
            'can_view_attendance', 'can_record_attendance', 'can_view_attendance_reports',
            'can_view_overtime', 'can_view_absence_rates',
            'can_view_evaluations', 'can_add_evaluations', 'can_view_evaluation_reports',
            'can_view_detailed_evaluations',
            'can_view_performance', 'can_view_top_employees', 'can_view_employee_efficiency',
            'can_view_companies', 'can_view_company_stats', 'can_view_zones',
            'can_view_salaries', 'can_view_salary_reports', 'can_view_financial',
            'can_view_invoices', 'can_view_penalties',
            'can_view_dashboard', 'can_view_kpis', 'can_view_heatmap',
            'can_manage_users', 'can_manage_roles'
        ]

        for col in permission_columns:
            if col in data:
                setattr(user, col, data[col])

        user.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'تم تحديث الصلاحيات بنجاح'
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating permissions: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'حدث خطأ: {str(e)}'
        }), 500


@app.route('/debug-user-permissions/<int:user_id>')
@login_required
def debug_user_permissions(user_id):
    """دالة تشخيصية لعرض صلاحيات المستخدم"""
    if current_user.role != 'owner':
        return "غير مصرح", 403

    user = User.query.get_or_404(user_id)

    # قائمة بجميع الصلاحيات
    permission_columns = [
        'can_view_employees', 'can_edit_employees', 'can_add_employees', 'can_delete_employees',
        'can_view_attendance', 'can_record_attendance', 'can_view_attendance_reports',
        'can_view_overtime', 'can_view_absence_rates',
        'can_view_evaluations', 'can_add_evaluations', 'can_view_evaluation_reports',
        'can_view_detailed_evaluations',
        'can_view_performance', 'can_view_top_employees', 'can_view_employee_efficiency',
        'can_view_companies', 'can_view_company_stats', 'can_view_zones',
        'can_view_salaries', 'can_view_salary_reports', 'can_view_financial',
        'can_view_invoices', 'can_view_penalties',
        'can_view_dashboard', 'can_view_kpis', 'can_view_heatmap',
        'can_manage_users', 'can_manage_roles'
    ]

    permissions = {}
    for col in permission_columns:
        permissions[col] = getattr(user, col, False)

    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'role': user.role
        },
        'permissions': permissions
    })


@app.route('/api/test-update-permission/<int:user_id>', methods=['GET'])
@login_required
def test_update_permission_api(user_id):
    """اختبار تحديث صلاحية عبر API"""
    if current_user.role != 'owner':
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403

    try:
        user = User.query.get_or_404(user_id)

        # جلب القيمة الحالية
        current_value = user.can_view_salaries

        # عكس القيمة
        new_value = not current_value
        setattr(user, 'can_view_salaries', new_value)
        user.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'تم تغيير can_view_salaries من {current_value} إلى {new_value}',
            'user': user.username,
            'old_value': current_value,
            'new_value': new_value
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
# دوال التحقق من الصلاحيات
def get_supervised_employees(user):
    """الحصول على الموظفين التابعين للمستخدم الحالي"""
    try:
        if user.role == 'owner':
            # المالك يرى جميع الموظفين
            return Employee.query.filter_by(is_active=True).all()

        elif user.role == 'supervisor':
            # المشرف يرى الموظفين التابعين له فقط
            supervisor_emp = Employee.query.filter_by(user_id=user.id).first()
            if supervisor_emp:
                # جلب الموظفين الذين supervisor_id = supervisor_emp.id
                return Employee.query.filter_by(
                    supervisor_id=supervisor_emp.id,
                    is_active=True
                ).all()
            return []

        elif user.role == 'monitor':
            # المراقب يرى العمال في موقعه فقط
            monitor_emp = Employee.query.filter_by(user_id=user.id).first()
            if monitor_emp:
                # جلب العمال المرتبطين بنفس الموقع عبر الأماكن
                from models import Place, Location
                places = Place.query.join(Location).filter(
                    Location.monitor_id == monitor_emp.id
                ).all()
                worker_ids = [p.worker_id for p in places if p.worker_id]
                return Employee.query.filter(Employee.id.in_(worker_ids)).all()
            return []

        else:
            # العامل يرى نفسه فقط
            emp = Employee.query.filter_by(user_id=user.id).first()
            return [emp] if emp else []

    except Exception as e:
        app.logger.error(f"Error in get_supervised_employees: {str(e)}")
        return []


def can_manage_attendance(user, employee_id):
    """التحقق من صلاحية المستخدم لإدارة حضور موظف معين"""
    try:
        if user.role == 'owner':
            return True

        if user.role == 'supervisor':
            supervisor_emp = Employee.query.filter_by(user_id=user.id).first()
            if not supervisor_emp:
                return False

            # التحقق أن الموظف تابع لهذا المشرف
            employee = Employee.query.get(employee_id)
            return employee and employee.supervisor_id == supervisor_emp.id

        if user.role == 'monitor':
            monitor_emp = Employee.query.filter_by(user_id=user.id).first()
            if not monitor_emp:
                return False

            # التحقق أن الموظف عامل في موقع يراقبه
            from models import Place, Location
            place = Place.query.join(Location).filter(
                Place.worker_id == employee_id,
                Location.monitor_id == monitor_emp.id
            ).first()
            return place is not None

        return False

    except Exception as e:
        app.logger.error(f"Error in can_manage_attendance: {str(e)}")
        return False


# API Routes for AJAX
@app.route('/api/companies')
@login_required
def api_companies():
    """API للحصول على قائمة الشركات النشطة"""
    try:
        companies = Company.query.filter_by(is_active=True).order_by(Company.name).all()
        companies_data = [{
            'id': company.id,
            'name': company.name,
            'contact_person': company.contact_person or '',
            'phone': company.phone or ''
        } for company in companies]

        return jsonify({
            'success': True,
            'data': companies_data,
            'count': len(companies_data)
        })

    except SQLAlchemyError as e:
        app.logger.error(f"Database error in api_companies: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ في تحميل بيانات الشركات',
            'data': [],
            'count': 0
        }), 500


@app.route('/api/areas/<int:company_id>')
@login_required
def get_areas(company_id):
    """API للحصول على مناطق شركة محددة"""
    try:
        # التحقق من وجود الشركة
        company = Company.query.filter_by(id=company_id, is_active=True).first()
        if not company:
            return jsonify({
                'success': False,
                'message': 'الشركة غير موجودة أو غير نشطة',
                'data': [],
                'count': 0
            }), 404

        areas = Area.query.filter_by(company_id=company_id, is_active=True).order_by(Area.name).all()
        areas_data = [{
            'id': area.id,
            'name': area.name,
            'company_id': area.company_id,
            'supervisor_name': area.supervisor.full_name if area.supervisor else 'غير محدد'
        } for area in areas]

        return jsonify({
            'success': True,
            'data': areas_data,
            'count': len(areas_data),
            'company_name': company.name
        })

    except SQLAlchemyError as e:
        app.logger.error(f"Database error in get_areas: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ في تحميل بيانات المناطق',
            'data': [],
            'count': 0
        }), 500


@app.route('/api/locations/<int:area_id>')
@login_required
def get_locations(area_id):
    """API للحصول على مواقع منطقة محددة"""
    try:
        # التحقق من وجود المنطقة
        area = Area.query.filter_by(id=area_id, is_active=True).first()
        if not area:
            return jsonify({
                'success': False,
                'message': 'المنطقة غير موجودة أو غير نشطة',
                'data': [],
                'count': 0
            }), 404

        locations = Location.query.filter_by(area_id=area_id, is_active=True).order_by(Location.name).all()
        locations_data = [{
            'id': loc.id,
            'name': loc.name,
            'area_id': loc.area_id,
            'monitor_name': loc.monitor.full_name if loc.monitor else 'غير محدد'
        } for loc in locations]

        return jsonify({
            'success': True,
            'data': locations_data,
            'count': len(locations_data),
            'area_name': area.name
        })

    except SQLAlchemyError as e:
        app.logger.error(f"Database error in get_locations: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ في تحميل بيانات المواقع',
            'data': [],
            'count': 0
        }), 500


@app.route('/api/places/<int:location_id>')
@login_required
def get_places(location_id):
    """API للحصول على أماكن موقع محدد"""
    try:
        # التحقق من وجود الموقع
        location = Location.query.filter_by(id=location_id, is_active=True).first()
        if not location:
            return jsonify({
                'success': False,
                'message': 'الموقع غير موجود أو غير نشط',
                'data': [],
                'count': 0
            }), 404

        places = Place.query.filter_by(location_id=location_id, is_active=True).order_by(Place.name).all()
        places_data = [{
            'id': place.id,
            'name': place.name,
            'location_id': place.location_id,
            # إزالة reference إلى description
            'worker_info': place.worker.full_name if place.worker else 'غير محدد'
        } for place in places]

        return jsonify({
            'success': True,
            'data': places_data,
            'count': len(places_data),
            'location_name': location.name
        })

    except SQLAlchemyError as e:
        app.logger.error(f"Database error in get_places: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ في تحميل بيانات الأماكن',
            'data': [],
            'count': 0
        }), 500

@app.route('/api/evaluation/<int:evaluation_id>')
@login_required
def get_evaluation(evaluation_id):
    """API للحصول على بيانات تقييم محدد"""
    try:
        from sqlalchemy.orm import joinedload

        evaluation = CleaningEvaluation.query \
            .options(
            joinedload(CleaningEvaluation.place)
            .joinedload(Place.location)
            .joinedload(Location.area)
            .joinedload(Area.company),
            joinedload(CleaningEvaluation.evaluator),
            joinedload(CleaningEvaluation.evaluated_employee)
        ) \
            .filter(CleaningEvaluation.id == evaluation_id) \
            .first()

        if not evaluation:
            return jsonify({
                'success': False,
                'message': 'التقييم غير موجود'
            }), 404

        evaluation_data = {
            'id': evaluation.id,
            'date': evaluation.date.strftime('%Y-%m-%d'),
            'place': evaluation.place.name if evaluation.place else 'غير محدد',
            'evaluated_employee': evaluation.evaluated_employee.full_name if evaluation.evaluated_employee else 'غير محدد',
            'evaluator': evaluation.evaluator.full_name if evaluation.evaluator else 'غير محدد',
            'cleanliness': evaluation.cleanliness,
            'organization': evaluation.organization,
            'equipment_condition': evaluation.equipment_condition,
            'time': getattr(evaluation, 'time', 0),  # إضافة حقل الوقت إذا كان موجوداً
            'safety_measures': evaluation.safety_measures,
            'overall_score': float(evaluation.overall_score),
            'comments': evaluation.comments or 'لا توجد ملاحظات',
            'created_at': evaluation.created_at.strftime('%Y-%m-%d %H:%M') if evaluation.created_at else 'غير محدد'
        }

        # إضافة معلومات إضافية عن المكان إذا كانت متاحة
        if evaluation.place and evaluation.place.location:
            evaluation_data['location'] = evaluation.place.location.name
            if evaluation.place.location.area:
                evaluation_data['area'] = evaluation.place.location.area.name
                if evaluation.place.location.area.company:
                    evaluation_data['company'] = evaluation.place.location.area.company.name

        return jsonify({
            'success': True,
            'data': evaluation_data
        })

    except Exception as e:
        app.logger.error(f"Error in get_evaluation: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ في تحميل بيانات التقييم'
        }), 500

@app.route('/api/employees/<int:employee_id>')
@login_required
def get_employee(employee_id):
    """API للحصول على بيانات موظف محدد"""
    try:
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({
                'success': False,
                'message': 'الموظف غير موجود'
            }), 404

        # استخدام joinedload لتحميل العلاقات
        from sqlalchemy.orm import joinedload

        employee = Employee.query \
            .options(joinedload(Employee.user)) \
            .filter(Employee.id == employee_id) \
            .first()

        # حساب الإحصائيات - استخدام العلاقات الجديدة
        total_evaluations = len(employee.conducted_evaluations)  # تغيير من evaluations_given إلى conducted_evaluations
        avg_score = db.session.query(db.func.avg(CleaningEvaluation.overall_score)) \
                        .filter(CleaningEvaluation.evaluator_id == employee_id) \
                        .scalar() or 0
        attendance_days = Attendance.query.filter_by(employee_id=employee_id, status='present').count()

        employee_data = {
            'id': employee.id,
            'full_name': employee.full_name,
            'phone': employee.phone or 'غير محدد',
            'address': employee.address or 'غير محدد',
            'position': employee.position,
            'position_ar': 'مشرف' if employee.position == 'supervisor' else 'مراقب' if employee.position == 'monitor' else 'عامل',
            'salary': float(employee.salary) if employee.salary else 0,
            'hire_date': employee.hire_date.strftime('%Y-%m-%d'),
            'is_active': employee.is_active,
            'status_ar': 'نشط' if employee.is_active else 'غير نشط',
            'username': employee.user.username if employee.user else 'غير محدد',
            'email': employee.user.email if employee.user else 'غير محدد',
            'total_evaluations': total_evaluations,
            'avg_score': float(avg_score),
            'attendance_days': attendance_days,
            'performance_level': 'ممتاز' if avg_score >= 4.5 else 'جيد جداً' if avg_score >= 4.0 else 'جيد' if avg_score >= 3.0 else 'يحتاج تحسين'
        }

        return jsonify({
            'success': True,
            'data': employee_data
        })

    except Exception as e:
        app.logger.error(f"Error in get_employee: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ في تحميل بيانات الموظف'
        }), 500

@app.route('/api/employees/active')
@login_required
def get_active_employees():
    """API للحصول على الموظفين النشطين فقط"""
    try:
        employees = Employee.query \
            .filter_by(is_active=True) \
            .order_by(Employee.full_name) \
            .all()

        employees_data = [{
            'id': emp.id,
            'full_name': emp.full_name,
            'position': emp.position,
            'position_ar': 'مشرف' if emp.position == 'supervisor' else 'مراقب' if emp.position == 'monitor' else 'عامل',
            'phone': emp.phone or '',
            'hire_date': emp.hire_date.strftime('%Y-%m-%d')
        } for emp in employees]

        return jsonify({
            'success': True,
            'data': employees_data,
            'count': len(employees_data)
        })

    except SQLAlchemyError as e:
        app.logger.error(f"Database error in get_active_employees: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ في تحميل بيانات الموظفين',
            'data': [],
            'count': 0
        }), 500


@app.route('/api/attendance/employee/<int:employee_id>')
@login_required
def get_employee_attendance(employee_id):
    """API للحصول على سجل حضور موظف محدد"""
    try:
        # التحقق من وجود الموظف
        employee = Employee.query.filter_by(id=employee_id, is_active=True).first()
        if not employee:
            return jsonify({
                'success': False,
                'message': 'الموظف غير موجود أو غير نشط'
            }), 404

        # الحصول على سجلات الحضور للشهر الحالي
        today = date.today()
        start_date = date(today.year, today.month, 1)
        if today.month == 12:
            end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)

        attendance_records = Attendance.query \
            .filter(
            Attendance.employee_id == employee_id,
            Attendance.date >= start_date,
            Attendance.date <= end_date
        ) \
            .order_by(Attendance.date.desc()) \
            .all()

        attendance_data = [{
            'date': record.date.strftime('%Y-%m-%d'),
            'status': record.status,
            'status_ar': 'حاضر' if record.status == 'present' else 'غائب' if record.status == 'absent' else 'متأخر',
            'check_in': record.check_in.strftime('%H:%M') if record.check_in else '-',
            'check_out': record.check_out.strftime('%H:%M') if record.check_out else '-',
            'notes': record.notes or 'لا توجد ملاحظات'
        } for record in attendance_records]

        # إحصائيات الحضور
        present_days = sum(1 for record in attendance_records if record.status == 'present')
        total_days = (end_date - start_date).days + 1
        attendance_rate = (present_days / total_days) * 100 if total_days > 0 else 0

        return jsonify({
            'success': True,
            'data': {
                'employee': {
                    'id': employee.id,
                    'full_name': employee.full_name,
                    'position': employee.position
                },
                'attendance_records': attendance_data,
                'stats': {
                    'total_days': total_days,
                    'present_days': present_days,
                    'absent_days': total_days - present_days,
                    'attendance_rate': round(attendance_rate, 1)
                }
            }
        })

    except SQLAlchemyError as e:
        app.logger.error(f"Database error in get_employee_attendance: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ في تحميل سجل الحضور'
        }), 500

@app.route('/users/toggle-status/<int:user_id>')
@login_required
def toggle_user_status(user_id):
    if current_user.role != 'owner':
        return jsonify({'success': False, 'message': 'غير مصرح بهذا الإجراء'})

    user = User.query.get_or_404(user_id)

    # منع تعطيل المستخدم الحالي
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'لا يمكن تعطيل حسابك الشخصي'})

    try:
        user.is_active = not user.is_active
        db.session.commit()

        status = "مفعل" if user.is_active else "معطل"
        return jsonify({
            'success': True,
            'message': f'تم {status} المستخدم بنجاح',
            'is_active': user.is_active
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})


from flask import render_template, jsonify
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, or_
from models import db, Employee, CleaningEvaluation, Attendance, Company, Area


def get_dashboard_data():
    """جلب بيانات لوحة التحكم"""

    # إحصائيات أساسية
    total_employees = Employee.query.filter_by(is_active=True).count()

    # الحضور اليومي
    today = date.today()
    today_attendance = Attendance.query.filter_by(date=today).all()
    present_today = len([a for a in today_attendance if a.status == 'present'])
    absent_today = len([a for a in today_attendance if a.status == 'absent'])
    attendance_rate = (present_today / total_employees * 100) if total_employees > 0 else 0

    # التقييمات
    today_evaluations = CleaningEvaluation.query.filter_by(date=today).all()
    avg_evaluation = sum(e.overall_score for e in today_evaluations) / len(
        today_evaluations) * 20 if today_evaluations else 0
    max_evaluation = max(e.overall_score for e in today_evaluations) * 20 if today_evaluations else 0
    min_evaluation = min(e.overall_score for e in today_evaluations) * 20 if today_evaluations else 0

    # الموظفين الجدد (في آخر 30 يوم)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    new_employees = Employee.query.filter(
        Employee.created_at >= thirty_days_ago,
        Employee.is_active == True
    ).count()

    # التقييمات التي تحتاج مراجعة (تقييمات أقل من 60%)
    pending_reviews = CleaningEvaluation.query.filter(
        CleaningEvaluation.overall_score < 3.0,  # أقل من 60%
        CleaningEvaluation.date == today
    ).count()

    # بيانات التغيير (محاكاة - في التطبيق الحقيقي يجب حسابها من البيانات السابقة)
    evaluation_change = 2.5  # محاكاة
    attendance_change = 1.2  # محاكاة
    reviews_change = -3  # محاكاة

    # مؤشرات الأداء (محاكاة - يمكن حسابها من التقييمات والتعليقات)
    customer_satisfaction = 92.0
    task_completion = 88.0
    quality_score = 95.0
    time_utilization = 78.0

    customer_satisfaction_change = 3.0
    task_completion_change = 5.0
    quality_change = 2.0
    time_utilization_change = -2.0

    stats = {
        'total_employees': total_employees,
        'present_today': present_today,
        'absent_today': absent_today,
        'attendance_rate': attendance_rate,
        'avg_evaluation': avg_evaluation,
        'max_evaluation': max_evaluation,
        'min_evaluation': min_evaluation,
        'active_employees': total_employees,
        'new_employees': new_employees,
        'pending_reviews': pending_reviews,
        'evaluation_change': evaluation_change,
        'attendance_change': attendance_change,
        'reviews_change': reviews_change,
        'customer_satisfaction': customer_satisfaction,
        'task_completion': task_completion,
        'quality_score': quality_score,
        'time_utilization': time_utilization,
        'customer_satisfaction_change': customer_satisfaction_change,
        'task_completion_change': task_completion_change,
        'quality_change': quality_change,
        'time_utilization_change': time_utilization_change
    }

    return stats


def get_evaluation_chart_data():
    """جلب بيانات الرسم البياني للتقييمات"""

    # محاكاة بيانات التقييم خلال اليوم
    times = ['8:00', '10:00', '12:00', '14:00', '16:00', '18:00']
    avg_scores = [88, 90, 92, 94, 95, 94]
    max_scores = [92, 94, 96, 97, 98, 97]
    min_scores = [82, 84, 85, 86, 85, 85]

    evaluation_data = {
        'labels': times,
        'datasets': [
            {
                'label': 'متوسط التقييم',
                'data': avg_scores,
                'borderColor': '#4e73df',
                'backgroundColor': 'rgba(78, 115, 223, 0.1)',
                'tension': 0.3,
                'fill': True
            },
            {
                'label': 'الأعلى أداءً',
                'data': max_scores,
                'borderColor': '#1cc88a',
                'backgroundColor': 'rgba(28, 200, 138, 0.1)',
                'tension': 0.3,
                'fill': True
            },
            {
                'label': 'الأقل أداءً',
                'data': min_scores,
                'borderColor': '#f6c23e',
                'backgroundColor': 'rgba(246, 194, 62, 0.1)',
                'tension': 0.3,
                'fill': True
            }
        ]
    }

    return evaluation_data


def get_attendance_chart_data():
    """جلب بيانات الرسم البياني للحضور"""

    today = date.today()
    attendance_records = Attendance.query.filter_by(date=today).all()

    present = len([a for a in attendance_records if a.status == 'present'])
    absent = len([a for a in attendance_records if a.status == 'absent'])
    vacation = len([a for a in attendance_records if a.status == 'vacation'])

    attendance_data = {
        'labels': ['حاضرون', 'غائبون', 'إجازة'],
        'datasets': [{
            'data': [present, absent, vacation],
            'backgroundColor': [
                '#1cc88a',
                '#e74a3b',
                '#f6c23e'
            ],
            'borderWidth': 2,
            'borderColor': '#fff'
        }]
    }

    return attendance_data


def get_companies_chart_data():
    """جلب بيانات الرسم البياني للشركات"""

    companies = Company.query.filter_by(is_active=True).all()
    company_names = []
    company_scores = []

    for company in companies:
        # حساب متوسط التقييم لكل شركة
        avg_score = db.session.query(
            func.avg(CleaningEvaluation.overall_score * 20)
        ).join(Place).join(Location).join(Area).filter(
            Area.company_id == company.id,
            CleaningEvaluation.date == date.today()
        ).scalar() or 0

        company_names.append(company.name)
        company_scores.append(round(avg_score, 1))

    companies_data = {
        'labels': company_names,
        'datasets': [{
            'label': 'متوسط التقييم',
            'data': company_scores,
            'backgroundColor': [
                'rgba(78, 115, 223, 0.7)',
                'rgba(28, 200, 138, 0.7)',
                'rgba(54, 185, 204, 0.7)',
                'rgba(246, 194, 62, 0.7)'
            ],
            'borderColor': [
                '#4e73df',
                '#1cc88a',
                '#36b9cc',
                '#f6c23e'
            ],
            'borderWidth': 1
        }]
    }

    return companies_data


def get_areas_chart_data():
    """جلب بيانات الرسم البياني للمناطق"""

    areas = Area.query.filter_by(is_active=True).all()
    area_names = []
    area_scores = []

    for area in areas:
        # حساب متوسط التقييم لكل منطقة
        avg_score = db.session.query(
            func.avg(CleaningEvaluation.overall_score * 20)
        ).join(Place).join(Location).filter(
            Location.area_id == area.id,
            CleaningEvaluation.date == date.today()
        ).scalar() or 0

        area_names.append(area.name)
        area_scores.append(round(avg_score, 1))

    areas_data = {
        'labels': area_names,
        'datasets': [{
            'data': area_scores,
            'backgroundColor': [
                'rgba(78, 115, 223, 0.7)',
                'rgba(28, 200, 138, 0.7)',
                'rgba(54, 185, 204, 0.7)',
                'rgba(246, 194, 62, 0.7)',
                'rgba(231, 74, 59, 0.7)'
            ],
            'borderWidth': 2,
            'borderColor': '#fff'
        }]
    }

    return areas_data


def get_performance_data():
    """جلب بيانات مؤشرات الأداء"""

    # في التطبيق الحقيقي، يمكن حساب هذه المؤشرات من البيانات الفعلية
    performance_data = {
        'customer_satisfaction': 92,
        'task_completion': 88,
        'quality_score': 95,
        'time_utilization': 78
    }

    return performance_data


@app.route('/api/check-username/<username>')
@login_required
def check_username(username):
    """التحقق من توفر اسم المستخدم"""
    try:
        # البحث عن المستخدم في قاعدة البيانات
        user = User.query.filter_by(username=username).first()

        return jsonify({
            'available': user is None,
            'username': username
        })
    except Exception as e:
        return jsonify({
            'available': False,
            'error': str(e)
        }), 500


@app.route('/api/generate-password')
@login_required
def generate_password():
    """توليد كلمة مرور عشوائية"""
    import random
    import string

    # كلمة مرور عشوائية من 8 أحرف
    chars = string.ascii_letters + string.digits
    password = ''.join(random.choice(chars) for _ in range(8))

    return jsonify({
        'password': password
    })

@app.route('/api/dashboard/data')
def api_dashboard_data():
    """API لجلب بيانات لوحة التحكم"""

    view = request.args.get('view', 'day')
    department = request.args.get('department', 'all')

    # يمكنك هنا جلب البيانات حسب view و department
    stats = get_dashboard_data()
    evaluation_data = get_evaluation_chart_data()
    attendance_data = get_attendance_chart_data()

    return jsonify({
        'stats': stats,
        'evaluationData': evaluation_data,
        'attendanceData': attendance_data
    })


# Dashboard - النسخة المحسنة
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    # Basic stats - الإحصائيات الأساسية
    total_employees = Employee.query.count()
    active_employees = Employee.query.filter_by(is_active=True).count()
    inactive_employees = total_employees - active_employees

    # Employee position stats - إحصائيات المناصب
    supervisors_count = Employee.query.filter_by(position='supervisor', is_active=True).count()
    monitors_count = Employee.query.filter_by(position='monitor', is_active=True).count()
    workers_count = Employee.query.filter_by(position='worker', is_active=True).count()

    # Company and area stats - إحصائيات الشركات والمناطق
    total_companies = Company.query.filter_by(is_active=True).count()
    total_areas = Area.query.filter_by(is_active=True).count()

    # Evaluation stats - إحصائيات التقييمات
    total_evaluations_today = CleaningEvaluation.query.filter_by(date=date.today()).count()
    avg_score_today = db.session.query(db.func.avg(CleaningEvaluation.overall_score)) \
                          .filter(CleaningEvaluation.date == date.today()).scalar() or 0

    # This week evaluations - التقييمات هذا الأسبوع
    week_ago = date.today() - timedelta(days=7)
    evaluations_this_week = CleaningEvaluation.query.filter(
        CleaningEvaluation.date >= week_ago
    ).count()

    # New employees this month - الموظفين الجدد هذا الشهر
    month_ago = date.today() - timedelta(days=30)
    new_employees_this_month = Employee.query.filter(
        Employee.hire_date >= month_ago
    ).count()

    # الحضور اليومي - بيانات جديدة
    today_attendance = Attendance.query.filter_by(date=date.today()).all()
    present_today = len([a for a in today_attendance if a.status == 'present'])
    absent_today = len([a for a in today_attendance if a.status == 'absent'])
    attendance_rate = (present_today / active_employees * 100) if active_employees > 0 else 0

    # التقييمات التي تحتاج مراجعة
    pending_reviews = CleaningEvaluation.query.filter(
        CleaningEvaluation.overall_score < 3.0,
        CleaningEvaluation.date == date.today()
    ).count()

    # بيانات التقييمات للمخططات
    today_evaluations = CleaningEvaluation.query.filter_by(date=date.today()).all()
    if today_evaluations:
        avg_evaluation = sum(e.overall_score for e in today_evaluations) / len(today_evaluations) * 20
        max_evaluation = max(e.overall_score for e in today_evaluations) * 20
        min_evaluation = min(e.overall_score for e in today_evaluations) * 20
    else:
        avg_evaluation = max_evaluation = min_evaluation = 0

    # إحصائيات محسنة
    stats = {
        # الإحصائيات القديمة
        'total_employees': total_employees,
        'active_employees': active_employees,
        'inactive_employees': inactive_employees,
        'total_companies': total_companies,
        'total_areas': total_areas,
        'total_evaluations_today': total_evaluations_today,
        'avg_score_today': avg_score_today,
        'evaluations_this_week': evaluations_this_week,
        'supervisors_count': supervisors_count,
        'monitors_count': monitors_count,
        'workers_count': workers_count,
        'new_employees_this_month': new_employees_this_month,

        # الإحصائيات الجديدة للوحة المحسنة
        'present_today': present_today,
        'absent_today': absent_today,
        'attendance_rate': round(attendance_rate, 1),
        'avg_evaluation': round(avg_evaluation, 1),
        'max_evaluation': round(max_evaluation, 1),
        'min_evaluation': round(min_evaluation, 1),
        'pending_reviews': pending_reviews,

        # بيانات التغيير (محاكاة - يمكن حسابها من البيانات التاريخية)
        'evaluation_change': 2.5,
        'attendance_change': 1.2,
        'reviews_change': -3,

        # مؤشرات الأداء
        'customer_satisfaction': 92.0,
        'task_completion': 88.0,
        'quality_score': 95.0,
        'time_utilization': 78.0,
        'customer_satisfaction_change': 3.0,
        'task_completion_change': 5.0,
        'quality_change': 2.0,
        'time_utilization_change': -2.0
    }

    # بيانات الرسوم البيانية
    evaluation_data = get_evaluation_chart_data()
    attendance_data = get_attendance_chart_data()
    companies_data = get_companies_chart_data()
    areas_data = get_areas_chart_data()
    performance_data = get_performance_data()

    # البيانات القديمة للتوافق مع القالب القديم
    from sqlalchemy.orm import joinedload
    recent_evaluations = CleaningEvaluation.query \
        .options(
        joinedload(CleaningEvaluation.place),
        joinedload(CleaningEvaluation.evaluator),
        joinedload(CleaningEvaluation.evaluated_employee)
    ) \
        .order_by(CleaningEvaluation.created_at.desc()) \
        .limit(10) \
        .all()

    recent_employees = Employee.query \
        .order_by(Employee.created_at.desc()) \
        .limit(5) \
        .all()

    top_performers = db.session.query(
        Employee,
        db.func.avg(CleaningEvaluation.overall_score).label('avg_score'),
        db.func.count(CleaningEvaluation.id).label('evaluations_count')
    ).join(CleaningEvaluation, CleaningEvaluation.evaluator_id == Employee.id) \
        .group_by(Employee.id) \
        .order_by(db.desc('avg_score')) \
        .limit(5) \
        .all()

    formatted_performers = []
    for employee, avg_score, eval_count in top_performers:
        formatted_performers.append({
            'id': employee.id,
            'full_name': employee.full_name,
            'position': employee.position,
            'position_ar': 'مشرف' if employee.position == 'supervisor' else 'مراقب' if employee.position == 'monitor' else 'عامل',
            'avg_score': float(avg_score) if avg_score else 0,
            'evaluations_count': eval_count
        })
    defaultData = {
        "evaluationData": [],
    }

    # استخدام القالب الجديد مع تمرير جميع البيانات
    return render_template('dashboard.html',  # تغيير إلى القالب الجديد
                           stats=stats,
                           evaluation_data=evaluation_data,
                           attendance_data=attendance_data,
                           companies_data=companies_data,
                           areas_data=areas_data,
                           performance_data=performance_data,
                           # البيانات القديمة للتوافق
                           recent_evaluations=recent_evaluations,
                           recent_employees=recent_employees,
                           top_performers=formatted_performers,
                           today=date.today,
                           defaultData=defaultData)

# Employee Management (Owner only)
from datetime import datetime, date


@app.route('/employees/hierarchy')
@login_required
def employees_hierarchy():
    """عرض الهيكل التنظيمي الكامل للموظفين مع جميع البيانات التابعة"""
    if not check_permission('can_view_employees'):
        flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))

    try:
        # الحصول على معاملات الفلترة
        company_id = request.args.get('company_id', type=int)
        position = request.args.get('position', '')
        status = request.args.get('status', 'active')
        search = request.args.get('search', '')

        # بناء استعلام الموظفين
        query = Employee.query

        if company_id:
            query = query.filter_by(company_id=company_id)

        if position and position != 'all':
            query = query.filter_by(position=position)

        if status == 'active':
            query = query.filter_by(is_active=True)
        elif status == 'inactive':
            query = query.filter_by(is_active=False)

        if search:
            query = query.filter(
                db.or_(
                    Employee.full_name.ilike(f'%{search}%'),
                    Employee.code.ilike(f'%{search}%'),
                    Employee.phone.ilike(f'%{search}%')
                )
            )

        # تنفيذ الاستعلام
        employees = query.order_by(Employee.full_name).all()

        # تجهيز بيانات الشركات
        companies = Company.query.filter_by(is_active=True).all()

        # تجهيز إحصائيات سريعة
        stats = {
            'total': len(employees),
            'active': sum(1 for e in employees if e.is_active),
            'supervisors': sum(1 for e in employees if e.position == 'supervisor'),
            'monitors': sum(1 for e in employees if e.position == 'monitor'),
            'workers': sum(1 for e in employees if e.position == 'worker')
        }

        # تجهيز بيانات الهيكل التنظيمي
        hierarchy_data = []
        for company in companies:
            if company_id and company.id != company_id:
                continue

            company_employees = [e for e in employees if e.company_id == company.id]
            if not company_employees:
                continue

            company_info = {
                'id': company.id,
                'name': company.name,
                'total_employees': len(company_employees),
                'supervisors': [],
                'independent_monitors': [],
                'independent_workers': []
            }

            # تجميع المشرفين
            supervisors = [e for e in company_employees if e.position == 'supervisor']
            for supervisor in supervisors:
                # المناطق التي يشرف عليها هذا المشرف
                supervised_areas = Area.query.filter_by(
                    supervisor_id=supervisor.id,
                    is_active=True
                ).all()

                supervisor_areas = []
                for area in supervised_areas:
                    # المواقع في هذه المنطقة
                    locations = Location.query.filter_by(
                        area_id=area.id,
                        is_active=True
                    ).all()

                    area_info = {
                        'id': area.id,
                        'name': area.name,
                        'locations': []
                    }

                    for location in locations:
                        # الأماكن في هذا الموقع
                        places = Place.query.filter_by(
                            location_id=location.id,
                            is_active=True
                        ).all()

                        location_info = {
                            'id': location.id,
                            'name': location.name,
                            'monitor': location.monitor.full_name if location.monitor else 'غير معين',
                            'places': []
                        }

                        for place in places:
                            place_info = {
                                'id': place.id,
                                'name': place.name,
                                'worker': place.worker.full_name if place.worker else 'غير معين'
                            }
                            location_info['places'].append(place_info)

                        area_info['locations'].append(location_info)

                    supervisor_areas.append(area_info)

                supervisor_info = {
                    'id': supervisor.id,
                    'name': supervisor.full_name,
                    'phone': supervisor.phone or 'لا يوجد',
                    'areas': supervisor_areas
                }
                company_info['supervisors'].append(supervisor_info)

            # الحصول على جميع معرفات العمال المرتبطين
            assigned_worker_ids = set()
            for sup in company_info['supervisors']:
                for area in sup['areas']:
                    for loc in area['locations']:
                        for place in loc['places']:
                            # استخراج اسم العامل وليس الكائن
                            if place['worker'] != 'غير معين':
                                # البحث عن الموظف بالاسم (طريقة تقريبية)
                                worker = Employee.query.filter_by(
                                    full_name=place['worker'],
                                    company_id=company.id,
                                    position='worker'
                                ).first()
                                if worker:
                                    assigned_worker_ids.add(worker.id)

            # إضافة المراقبين غير المرتبطين بمشرف معين
            monitors = [e for e in company_employees if e.position == 'monitor'
                        and e.id not in [s['id'] for s in company_info['supervisors']]]

            for monitor in monitors:
                # المواقع التي يراقبها
                monitored_locations = Location.query.filter_by(
                    monitor_id=monitor.id,
                    is_active=True
                ).all()

                monitor_info = {
                    'id': monitor.id,
                    'name': monitor.full_name,
                    'phone': monitor.phone or 'لا يوجد',
                    'supervisor': Employee.query.get(
                        monitor.supervisor_id).full_name if monitor.supervisor_id else 'غير مرتبط',
                    'locations': []
                }

                for location in monitored_locations:
                    places = Place.query.filter_by(
                        location_id=location.id,
                        is_active=True
                    ).all()

                    location_info = {
                        'id': location.id,
                        'name': location.name,
                        'places': []
                    }

                    for place in places:
                        place_info = {
                            'id': place.id,
                            'name': place.name,
                            'worker': place.worker.full_name if place.worker else 'غير معين'
                        }
                        location_info['places'].append(place_info)

                    monitor_info['locations'].append(location_info)

                company_info['independent_monitors'].append(monitor_info)

            # إضافة العمال غير المرتبطين
            workers = [e for e in company_employees if e.position == 'worker'
                       and e.id not in assigned_worker_ids]

            for worker in workers:
                worker_info = {
                    'id': worker.id,
                    'name': worker.full_name,
                    'phone': worker.phone or 'لا يوجد',
                    'supervisor': Employee.query.get(
                        worker.supervisor_id).full_name if worker.supervisor_id else 'غير مرتبط',
                    'assigned_places': []
                }

                # الأماكن التي يعمل بها هذا العامل
                assigned_places = Place.query.filter_by(
                    worker_id=worker.id,
                    is_active=True
                ).all()

                for place in assigned_places:
                    place_info = {
                        'id': place.id,
                        'name': place.name,
                        'location': place.location.name if place.location else 'غير معروف',
                        'area': place.location.area.name if place.location and place.location.area else 'غير معروف'
                    }
                    worker_info['assigned_places'].append(place_info)

                company_info['independent_workers'].append(worker_info)

            hierarchy_data.append(company_info)

        return render_template('employees/hierarchy.html',
                               hierarchy_data=hierarchy_data,
                               companies=companies,
                               selected_company=company_id,
                               selected_position=position,
                               selected_status=status,
                               search_query=search,
                               stats=stats,
                               today=date.today())

    except Exception as e:
        app.logger.error(f"❌ Error in employees_hierarchy: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        flash(f'حدث خطأ: {str(e)}', 'error')
        return redirect(url_for('employees_list'))


@app.route('/employees/comprehensive')
@login_required
def employees_comprehensive():
    """عرض جميع بيانات الموظفين بشكل شامل مع الرواتب والسلف والجزاءات والساعات الإضافية"""
    if not check_permission('can_view_employees'):
        flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))

    try:
        # الحصول على معاملات الفلترة
        company_id = request.args.get('company_id', type=int)
        position = request.args.get('position', '')
        status = request.args.get('status', 'active')
        search = request.args.get('search', '')
        month = request.args.get('month', type=int, default=date.today().month)
        year = request.args.get('year', type=int, default=date.today().year)

        # حساب تاريخ بداية ونهاية الشهر المحدد
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        # بناء استعلام الموظفين
        query = Employee.query

        if company_id:
            query = query.filter_by(company_id=company_id)

        if position and position != 'all':
            query = query.filter_by(position=position)

        if status == 'active':
            query = query.filter_by(is_active=True)
        elif status == 'inactive':
            query = query.filter_by(is_active=False)

        if search:
            query = query.filter(
                db.or_(
                    Employee.full_name.ilike(f'%{search}%'),
                    Employee.code.ilike(f'%{search}%'),
                    Employee.phone.ilike(f'%{search}%')
                )
            )

        # تنفيذ الاستعلام
        employees = query.order_by(Employee.full_name).all()

        # تجهيز بيانات الشركات
        companies = Company.query.filter_by(is_active=True).all()

        # تجهيز البيانات الشاملة لكل موظف
        comprehensive_data = []

        # إحصائيات عامة
        total_stats = {
            'total_employees': len(employees),
            'total_salaries': 0,
            'total_overtime': 0,
            'total_loans': 0,
            'total_penalties': 0,
            'total_attendance': 0,
            'total_absences': 0,
            'total_late': 0
        }

        for employee in employees:
            # ============================================
            # 1. بيانات الموظف الأساسية
            # ============================================
            position_ar = {
                'supervisor': 'مشرف',
                'monitor': 'مراقب',
                'worker': 'عامل',
                'owner': 'مالك',
                'admin': 'إداري'
            }.get(employee.position, employee.position)

            # ============================================
            # 2. بيانات الحضور للشهر المحدد
            # ============================================
            attendance_records = Attendance.query.filter(
                Attendance.employee_id == employee.id,
                Attendance.date >= start_date,
                Attendance.date <= end_date
            ).all()

            present_days = len([r for r in attendance_records if r.status == 'present'])
            absent_days = len([r for r in attendance_records if r.status == 'absent'])
            late_days = len([r for r in attendance_records if r.status == 'late'])
            total_days = (end_date - start_date).days + 1

            attendance_rate = round((present_days / total_days) * 100, 1) if total_days > 0 else 0

            # ============================================
            # 3. الساعات الإضافية
            # ============================================
            from models import Overtime
            overtime_records = Overtime.query.filter(
                Overtime.employee_id == employee.id,
                Overtime.overtime_date >= start_date,
                Overtime.overtime_date <= end_date
            ).all()

            overtime_hours = sum(r.hours for r in overtime_records)
            overtime_cost = sum(r.cost for r in overtime_records)
            overtime_count = len(overtime_records)

            # ============================================
            # 4. السلف والاقساط
            # ============================================
            from models import EmployeeLoan, LoanInstallment

            # جميع سلف الموظف
            all_loans = EmployeeLoan.query.filter_by(employee_id=employee.id).all()

            # السلف النشطة
            active_loans = [l for l in all_loans if l.status == 'active']

            # إجمالي السلف
            total_loans_amount = sum(l.amount for l in all_loans)

            # المتبقي من السلف
            remaining_loans = sum(l.remaining for l in active_loans)

            # الأقساط المسددة في هذا الشهر
            monthly_installments = LoanInstallment.query.join(
                EmployeeLoan, LoanInstallment.loan_id == EmployeeLoan.id
            ).filter(
                EmployeeLoan.employee_id == employee.id,
                LoanInstallment.payment_date >= start_date,
                LoanInstallment.payment_date <= end_date
            ).all()

            monthly_installments_amount = sum(i.amount for i in monthly_installments)

            # ============================================
            # 5. الجزاءات
            # ============================================
            from models import Penalty
            penalties = Penalty.query.filter(
                Penalty.employee_id == employee.id,
                Penalty.penalty_date >= start_date,
                Penalty.penalty_date <= end_date
            ).all()

            penalties_amount = sum(p.amount for p in penalties)
            penalties_count = len(penalties)

            # ============================================
            # 6. معلومات الموقع والمكان
            # ============================================
            # الأماكن التي يعمل بها الموظف (إذا كان عامل)
            assigned_places = []
            if employee.position == 'worker':
                places = Place.query.filter_by(worker_id=employee.id, is_active=True).all()
                for place in places:
                    assigned_places.append({
                        'id': place.id,
                        'name': place.name,
                        'location': place.location.name if place.location else 'غير معروف',
                        'area': place.location.area.name if place.location and place.location.area else 'غير معروف',
                        'company': place.location.area.company.name if place.location and place.location.area and place.location.area.company else 'غير معروف'
                    })

            # المناطق التي يشرف عليها (إذا كان مشرف)
            supervised_areas = []
            if employee.position == 'supervisor':
                areas = Area.query.filter_by(supervisor_id=employee.id, is_active=True).all()
                for area in areas:
                    supervised_areas.append({
                        'id': area.id,
                        'name': area.name,
                        'company': area.company.name if area.company else 'غير معروف',
                        'locations_count': len(area.locations)
                    })

            # المواقع التي يراقبها (إذا كان مراقب)
            monitored_locations = []
            if employee.position == 'monitor':
                locations = Location.query.filter_by(monitor_id=employee.id, is_active=True).all()
                for location in locations:
                    monitored_locations.append({
                        'id': location.id,
                        'name': location.name,
                        'area': location.area.name if location.area else 'غير معروف',
                        'company': location.area.company.name if location.area and location.area.company else 'غير معروف',
                        'places_count': len(location.places)
                    })

            # ============================================
            # 7. حساب الراتب للشهر
            # ============================================
            daily_rate = round(employee.salary / 30, 2) if employee.salary else 0
            base_pay = daily_rate * present_days

            # إجمالي الخصومات (الجزاءات + أقساط السلف)
            total_deductions = penalties_amount + monthly_installments_amount

            # صافي الراتب
            net_salary = base_pay + overtime_cost - total_deductions

            # تحديث الإحصائيات العامة
            total_stats['total_salaries'] += net_salary
            total_stats['total_overtime'] += overtime_cost
            total_stats['total_loans'] += monthly_installments_amount
            total_stats['total_penalties'] += penalties_amount
            total_stats['total_attendance'] += present_days
            total_stats['total_absences'] += absent_days
            total_stats['total_late'] += late_days

            # ============================================
            # 8. تجميع بيانات الموظف
            # ============================================
            employee_data = {
                'id': employee.id,
                'code': employee.code,
                'name': employee.full_name,
                'position': position_ar,
                'position_en': employee.position,
                'phone': employee.phone or 'لا يوجد',
                'email': employee.user.email if employee.user else 'لا يوجد',
                'hire_date': employee.hire_date.strftime('%Y-%m-%d') if employee.hire_date else 'غير محدد',
                'is_active': employee.is_active,
                'company': employee.company.name if employee.company else 'غير محدد',
                'company_id': employee.company_id,
                'salary': employee.salary or 0,
                'daily_rate': daily_rate,

                # بيانات الحضور
                'present_days': present_days,
                'absent_days': absent_days,
                'late_days': late_days,
                'total_days': total_days,
                'attendance_rate': attendance_rate,

                # الساعات الإضافية
                'overtime_hours': round(overtime_hours, 1),
                'overtime_cost': round(overtime_cost, 2),
                'overtime_count': overtime_count,

                # السلف
                'total_loans': round(total_loans_amount, 2),
                'remaining_loans': round(remaining_loans, 2),
                'active_loans_count': len(active_loans),
                'monthly_installments': round(monthly_installments_amount, 2),
                'has_active_loans': len(active_loans) > 0,

                # الجزاءات
                'penalties_amount': round(penalties_amount, 2),
                'penalties_count': penalties_count,

                # الراتب
                'base_pay': round(base_pay, 2),
                'total_deductions': round(total_deductions, 2),
                'net_salary': round(net_salary, 2),

                # المواقع والأماكن
                'assigned_places': assigned_places,
                'supervised_areas': supervised_areas,
                'monitored_locations': monitored_locations,

                # مؤشرات
                'performance_score': round((net_salary / employee.salary * 100) if employee.salary else 0, 1),
                'loan_to_salary_ratio': round((remaining_loans / employee.salary * 100) if employee.salary else 0, 1)
            }

            comprehensive_data.append(employee_data)

        # ترتيب الموظفين حسب الاسم
        comprehensive_data.sort(key=lambda x: x['name'])

        # أشهر السنة
        month_names = {
            1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
            5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
            9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
        }

        # السنوات المتاحة
        years = list(range(2020, date.today().year + 2))

        return render_template('employees/comprehensive.html',
                               employees=comprehensive_data,
                               companies=companies,
                               month_names=month_names,
                               years=years,
                               selected_company=company_id,
                               selected_position=position,
                               selected_status=status,
                               selected_month=month,
                               selected_year=year,
                               search_query=search,
                               stats=total_stats,
                               today=date.today(),
                               month_name=month_names.get(month, ''),
                               start_date=start_date,
                               end_date=end_date)

    except Exception as e:
        app.logger.error(f"❌ Error in employees_comprehensive: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        flash(f'حدث خطأ: {str(e)}', 'error')
        return redirect(url_for('employees_list'))


@app.route('/employees/financial')
@login_required
def employees_financial():
    """عرض البيانات المالية الشاملة للموظفين: الرواتب، السلف، الجزاءات، الساعات الإضافية"""
    if not check_permission('can_view_employees'):
        flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))

    try:
        # الحصول على معاملات الفلترة
        company_id = request.args.get('company_id', type=int)
        position = request.args.get('position', '')
        status = request.args.get('status', 'active')
        search = request.args.get('search', '')
        month = request.args.get('month', type=int, default=date.today().month)
        year = request.args.get('year', type=int, default=date.today().year)

        # حساب تاريخ بداية ونهاية الشهر المحدد
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        # بناء استعلام الموظفين
        query = Employee.query

        if company_id:
            query = query.filter_by(company_id=company_id)

        if position and position != 'all':
            query = query.filter_by(position=position)

        if status == 'active':
            query = query.filter_by(is_active=True)
        elif status == 'inactive':
            query = query.filter_by(is_active=False)

        if search:
            query = query.filter(
                db.or_(
                    Employee.full_name.ilike(f'%{search}%'),
                    Employee.code.ilike(f'%{search}%'),
                    Employee.phone.ilike(f'%{search}%')
                )
            )

        # تنفيذ الاستعلام
        employees = query.order_by(Employee.full_name).all()

        # تجهيز بيانات الشركات
        companies = Company.query.filter_by(is_active=True).all()

        # تجهيز البيانات المالية لكل موظف
        financial_data = []

        # إحصائيات عامة
        total_stats = {
            'total_employees': len(employees),
            'total_base_salaries': 0,
            'total_overtime': 0,
            'total_loans': 0,
            'total_penalties': 0,
            'total_attendance_days': 0,
            'total_net_salaries': 0,
            'employees_with_loans': 0,
            'employees_with_penalties': 0,
            'total_loan_remaining': 0
        }

        for employee in employees:
            # ============================================
            # 1. بيانات الموظف الأساسية
            # ============================================
            position_ar = {
                'supervisor': 'مشرف',
                'monitor': 'مراقب',
                'worker': 'عامل',
                'owner': 'مالك',
                'admin': 'إداري'
            }.get(employee.position, employee.position)

            # ============================================
            # 2. بيانات الحضور للشهر المحدد
            # ============================================
            attendance_records = Attendance.query.filter(
                Attendance.employee_id == employee.id,
                Attendance.date >= start_date,
                Attendance.date <= end_date
            ).all()

            present_days = len([r for r in attendance_records if r.status == 'present'])
            absent_days = len([r for r in attendance_records if r.status == 'absent'])
            late_days = len([r for r in attendance_records if r.status == 'late'])
            total_days = (end_date - start_date).days + 1

            attendance_rate = round((present_days / total_days) * 100, 1) if total_days > 0 else 0

            # ============================================
            # 3. الساعات الإضافية
            # ============================================
            from models import Overtime
            overtime_records = Overtime.query.filter(
                Overtime.employee_id == employee.id,
                Overtime.overtime_date >= start_date,
                Overtime.overtime_date <= end_date
            ).all()

            overtime_hours = sum(r.hours for r in overtime_records)
            overtime_cost = sum(r.cost for r in overtime_records)
            overtime_count = len(overtime_records)

            # ============================================
            # 4. السلف والاقساط
            # ============================================
            from models import EmployeeLoan, LoanInstallment

            # جميع سلف الموظف
            all_loans = EmployeeLoan.query.filter_by(employee_id=employee.id).all()

            # السلف النشطة
            active_loans = [l for l in all_loans if l.status == 'active']

            # إجمالي السلف
            total_loans_amount = sum(l.amount for l in all_loans)

            # المتبقي من السلف
            remaining_loans = sum(l.remaining for l in active_loans)

            # الأقساط المسددة في هذا الشهر
            monthly_installments = LoanInstallment.query.join(
                EmployeeLoan, LoanInstallment.loan_id == EmployeeLoan.id
            ).filter(
                EmployeeLoan.employee_id == employee.id,
                LoanInstallment.payment_date >= start_date,
                LoanInstallment.payment_date <= end_date
            ).all()

            monthly_installments_amount = sum(i.amount for i in monthly_installments)

            # ============================================
            # 5. الجزاءات
            # ============================================
            from models import Penalty
            penalties = Penalty.query.filter(
                Penalty.employee_id == employee.id,
                Penalty.penalty_date >= start_date,
                Penalty.penalty_date <= end_date
            ).all()

            penalties_amount = sum(p.amount for p in penalties)
            penalties_count = len(penalties)

            # ============================================
            # 6. حساب الراتب للشهر
            # ============================================
            daily_rate = round(employee.salary / 30, 2) if employee.salary else 0
            base_pay = daily_rate * present_days

            # إجمالي الخصومات (الجزاءات + أقساط السلف)
            total_deductions = penalties_amount + monthly_installments_amount

            # صافي الراتب
            net_salary = base_pay + overtime_cost - total_deductions

            # تحديث الإحصائيات العامة
            total_stats['total_base_salaries'] += base_pay
            total_stats['total_overtime'] += overtime_cost
            total_stats['total_loans'] += monthly_installments_amount
            total_stats['total_penalties'] += penalties_amount
            total_stats['total_attendance_days'] += present_days
            total_stats['total_net_salaries'] += net_salary

            if active_loans:
                total_stats['employees_with_loans'] += 1
                total_stats['total_loan_remaining'] += remaining_loans

            if penalties_count > 0:
                total_stats['employees_with_penalties'] += 1

            # ============================================
            # 7. تجميع البيانات المالية للموظف
            # ============================================
            employee_data = {
                'id': employee.id,
                'code': employee.code,
                'name': employee.full_name,
                'position': position_ar,
                'position_en': employee.position,
                'company': employee.company.name if employee.company else 'غير محدد',
                'company_id': employee.company_id,
                'is_active': employee.is_active,

                # بيانات الراتب الأساسي
                'base_salary': employee.salary or 0,
                'daily_rate': daily_rate,

                # بيانات الحضور
                'present_days': present_days,
                'absent_days': absent_days,
                'late_days': late_days,
                'total_days': total_days,
                'attendance_rate': attendance_rate,

                # بيانات الراتب المحتسب
                'base_pay': round(base_pay, 2),
                'overtime_hours': round(overtime_hours, 1),
                'overtime_cost': round(overtime_cost, 2),
                'overtime_count': overtime_count,

                # بيانات السلف
                'total_loans': round(total_loans_amount, 2),
                'remaining_loans': round(remaining_loans, 2),
                'active_loans_count': len(active_loans),
                'monthly_installments': round(monthly_installments_amount, 2),
                'has_active_loans': len(active_loans) > 0,

                # بيانات الجزاءات
                'penalties_amount': round(penalties_amount, 2),
                'penalties_count': penalties_count,

                # إجمالي الخصومات والصافي
                'total_deductions': round(total_deductions, 2),
                'net_salary': round(net_salary, 2),

                # مؤشرات مالية
                'deduction_ratio': round((total_deductions / base_pay * 100), 1) if base_pay > 0 else 0,
                'overtime_ratio': round((overtime_cost / base_pay * 100), 1) if base_pay > 0 else 0,
                'loan_ratio': round((remaining_loans / employee.salary * 100), 1) if employee.salary else 0
            }

            financial_data.append(employee_data)

        # ترتيب الموظفين حسب الاسم
        financial_data.sort(key=lambda x: x['name'])

        # أشهر السنة
        month_names = {
            1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
            5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
            9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
        }

        # السنوات المتاحة
        years = list(range(2020, date.today().year + 2))

        return render_template('employees/financial.html',
                               employees=financial_data,
                               companies=companies,
                               month_names=month_names,
                               years=years,
                               selected_company=company_id,
                               selected_position=position,
                               selected_status=status,
                               selected_month=month,
                               selected_year=year,
                               search_query=search,
                               stats=total_stats,
                               today=date.today(),
                               month_name=month_names.get(month, ''),
                               start_date=start_date,
                               end_date=end_date)

    except Exception as e:
        app.logger.error(f"❌ Error in employees_financial: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        flash(f'حدث خطأ: {str(e)}', 'error')
        return redirect(url_for('employees_list'))

# ============================================
# تصدير البيانات المالية للموظفين
# ============================================
@app.route('/employees/financial/export/<export_type>')
@login_required
def export_employees_financial(export_type):
    """تصدير البيانات المالية الشاملة للموظفين"""
    if not check_permission('can_view_employees'):
        flash('غير مصرح', 'error')
        return redirect(url_for('dashboard'))

    try:
        # الحصول على معاملات الفلترة
        company_id = request.args.get('company_id', type=int)
        position = request.args.get('position', '')
        status = request.args.get('status', 'active')
        search = request.args.get('search', '')
        month = request.args.get('month', type=int, default=date.today().month)
        year = request.args.get('year', type=int, default=date.today().year)

        # حساب تاريخ بداية ونهاية الشهر المحدد
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        # بناء استعلام الموظفين
        query = Employee.query

        if company_id:
            query = query.filter_by(company_id=company_id)

        if position and position != 'all':
            query = query.filter_by(position=position)

        if status == 'active':
            query = query.filter_by(is_active=True)
        elif status == 'inactive':
            query = query.filter_by(is_active=False)

        if search:
            query = query.filter(
                db.or_(
                    Employee.full_name.ilike(f'%{search}%'),
                    Employee.code.ilike(f'%{search}%'),
                    Employee.phone.ilike(f'%{search}%')
                )
            )

        employees = query.order_by(Employee.full_name).all()
        today = datetime.now()

        # تجهيز البيانات المالية لكل موظف
        financial_data = []

        # إحصائيات عامة
        total_stats = {
            'total_employees': len(employees),
            'total_base_salaries': 0,
            'total_overtime': 0,
            'total_loans': 0,
            'total_penalties': 0,
            'total_attendance_days': 0,
            'total_net_salaries': 0,
            'employees_with_loans': 0,
            'employees_with_penalties': 0,
            'total_loan_remaining': 0
        }

        for employee in employees:
            # بيانات الموظف الأساسية
            position_ar = {
                'supervisor': 'مشرف',
                'monitor': 'مراقب',
                'worker': 'عامل',
                'owner': 'مالك',
                'admin': 'إداري'
            }.get(employee.position, employee.position)

            # بيانات الحضور للشهر المحدد
            attendance_records = Attendance.query.filter(
                Attendance.employee_id == employee.id,
                Attendance.date >= start_date,
                Attendance.date <= end_date
            ).all()

            present_days = len([r for r in attendance_records if r.status == 'present'])
            absent_days = len([r for r in attendance_records if r.status == 'absent'])
            late_days = len([r for r in attendance_records if r.status == 'late'])
            total_days = (end_date - start_date).days + 1

            attendance_rate = round((present_days / total_days) * 100, 1) if total_days > 0 else 0

            # الساعات الإضافية
            from models import Overtime
            overtime_records = Overtime.query.filter(
                Overtime.employee_id == employee.id,
                Overtime.overtime_date >= start_date,
                Overtime.overtime_date <= end_date
            ).all()

            overtime_hours = sum(r.hours for r in overtime_records)
            overtime_cost = sum(r.cost for r in overtime_records)

            # السلف
            from models import EmployeeLoan, LoanInstallment

            all_loans = EmployeeLoan.query.filter_by(employee_id=employee.id).all()
            active_loans = [l for l in all_loans if l.status == 'active']
            total_loans_amount = sum(l.amount for l in all_loans)
            remaining_loans = sum(l.remaining for l in active_loans)

            # الأقساط المسددة في هذا الشهر
            monthly_installments = LoanInstallment.query.join(
                EmployeeLoan, LoanInstallment.loan_id == EmployeeLoan.id
            ).filter(
                EmployeeLoan.employee_id == employee.id,
                LoanInstallment.payment_date >= start_date,
                LoanInstallment.payment_date <= end_date
            ).all()

            monthly_installments_amount = sum(i.amount for i in monthly_installments)

            # الجزاءات
            from models import Penalty
            penalties = Penalty.query.filter(
                Penalty.employee_id == employee.id,
                Penalty.penalty_date >= start_date,
                Penalty.penalty_date <= end_date
            ).all()

            penalties_amount = sum(p.amount for p in penalties)
            penalties_count = len(penalties)

            # حساب الراتب للشهر
            daily_rate = round(employee.salary / 30, 2) if employee.salary else 0
            base_pay = daily_rate * present_days
            total_deductions = penalties_amount + monthly_installments_amount
            net_salary = base_pay + overtime_cost - total_deductions

            # تحديث الإحصائيات
            total_stats['total_base_salaries'] += base_pay
            total_stats['total_overtime'] += overtime_cost
            total_stats['total_loans'] += monthly_installments_amount
            total_stats['total_penalties'] += penalties_amount
            total_stats['total_attendance_days'] += present_days
            total_stats['total_net_salaries'] += net_salary

            if active_loans:
                total_stats['employees_with_loans'] += 1
                total_stats['total_loan_remaining'] += remaining_loans

            if penalties_count > 0:
                total_stats['employees_with_penalties'] += 1

            financial_data.append({
                'code': employee.code or '-',
                'name': employee.full_name,
                'position': position_ar,
                'company': employee.company.name if employee.company else '-',
                'base_salary': employee.salary or 0,
                'present_days': present_days,
                'base_pay': round(base_pay, 2),
                'overtime_hours': round(overtime_hours, 1),
                'overtime_cost': round(overtime_cost, 2),
                'monthly_installments': round(monthly_installments_amount, 2),
                'remaining_loans': round(remaining_loans, 2),
                'penalties_amount': round(penalties_amount, 2),
                'penalties_count': penalties_count,
                'total_deductions': round(total_deductions, 2),
                'net_salary': round(net_salary, 2),
                'attendance_rate': attendance_rate,
                'is_active': employee.is_active
            })

        if export_type == 'excel':
            rows = []
            for emp in financial_data:
                rows.append({
                    'الكود': emp['code'],
                    'الموظف': emp['name'],
                    'الوظيفة': emp['position'],
                    'الشركة': emp['company'],
                    'الراتب الأساسي': emp['base_salary'],
                    'أيام الحضور': emp['present_days'],
                    'الراتب المحتسب': emp['base_pay'],
                    'ساعات إضافية': emp['overtime_hours'],
                    'قيمة الساعات': emp['overtime_cost'],
                    'أقساط السلف': emp['monthly_installments'],
                    'باقي السلف': emp['remaining_loans'],
                    'الجزاءات': emp['penalties_amount'],
                    'إجمالي الخصومات': emp['total_deductions'],
                    'صافي الراتب': emp['net_salary'],
                    'نسبة الحضور': f"{emp['attendance_rate']}%",
                    'الحالة': 'نشط' if emp['is_active'] else 'غير نشط'
                })

            headers = [
                'الكود', 'الموظف', 'الوظيفة', 'الشركة', 'الراتب الأساسي',
                'أيام الحضور', 'الراتب المحتسب', 'ساعات إضافية', 'قيمة الساعات',
                'أقساط السلف', 'باقي السلف', 'الجزاءات', 'إجمالي الخصومات',
                'صافي الراتب', 'نسبة الحضور', 'الحالة'
            ]
            report_name = f"البيانات المالية للموظفين {month}-{year}"
            filename_prefix = f"employees_financial_{year}{month:02d}"
            return export_report(export_type, report_name, headers, rows, filename_prefix, 'landscape')
        elif export_type == 'pdf':
            from flask import render_template

            try:
                # أسماء الأشهر
                month_names = {
                    1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
                    5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
                    9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
                }

                html_content = render_template(
                    'reports/employees_financial_pdf_report.html',
                    employees=financial_data,
                    stats=total_stats,
                    month=month,
                    year=year,
                    month_name=month_names.get(month, ''),
                    start_date=start_date,
                    end_date=end_date,
                    today=today,
                    current_user=current_user
                )

                # ✅ استخدام الدالة المساعدة
                response = export_pdf(html_content, f'employees_financial_{year}{month:02d}')
                if response:
                    return response
                else:
                    flash('حدث خطأ في إنشاء PDF', 'error')
                    return redirect(url_for('employees_financial', **request.args))

            except Exception as pdf_error:
                app.logger.error(f"PDF Error: {str(pdf_error)}")
                flash(f'حدث خطأ في إنشاء PDF: {str(pdf_error)}', 'error')
                return redirect(url_for('employees_financial', **request.args))

    except Exception as e:
        app.logger.error(f"Error exporting employees financial: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'حدث خطأ في التصدير: {str(e)}', 'error')
        return redirect(url_for('employees_financial', **request.args))

@app.route('/employees')
@login_required
def employees_list():
    if not check_permission('can_view_employees'):
        flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))


    try:
        # الحصول على معاملات البحث والفلترة
        search = request.args.get('search', '')
        position = request.args.get('position', '')
        status = request.args.get('status', '')
        show_all = request.args.get('show_all', '')

        # بناء الاستعلام الأساسي
        query = Employee.query

        # تطبيق الفلترة حسب البحث
        if search:
            query = query.filter(
                db.or_(
                    Employee.full_name.ilike(f'%{search}%'),
                    Employee.phone.ilike(f'%{search}%'),
                    Employee.position.ilike(f'%{search}%')
                )
            )

        # فلترة حسب الوظيفة
        if position and position != 'all':
            query = query.filter(Employee.position == position)

        # فلترة حسب الحالة
        if status == 'active':
            query = query.filter(Employee.is_active == True)
        elif status == 'inactive':
            query = query.filter(Employee.is_active == False)
        elif show_all == 'true':
            # عرض الكل - لا تطبيق فلترة الحالة
            pass
        else:
            # افتراضي: الموظفين النشطين فقط
            query = query.filter(Employee.is_active == True)

        # ترتيب النتائج
        employees_list = query.order_by(Employee.full_name).all()

        # إحصائيات مفصلة
        total_employees = len(employees_list)
        active_employees = len([e for e in employees_list if e.is_active])
        inactive_employees = total_employees - active_employees

        # إحصائيات حسب المناصب
        positions_stats = {
            'owner': len([e for e in employees_list if e.position == 'owner']),
            'supervisor': len([e for e in employees_list if e.position == 'supervisor']),
            'monitor': len([e for e in employees_list if e.position == 'monitor']),
            'worker': len([e for e in employees_list if e.position == 'worker'])
        }

        # تمرير المتغيرات للقالب
        current_time = datetime.now()
        today = date.today()

        return render_template('employees/list.html',
                               employees=employees_list,
                               today=today,
                               now=current_time,
                               search_query=search,
                               selected_position=position,
                               selected_status=status,
                               show_all=show_all,
                               total_employees=total_employees,
                               active_employees=active_employees,
                               inactive_employees=inactive_employees,
                               positions_stats=positions_stats,
                               user_role=current_user.role)

    except Exception as e:
        app.logger.error(f"Error in employees_list: {str(e)}")
        flash('حدث خطأ في تحميل قائمة الموظفين', 'error')
        return render_template('employees/list.html',
                               employees=[],
                               today=date.today(),
                               now=datetime.now(),
                               total_employees=0,
                               active_employees=0,
                               inactive_employees=0,
                               positions_stats={},
                               user_role=current_user.role)
# ============================================
# تصدير قائمة الموظفين
# ============================================
@app.route('/employees/export/<export_type>')
@login_required
def export_employees_list(export_type):
    """تصدير قائمة الموظفين"""
    if not check_permission('can_view_employees'):
        flash('غير مصرح', 'error')
        return redirect(url_for('dashboard'))

    try:
        # الحصول على معاملات البحث والفلترة
        search = request.args.get('search', '')
        position = request.args.get('position', '')
        status = request.args.get('status', '')
        show_all = request.args.get('show_all', '')

        # بناء الاستعلام الأساسي
        query = Employee.query

        if search:
            query = query.filter(
                db.or_(
                    Employee.full_name.ilike(f'%{search}%'),
                    Employee.phone.ilike(f'%{search}%'),
                    Employee.position.ilike(f'%{search}%')
                )
            )

        if position and position != 'all':
            query = query.filter(Employee.position == position)

        if status == 'active':
            query = query.filter(Employee.is_active == True)
        elif status == 'inactive':
            query = query.filter(Employee.is_active == False)
        elif show_all != 'true':
            query = query.filter(Employee.is_active == True)

        employees = query.order_by(Employee.full_name).all()
        today = datetime.now()

        # إحصائيات
        total_employees = len(employees)
        active_count = len([e for e in employees if e.is_active])
        inactive_count = total_employees - active_count

        if export_type == 'excel':
            rows = []
            for emp in employees:
                position_ar = {
                    'supervisor': 'مشرف',
                    'monitor': 'مراقب',
                    'worker': 'عامل',
                    'owner': 'مالك',
                    'admin': 'إداري'
                }.get(emp.position, emp.position)

                rows.append({
                    'الكود': emp.code or '-',
                    'الاسم': emp.full_name,
                    'الوظيفة': position_ar,
                    'الشركة': emp.company.name if emp.company else '-',
                    'رقم الهاتف': emp.phone or '-',
                    'الراتب الأساسي': emp.salary or 0,
                    'الحالة': 'نشط' if emp.is_active else 'غير نشط'
                })

            headers = ['الكود', 'الاسم', 'الوظيفة', 'الشركة', 'رقم الهاتف', 'الراتب الأساسي', 'الحالة']
            report_name = f"قائمة الموظفين {today.strftime('%Y-%m-%d')}"
            filename_prefix = f"employees_list_{today.strftime('%Y%m%d')}"
            return export_report(export_type, report_name, headers, rows, filename_prefix, 'landscape')

        elif export_type == 'pdf':
            from flask import render_template

            try:
                # تجهيز بيانات الموظفين للقالب
                employees_data = []
                for emp in employees:
                    position_ar = {
                        'supervisor': 'مشرف',
                        'monitor': 'مراقب',
                        'worker': 'عامل',
                        'owner': 'مالك',
                        'admin': 'إداري'
                    }.get(emp.position, emp.position)

                    employees_data.append({
                        'code': emp.code or '-',
                        'name': emp.full_name,
                        'position': position_ar,
                        'company': emp.company.name if emp.company else '-',
                        'phone': emp.phone or '-',
                        'salary': emp.salary or 0,
                        'is_active': emp.is_active
                    })

                html_content = render_template(
                    'reports/employees_list_pdf_report.html',
                    employees=employees_data,
                    total_employees=total_employees,
                    active_count=active_count,
                    inactive_count=inactive_count,
                    search_query=search,
                    selected_position=position,
                    selected_status=status,
                    today=today,
                    current_user=current_user
                )

                # ✅ استخدام الدالة المساعدة
                response = export_pdf(html_content, 'employees_list')
                if response:
                    return response
                else:
                    flash('حدث خطأ في إنشاء PDF', 'error')
                    return redirect(url_for('employees_list', **request.args))

            except Exception as pdf_error:
                app.logger.error(f"PDF Error: {str(pdf_error)}")
                flash(f'حدث خطأ في إنشاء PDF: {str(pdf_error)}', 'error')
                return redirect(url_for('employees_list', **request.args))

    except Exception as e:
        app.logger.error(f"Error exporting employees list: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'حدث خطأ في التصدير: {str(e)}', 'error')
        return redirect(url_for('employees_list', **request.args))

@app.route('/employees/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    if not check_permission('can_add_employees'):
        flash('غير مصرح بإضافة موظفين', 'error')
        return redirect(url_for('employees_list'))


    if request.method == 'GET':
        # جلب قائمة الشركات النشطة
        companies = Company.query.filter_by(is_active=True).order_by(Company.name).all()

        # جلب المشرفين النشطين (لاختيار المشرف المباشر)
        supervisors = Employee.query.filter_by(position='supervisor', is_active=True).order_by(Employee.full_name).all()

        return render_template('employees/add.html',
                               today=date.today(),
                               companies=companies,
                               supervisors=supervisors)

    # معالجة POST
    try:
        # استخراج البيانات من النموذج
        full_name = request.form['full_name'].strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        position = request.form['position']
        salary = float(request.form.get('salary', 0))
        hire_date = datetime.strptime(request.form['hire_date'], '%Y-%m-%d').date()
        company_id = request.form.get('company_id')
        supervisor_id = request.form.get('supervisor_id')
        is_active = request.form.get('is_active') == 'on'

        # المؤهل العلمي (للمشرفين والإداريين)
        qualification = None
        if position in ['supervisor', 'admin']:
            qualification = request.form.get('qualification', '')
            if qualification == 'أخرى':
                qualification = request.form.get('qualification_other', '').strip()
            elif qualification:
                qualification = qualification
            else:
                qualification = None

        # التخصص (للمشرفين والإداريين)
        specialization = None
        if position in ['supervisor', 'admin']:
            specialization = request.form.get('specialization', '').strip()
            if not specialization:
                specialization = None

        # التحقق من البيانات المطلوبة
        if not full_name or not position or not hire_date:
            flash('الرجاء ملء جميع الحقول المطلوبة', 'error')
            return redirect(url_for('add_employee'))

        if not company_id:
            flash('الرجاء اختيار الشركة', 'error')
            return redirect(url_for('add_employee'))

        # التحقق من المؤهل العلمي والتخصص للمشرفين والإداريين
        if position in ['supervisor', 'admin']:
            if not qualification:
                flash('المؤهل العلمي مطلوب للمشرفين والإداريين', 'error')
                return redirect(url_for('add_employee'))
            if not specialization:
                flash('التخصص مطلوب للمشرفين والإداريين', 'error')
                return redirect(url_for('add_employee'))

        # توليد الرمز التسلسلي للموظف
        employee_code = Employee.generate_code()

        # إنشاء حساب مستخدم فقط إذا كان المشرف (supervisor)
        user_id = None
        if position == 'supervisor':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()

            if not username or not password:
                flash('اسم المستخدم وكلمة المرور مطلوبان للمشرفين', 'error')
                return redirect(url_for('add_employee'))

            # التحقق من عدم تكرار اسم المستخدم
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('اسم المستخدم موجود مسبقاً', 'error')
                return redirect(url_for('add_employee'))

            # إنشاء المستخدم (بدون إيميل - نضع قيمة افتراضية)
            user = User(
                username=username,
                email=f"{username}@local.local",  # إيميل افتراضي
                role='supervisor',
                is_active=True
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush()
            user_id = user.id

        # إنشاء الموظف
        employee = Employee(
            code=employee_code,
            qualification=qualification,
            specialization=specialization,  # التخصص الجديد
            user_id=user_id,
            full_name=full_name,
            phone=phone,
            address=address,
            position=position,
            salary=salary,
            hire_date=hire_date,
            company_id=int(company_id) if company_id else None,
            supervisor_id=int(supervisor_id) if supervisor_id and supervisor_id.isdigit() else None,
            is_active=is_active
        )

        db.session.add(employee)
        db.session.commit()

        flash(f'✅ تم إضافة الموظف {full_name} برقم {employee_code} بنجاح', 'success')
        return redirect(url_for('employees_list'))

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in add_employee: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        flash(f'❌ حدث خطأ أثناء إضافة الموظف: {str(e)}', 'error')
        return redirect(url_for('add_employee'))

@app.route('/employees/edit/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def edit_employee(employee_id):
    if not check_permission('can_edit_employees'):
        flash('غير مصرح بتعديل بيانات الموظفين', 'error')
        return redirect(url_for('employees_list'))
    """تعديل بيانات موظف مع دعم تغيير الشركة والمشرف"""
    if current_user.role != 'owner':
        flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))

    employee = Employee.query.options(
        db.joinedload(Employee.user)
    ).get_or_404(employee_id)

    if request.method == 'POST':
        try:
            app.logger.info(f"📝 بدء تحديث بيانات الموظف ID: {employee_id}")

            # تحديث بيانات الموظف الأساسية
            employee.full_name = request.form['full_name'].strip()
            employee.phone = request.form.get('phone', '').strip() or None
            employee.address = request.form.get('address', '').strip() or None
            employee.position = request.form['position']
            employee.salary = float(request.form.get('salary', 0)) if request.form.get('salary') else None
            employee.hire_date = datetime.strptime(request.form['hire_date'], '%Y-%m-%d').date()
            employee.is_active = request.form.get('is_active') == 'on'

            # تحديث الشركة (للمالك فقط)
            company_id = request.form.get('company_id')
            if company_id:
                employee.company_id = int(company_id)
                app.logger.info(f"🏢 تم تحديث الشركة إلى ID: {company_id}")

            # تحديث المشرف المباشر (للمراقبين والعمال)
            supervisor_id = request.form.get('supervisor_id')
            if supervisor_id:
                employee.supervisor_id = int(supervisor_id) if supervisor_id.isdigit() else None
                app.logger.info(f"👤 تم تحديث المشرف إلى ID: {supervisor_id}")
            else:
                employee.supervisor_id = None

            # تحديث بيانات المستخدم (للمشرفين)
            if employee.position == 'supervisor':
                # التأكد من وجود حساب مستخدم
                if not employee.user:
                    # إنشاء حساب جديد إذا لم يكن موجوداً
                    username = request.form.get('username', '').strip()
                    if not username:
                        flash('اسم المستخدم مطلوب للمشرفين', 'error')
                        return redirect(url_for('edit_employee', employee_id=employee_id))

                    # التحقق من عدم تكرار اسم المستخدم
                    existing_user = User.query.filter_by(username=username).first()
                    if existing_user and existing_user.id != (employee.user.id if employee.user else 0):
                        flash('اسم المستخدم موجود مسبقاً', 'error')
                        return redirect(url_for('edit_employee', employee_id=employee_id))

                    # إنشاء مستخدم جديد
                    user = User(
                        username=username,
                        email=request.form.get('email', f"{username}@local.local"),
                        role='supervisor',
                        is_active=employee.is_active
                    )
                    user.set_password(request.form.get('password', 'default123'))
                    db.session.add(user)
                    db.session.flush()
                    employee.user_id = user.id
                    app.logger.info(f"✅ تم إنشاء حساب جديد للمشرف: {username}")
                else:
                    # تحديث المستخدم الموجود
                    employee.user.username = request.form.get('username', employee.user.username)
                    employee.user.email = request.form.get('email', employee.user.email)
                    employee.user.is_active = employee.is_active

                    # تحديث كلمة المرور إذا تم إدخالها
                    password = request.form.get('password')
                    if password:
                        employee.user.set_password(password)
                        app.logger.info("🔑 تم تحديث كلمة المرور")

            employee.updated_at = datetime.utcnow()
            db.session.commit()

            flash(f'✅ تم تحديث بيانات الموظف {employee.full_name} بنجاح', 'success')
            return redirect(url_for('employees_list'))

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"❌ خطأ في تحديث الموظف: {str(e)}")
            import traceback
            app.logger.error(f"🔍 تفاصيل الخطأ: {traceback.format_exc()}")
            flash(f'حدث خطأ أثناء تحديث الموظف: {str(e)}', 'error')
            return redirect(url_for('edit_employee', employee_id=employee_id))

    # GET request - عرض نموذج التعديل
    try:
        # جلب قائمة الشركات النشطة
        companies = Company.query.filter_by(is_active=True).order_by(Company.name).all()

        # جلب جميع المشرفين النشطين (لاختيار المشرف المباشر)
        supervisors = Employee.query.filter_by(
            position='supervisor',
            is_active=True
        ).order_by(Employee.full_name).all()

        app.logger.info(f"📊 تم تحميل {len(companies)} شركة و {len(supervisors)} مشرف")
        app.logger.info(
            f"👤 الموظف الحالي: {employee.full_name} - الشركة: {employee.company.name if employee.company else 'غير محدد'}")

        return render_template('employees/edit.html',
                               employee=employee,
                               companies=companies,
                               supervisors=supervisors,
                               today=date.today(),
                               now=datetime.now())

    except Exception as e:
        app.logger.error(f"❌ خطأ في تحميل صفحة التعديل: {str(e)}")
        flash('حدث خطأ في تحميل صفحة التعديل', 'error')
        return redirect(url_for('employees_list'))

@app.route('/employees/toggle-status/<int:employee_id>', methods=['POST'])
@login_required
def toggle_employee_status(employee_id):
    """تفعيل/تعطيل حالة الموظف"""
    if current_user.role != 'owner':
        return jsonify({
            'success': False,
            'message': 'غير مصرح بهذا الإجراء'
        }), 403

    try:
        employee = Employee.query.get_or_404(employee_id)
        employee.is_active = not employee.is_active
        employee.updated_at = datetime.utcnow()

        # تعطيل/تفعيل حساب المستخدم أيضاً
        employee.user.is_active = employee.is_active

        db.session.commit()

        status = "تفعيل" if employee.is_active else "تعطيل"
        return jsonify({
            'success': True,
            'message': f'تم {status} الموظف بنجاح',
            'is_active': employee.is_active
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in toggle_employee_status: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء تغيير حالة الموظف'
        }), 500


@app.route('/employees/delete/<int:employee_id>', methods=['POST'])
@login_required
def delete_employee(employee_id):
    if not check_permission('can_delete_employees'):
        return jsonify({
            'success': False,
            'message': 'غير مصرح بحذف الموظفين'
        }), 403
    """حذف موظف"""
    if current_user.role != 'owner':
        return jsonify({
            'success': False,
            'message': 'غير مصرح بهذا الإجراء'
        }), 403

    try:
        employee = Employee.query.get_or_404(employee_id)
        user = employee.user

        # التحقق من عدم وجود بيانات مرتبطة بالموظف
        # المناطق التي يشرف عليها
        has_supervised_areas = Area.query.filter_by(supervisor_id=employee_id).first()
        # المواقع التي يراقبها
        has_monitored_locations = Location.query.filter_by(monitor_id=employee_id).first()
        # الأماكن التي يعمل بها
        has_assigned_places = Place.query.filter_by(worker_id=employee_id).first()
        # التقييمات التي أجراها أو تلقاها
        has_evaluations = CleaningEvaluation.query.filter(
            (CleaningEvaluation.evaluated_employee_id == employee_id) |
            (CleaningEvaluation.evaluator_id == employee_id)
        ).first()

        if any([has_supervised_areas, has_monitored_locations, has_assigned_places, has_evaluations]):
            return jsonify({
                'success': False,
                'message': 'لا يمكن حذف الموظف لأنه مرتبط ببيانات في النظام'
            }), 400

        # الحذف (أو التعطيل كبديل آمن)
        employee.is_active = False
        user.is_active = False
        employee.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'تم حذف الموظف بنجاح'
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in delete_employee: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء حذف الموظف'
        }), 500


from flask import jsonify
from datetime import datetime, date


@app.route('/api/company-stats/<path:company>')
def get_company_stats(company):
    """جلب إحصائيات شركة معينة"""
    try:
        # جلب موظفي الشركة
        employees = Employee.query.filter_by(company=company).all()

        # حساب الإحصائيات
        total = len(employees)
        supervisors = len([e for e in employees if e.position == 'supervisor'])
        monitors = len([e for e in employees if e.position == 'monitor'])
        workers = len([e for e in employees if e.position == 'worker'])
        active = len([e for e in employees if e.is_active])
        inactive = total - active

        # حساب حضور اليوم
        today_date = date.today()
        present_today = 0

        for emp in employees:
            # ابحث عن حضور اليوم
            today_attendance = [a for a in emp.attendance if a.date == today_date]
            if today_attendance and today_attendance[0].status in ['present', 'late']:
                present_today += 1

        attendance_rate = round((present_today / total * 100) if total > 0 else 0)

        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'supervisors': supervisors,
                'monitors': monitors,
                'workers': workers,
                'active': active,
                'inactive': inactive,
                'today_attendance': attendance_rate
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/employees/company/<company>')
def employees_by_company(company):
    """عرض الموظفين حسب الشركة"""
    employees = Employee.query.filter_by(company=company).all()

    # إحصائيات الشركة
    company_stats = {
        'total': len(employees),
        'supervisors': len([e for e in employees if e.position == 'supervisor']),
        'monitors': len([e for e in employees if e.position == 'monitor']),
        'workers': len([e for e in employees if e.position == 'worker']),
    }

    return render_template('employees_by_company.html',
                           employees=employees,
                           company=company,
                           company_stats=company_stats)

from datetime import datetime, date, timedelta
from flask import request, jsonify, render_template, flash
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest

from datetime import datetime, date, timedelta
from flask import request, jsonify, render_template, flash
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest

from sqlalchemy.orm import joinedload
from flask import jsonify, request, render_template, flash
from flask_login import login_required, current_user
from datetime import date, datetime, timedelta
from models import Attendance, Employee, Company, Area, Location, Place, db


def can_record_attendance(user, employee):
    """التحقق من صلاحية المستخدم لتسجيل حضور موظف معين"""

    if user.role == 'owner':
        # المالك: يمكنه تسجيل حضور جميع الموظفين
        return True
    elif user.role == 'supervisor':
        # المشرف: يمكنه تسجيل حضور جميع الموظفين في الشركة
        return True
    elif user.role == 'monitor':
        # المراقب: يمكنه تسجيل حضور العمال في موقعه فقط
        monitor_employee = Employee.query.filter_by(user_id=user.id).first()
        if not monitor_employee:
            return False

        # التحقق من أن الموظف عامل في موقع يراقبه هذا المراقب
        if employee.position != 'worker':
            return False

        # البحث عن أماكن العمل الخاصة بهذا العامل
        worker_places = Place.query.filter_by(worker_id=employee.id).all()
        if not worker_places:
            return False

        # التحقق من أن أحد هذه الأماكن في موقع يراقبه المراقب
        for place in worker_places:
            if place.location.monitor_id == monitor_employee.id:
                return True

        return False

    return False


def get_employees_for_attendance(user, company_id=None, area_id=None, location_id=None):
    """الحصول على الموظفين المسموح للمستخدم برؤيتهم حسب الصلاحيات"""
    try:
        query = Employee.query.filter_by(is_active=True)

        # تطبيق الفلترة حسب صلاحيات المستخدم
        if user.role == 'owner':
            # المالك يرى جميع الموظفين
            pass
        elif user.role == 'supervisor':
            # المشرف يرى الموظفين في الشركات/المناطق التي يشرف عليها
            if user.company_id:
                query = query.filter(Employee.company_id == user.company_id)
            if user.area_id:
                query = query.filter(Employee.area_id == user.area_id)
        elif user.role == 'monitor':
            # المراقب يرى الموظفين في المواقع التي يراقبها
            if user.location_id:
                query = query.filter(Employee.location_id == user.location_id)

        # تطبيق الفلترة الإضافية إذا تم تحديدها
        if company_id:
            query = query.filter(Employee.company_id == company_id)
        if area_id:
            query = query.filter(Employee.area_id == area_id)
        if location_id:
            query = query.filter(Employee.location_id == location_id)

        # ترتيب النتائج
        employees = query.order_by(Employee.full_name.asc()).all()

        app.logger.info(f"✅ تم تحميل {len(employees)} موظف للمستخدم {user.id} (دور: {user.role})")
        if company_id:
            app.logger.info(f"   - مع فلترة الشركة: {company_id}")
        if area_id:
            app.logger.info(f"   - مع فلترة المنطقة: {area_id}")
        if location_id:
            app.logger.info(f"   - مع فلترة الموقع: {location_id}")

        return employees

    except Exception as e:
        app.logger.error(f"❌ خطأ في get_employees_for_attendance: {str(e)}")
        return []

def can_view_employee(user, employee):
    """التحقق من صلاحية المستخدم لعرض بيانات موظف معين"""

    if user.role == 'owner':
        # المالك: يمكنه رؤية جميع الموظفين
        return True

    elif user.role == 'supervisor':
        # المشرف: يمكنه رؤية جميع الموظفين في شركته
        supervisor_employee = Employee.query.filter_by(user_id=user.id).first()
        if not supervisor_employee:
            return False

        # إذا كان الموظف في نفس شركة المشرف
        if employee.company_id == supervisor_employee.company_id:
            return True

        return False

    elif user.role == 'monitor':
        # المراقب: يمكنه رؤية العاملين في موقعه فقط
        monitor_employee = Employee.query.filter_by(user_id=user.id).first()
        if not monitor_employee:
            return False

        # التحقق إذا كان الموظف يعمل في موقع يراقبه هذا المراقب
        worker_places = Place.query.filter_by(worker_id=employee.id).all()
        authorized = any(place.location.monitor_id == monitor_employee.id for place in worker_places)

        return authorized

    return False


from sqlalchemy import text


@app.route('/attendance')
@login_required
def attendance_index():
    """عرض سجل الحضور مع دعم البحث المتقدم بالفترة"""
    try:
        # الحصول على معاملات الفلترة
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        employee_id = request.args.get('employee_id', type=int)
        company_id = request.args.get('company_id', type=int)
        shift_type = request.args.get('shift_type', 'all')

        # معالجة التواريخ
        today_date = date.today()

        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            except ValueError:
                date_from = today_date.replace(day=1)
                flash('صيغة تاريخ البداية غير صحيحة، تم استخدام أول الشهر', 'warning')
        else:
            date_from = today_date.replace(day=1)

        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            except ValueError:
                date_to = today_date
                flash('صيغة تاريخ النهاية غير صحيحة، تم استخدام تاريخ اليوم', 'warning')
        else:
            date_to = today_date

        # التأكد من أن تاريخ البداية <= تاريخ النهاية
        if date_from > date_to:
            date_from, date_to = date_to, date_from
            flash('تم تبديل التواريخ لأن تاريخ البداية أكبر من تاريخ النهاية', 'info')

        # ✅ بناء الاستعلام بدون joinedload في order_by
        attendance_query = db.session.query(Attendance).join(
            Employee, Attendance.employee_id == Employee.id
        ).outerjoin(
            Company, Employee.company_id == Company.id
        ).filter(
            Attendance.date.between(date_from, date_to)
        )

        # تطبيق الفلاتر
        if employee_id:
            attendance_query = attendance_query.filter(Attendance.employee_id == employee_id)

        if shift_type and shift_type != 'all':
            attendance_query = attendance_query.filter(Attendance.shift_type == shift_type)

        # فلتر الشركة
        if company_id:
            attendance_query = attendance_query.filter(Employee.company_id == company_id)

        # ✅ الترتيب باستخدام text() SQL للتأكد من صحة الأسماء
        attendance_records = attendance_query.order_by(
            Attendance.date.desc(),
            text('employees.full_name ASC')  # استخدام النص SQL مباشرة
        ).all()

        # ✅ إحصائيات الحضور
        total_records = len(attendance_records)

        # عدد الحاضرين
        present_count = sum(1 for r in attendance_records if r.status == 'present')

        # عدد المتأخرين
        late_count = sum(1 for r in attendance_records if r.status == 'late')

        # عدد الغائبين
        absent_count = sum(1 for r in attendance_records if r.status == 'absent')

        # بيانات الفلترة
        employees_for_filter = Employee.query.filter_by(is_active=True).order_by(Employee.full_name).all()
        companies = Company.query.filter_by(is_active=True).all()

        # الموظف المحدد
        selected_employee = Employee.query.get(employee_id) if employee_id else None

        # الشركة المحددة
        selected_company = Company.query.get(company_id) if company_id else None

        print(f"✅ تم تحميل {total_records} سجل حضور من {date_from} إلى {date_to}")

        return render_template('attendance/index.html',
                               attendance_records=attendance_records,
                               total_records=total_records,
                               present_count=present_count,
                               late_count=late_count,
                               absent_count=absent_count,
                               employees=employees_for_filter,
                               companies=companies,
                               date_from=date_from,
                               date_to=date_to,
                               selected_employee_id=employee_id,
                               selected_company_id=company_id,
                               selected_shift_type=shift_type,
                               selected_employee=selected_employee,
                               selected_company=selected_company)

    except Exception as e:
        app.logger.error(f"Error in attendance_index: {str(e)}")
        import traceback
        app.logger.error(f"🔍 تفاصيل الخطأ: {traceback.format_exc()}")
        flash('حدث خطأ في تحميل بيانات الحضور', 'error')

        return render_template('attendance/index.html',
                               attendance_records=[],
                               total_records=0,
                               present_count=0,
                               late_count=0,
                               absent_count=0,
                               employees=[],
                               companies=[],
                               date_from=date.today().replace(day=1),
                               date_to=date.today(),
                               selected_employee_id=None,
                               selected_company_id=None,
                               selected_shift_type='all',
                               selected_employee=None,
                               selected_company=None)

@app.route('/attendance/preparation-hub')
@login_required
def preparation_hub():
    """مركز التحضير - يوصل لكل واجهات التحضير"""
    return render_template('attendance/preparation_hub.html',
                           today=date.today())

@app.route('/attendance/add', methods=['GET', 'POST'])
@login_required
def add_attendance():
    if request.method == 'GET':
        if not check_permission('can_record_attendance'):
            flash('غير مصرح بتسجيل الحضور', 'error')
            return redirect(url_for('attendance_index'))
        try:
            # الحصول على الموظفين حسب الصلاحيات
            employees = get_supervised_employees(current_user)

            # التاريخ الافتراضي هو اليوم
            default_date = date.today().isoformat()

            return render_template('attendance/add.html',
                                   employees=employees,
                                   default_date=default_date,
                                   user_role=current_user.role)

        except Exception as e:
            app.logger.error(f"Error in add_attendance (GET): {str(e)}")
            flash('حدث خطأ في تحميل بيانات الموظفين', 'error')
            return render_template('attendance/add.html', employees=[])

    elif request.method == 'POST':
        try:
            # التحقق من الصلاحيات الأساسية
            if current_user.role not in ['owner', 'supervisor', 'monitor']:
                return jsonify({
                    'success': False,
                    'message': 'غير مصرح بهذا الإجراء',
                    'code': 'UNAUTHORIZED'
                }), 403

            # التحقق من البيانات المطلوبة
            required_fields = ['employee_id', 'date', 'status', 'shift_type']
            for field in required_fields:
                if not request.form.get(field):
                    return jsonify({
                        'success': False,
                        'message': f'حقل {field} مطلوب',
                        'code': 'MISSING_REQUIRED_FIELD'
                    }), 400

            # تنظيف البيانات
            employee_id = int(request.form['employee_id'])
            date_str = request.form['date'].strip()
            status = request.form['status'].strip()
            shift_type = request.form['shift_type'].strip()
            notes = request.form.get('notes', '').strip()
            check_in_time = request.form.get('check_in', '').strip()
            check_out_time = request.form.get('check_out', '').strip()

            # التحقق من الصلاحية للموظف المحدد
            if not can_manage_attendance(current_user, employee_id):
                return jsonify({
                    'success': False,
                    'message': 'غير مصرح بتسجيل حضور هذا الموظف',
                    'code': 'UNAUTHORIZED_EMPLOYEE'
                }), 403

            # التحقق من صحة التاريخ
            try:
                attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'صيغة التاريخ غير صحيحة',
                    'code': 'INVALID_DATE'
                }), 400

            # التحقق من وجود الموظف
            employee = Employee.query.filter_by(id=employee_id, is_active=True).first()
            if not employee:
                return jsonify({
                    'success': False,
                    'message': 'الموظف غير موجود أو غير نشط',
                    'code': 'EMPLOYEE_NOT_FOUND'
                }), 404

            # التحقق من عدم تكرار السجل
            existing_attendance = Attendance.query.filter(
                Attendance.employee_id == employee_id,
                Attendance.date == attendance_date,
                Attendance.shift_type == shift_type
            ).first()

            if existing_attendance:
                shift_name = 'صباحية' if shift_type == 'morning' else 'مسائية'
                return jsonify({
                    'success': False,
                    'message': f'تم تسجيل الحضور مسبقاً في الوردية {shift_name}',
                    'code': 'DUPLICATE_ATTENDANCE'
                }), 409

            # معالجة الأوقات
            check_in = None
            check_out = None

            if check_in_time:
                try:
                    check_in = datetime.strptime(check_in_time, '%H:%M').time()
                except ValueError:
                    return jsonify({
                        'success': False,
                        'message': 'صيغة وقت الحضور غير صحيحة',
                        'code': 'INVALID_CHECKIN_TIME'
                    }), 400

            if check_out_time:
                try:
                    check_out = datetime.strptime(check_out_time, '%H:%M').time()
                except ValueError:
                    return jsonify({
                        'success': False,
                        'message': 'صيغة وقت الانصراف غير صحيحة',
                        'code': 'INVALID_CHECKOUT_TIME'
                    }), 400

            # التحقق من تسلسل الأوقات
            if check_in and check_out and check_out <= check_in:
                return jsonify({
                    'success': False,
                    'message': 'وقت الانصراف يجب أن يكون بعد وقت الحضور',
                    'code': 'INVALID_TIME_RANGE'
                }), 400

            # إنشاء سجل الحضور
            attendance = Attendance(
                employee_id=employee_id,
                date=attendance_date,
                status=status,
                shift_type=shift_type,
                check_in=check_in,
                check_out=check_out,
                notes=notes or None
            )

            db.session.add(attendance)
            db.session.commit()

            shift_name = 'صباحية' if shift_type == 'morning' else 'مسائية'
            return jsonify({
                'success': True,
                'message': f'تم تسجيل الحضور بنجاح للوردية {shift_name}',
                'attendance_id': attendance.id,
                'code': 'ATTENDANCE_ADDED'
            }), 201

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error in add_attendance (POST): {str(e)}")
            return jsonify({
                'success': False,
                'message': f'حدث خطأ: {str(e)}',
                'code': 'INTERNAL_ERROR'
            }), 500

@app.route('/attendance/prepare')
@login_required
def prepare_attendance_enhanced():
    """نظام التحضير المتطور (يدعم الفلترة المتقدمة)"""
    if current_user.role not in ['owner', 'supervisor', 'monitor']:
        flash('غير مصرح', 'error')
        return redirect(url_for('dashboard'))

    try:
        # الحصول على معاملات الفلترة (مدمجة من النظام القديم)
        company_id = request.args.get('company_id', type=int)
        area_id = request.args.get('area_id', type=int)
        location_id = request.args.get('location_id', type=int)
        date_str = request.args.get('date', date.today().isoformat())

        # التحقق من صحة التاريخ
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = date.today()
            flash('صيغة التاريخ غير صحيحة، تم استخدام تاريخ اليوم', 'warning')

        # حساب التواريخ للتنقل
        prev_date = selected_date - timedelta(days=1)
        next_date = selected_date + timedelta(days=1)

        # تحديد إذا كان يمكن اختيار التاريخ (للمالك فقط)
        can_select_date = current_user.role == 'owner'
        if current_user.role in ['supervisor', 'monitor']:
            selected_date = date.today()
            can_select_date = False

        # الحصول على الموظفين حسب الصلاحيات والفلترة (مدمجة من النظام القديم)
        employees = get_employees_for_attendance(
            current_user,
            company_id,
            area_id,
            location_id
        )

        # الحصول على سجلات الحضور الحالية
        attendance_records = Attendance.query.filter_by(date=selected_date).all()

        # تجهيز بيانات الحضور الحالية
        existing_attendance = {}
        for record in attendance_records:
            existing_attendance[record.employee_id] = {
                'status': record.status,
                'check_in': record.check_in.strftime('%H:%M') if record.check_in else '',
                'check_out': record.check_out.strftime('%H:%M') if record.check_out else '',
                'notes': record.notes or ''
            }

        # إحصائيات
        stats = {
            'total_employees': len(employees),
            'present_count': len([r for r in attendance_records if r.status == 'present']),
            'absent_count': len([r for r in attendance_records if r.status == 'absent']),
            'late_count': len([r for r in attendance_records if r.status == 'late'])
        }

        # الحصول على قائمة الشركات والمناطق والمواقع للفلترة (مدمجة من النظام القديم)
        companies = Company.query.filter_by(is_active=True).all()
        areas = Area.query.filter_by(is_active=True).all()
        locations = Location.query.filter_by(is_active=True).all()

        return render_template('attendance/prepare_enhanced.html',
                               employees=employees,
                               selected_date=selected_date,
                               prev_date=prev_date,
                               next_date=next_date,
                               can_select_date=can_select_date,
                               existing_attendance=existing_attendance,
                               stats=stats,
                               companies=companies,
                               areas=areas,
                               locations=locations,
                               selected_company_id=company_id,
                               selected_area_id=area_id,
                               selected_location_id=location_id)

    except Exception as e:
        app.logger.error(f"Error in prepare_attendance_enhanced: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        flash('حدث خطأ في تحميل صفحة التحضير', 'error')
        return redirect(url_for('attendance_index'))


@app.route('/attendance/prepare', methods=['GET', 'POST'])
@login_required
def prepare_attendance_enhanced_post():
    """نظام التحضير المتطور - يدعم GET و POST لحفظ البيانات"""
    if current_user.role not in ['owner', 'supervisor', 'monitor']:
        if request.method == 'POST':
            return jsonify({'success': False, 'message': 'غير مصرح'}), 403
        flash('غير مصرح', 'error')
        return redirect(url_for('dashboard'))

    # معالجة طلب POST
    if request.method == 'POST':
        try:
            print("📥 استقبال طلب POST إلى /attendance/prepare")

            # ✅ استقبال البيانات - قد تكون JSON مباشرة
            data = request.get_json()

            print(f"📦 نوع البيانات المستلمة: {type(data)}")

            # إذا كانت البيانات ليست قائمة، نحاول تحويلها
            if not isinstance(data, list):
                if isinstance(data, dict) and 'attendance' in data:
                    data = data['attendance']
                else:
                    data = [data] if isinstance(data, dict) else []

            print(f"📊 عدد سجلات الحضور: {len(data)}")

            saved_count = 0
            errors = []

            for item in data:
                try:
                    employee_id = item.get('employee_id')
                    date_str = item.get('date')
                    status = item.get('status')
                    shift_type = item.get('shift_type', 'morning')
                    check_in = item.get('check_in')
                    check_out = item.get('check_out')
                    notes = item.get('notes', '')

                    # التحقق من البيانات الأساسية
                    if not employee_id or not date_str or not status:
                        errors.append(f"بيانات غير مكتملة: {item}")
                        continue

                    # تحويل التاريخ
                    try:
                        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        errors.append(f"تاريخ غير صالح: {date_str}")
                        continue

                    # البحث عن سجل موجود
                    attendance = Attendance.query.filter_by(
                        employee_id=int(employee_id),
                        date=attendance_date
                    ).first()

                    # معالجة الأوقات
                    check_in_time = None
                    if check_in and check_in.strip():
                        try:
                            check_in_time = datetime.strptime(check_in, '%H:%M').time()
                        except ValueError:
                            pass

                    check_out_time = None
                    if check_out and check_out.strip():
                        try:
                            check_out_time = datetime.strptime(check_out, '%H:%M').time()
                        except ValueError:
                            pass

                    if attendance:
                        # تحديث السجل الموجود
                        attendance.status = status
                        attendance.shift_type = shift_type
                        attendance.check_in = check_in_time
                        attendance.check_out = check_out_time
                        attendance.notes = notes
                    else:
                        # إنشاء سجل جديد
                        attendance = Attendance(
                            employee_id=int(employee_id),
                            date=attendance_date,
                            status=status,
                            shift_type=shift_type,
                            check_in=check_in_time,
                            check_out=check_out_time,
                            notes=notes
                        )
                        db.session.add(attendance)

                    saved_count += 1

                except Exception as e:
                    errors.append(f"خطأ في السجل: {str(e)}")

            db.session.commit()

            message = f'✅ تم حفظ {saved_count} سجل بنجاح'
            if errors:
                message += f' مع {len(errors)} خطأ'

            return jsonify({
                'success': True,
                'message': message,
                'count': saved_count,
                'errors': errors[:5]
            })

        except Exception as e:
            db.session.rollback()
            print(f"❌ خطأ في حفظ الحضور: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'حدث خطأ: {str(e)}'
            }), 500

    # إذا كانت الطريقة GET، استخدم الدالة الأصلية
    return prepare_attendance_enhanced()
# ✅ [جديد] صفحة ترحيل فترات التحضير - عرض النموذج
@app.route('/attendance/transfer', methods=['GET'])
@login_required
def transfer_attendance_page():
    """عرض صفحة ترحيل سجلات الحضور من فترة إلى أخرى"""
    # التحقق من الصلاحيات - المالك فقط
    if current_user.role != 'owner':
        flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))

    # الحصول على قائمة الموظفين للفلترة
    employees = Employee.query.filter_by(is_active=True).order_by(Employee.full_name).all()

    return render_template('attendance/transfer.html',
                           employees=employees,
                           today=date.today())


# ✅ [جديد] معالجة طلب ترحيل فترات التحضير
@app.route('/attendance/transfer', methods=['POST'])
@login_required
def transfer_attendance():
    """ترحيل سجلات الحضور من فترة إلى أخرى"""
    # التحقق من الصلاحيات - المالك فقط
    if current_user.role != 'owner':
        return jsonify({
            'success': False,
            'message': 'غير مصرح بهذا الإجراء'
        }), 403

    try:
        # الحصول على البيانات من النموذج
        from_date_str = request.form.get('from_date')
        to_date_str = request.form.get('to_date')
        target_date_str = request.form.get('target_date')
        employee_id = request.form.get('employee_id', type=int)
        transfer_mode = request.form.get('transfer_mode', 'copy')  # copy أو move

        # التحقق من البيانات المطلوبة
        if not all([from_date_str, to_date_str, target_date_str]):
            return jsonify({
                'success': False,
                'message': 'جميع التواريخ مطلوبة'
            }), 400

        # تحويل التواريخ
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'صيغة التاريخ غير صحيحة'
            }), 400

        # التحقق من صحة التواريخ
        if from_date > to_date:
            return jsonify({
                'success': False,
                'message': 'تاريخ البداية يجب أن يكون قبل تاريخ النهاية'
            }), 400

        # بناء استعلام سجلات الحضور
        query = Attendance.query.filter(
            Attendance.date >= from_date,
            Attendance.date <= to_date
        )

        # تطبيق فلترة الموظف إذا تم تحديده
        if employee_id:
            query = query.filter(Attendance.employee_id == employee_id)

        # الحصول على سجلات الحضور
        source_attendances = query.all()

        if not source_attendances:
            return jsonify({
                'success': False,
                'message': 'لا توجد سجلات حضور في الفترة المحددة'
            }), 404

        # حساب عدد أيام الفترة المصدر
        source_days = (to_date - from_date).days + 1

        # ترحيل السجلات
        transferred_count = 0
        skipped_count = 0

        for source_att in source_attendances:
            # حساب تاريخ الهدف المقابل
            days_diff = (source_att.date - from_date).days
            target_att_date = target_date + timedelta(days=days_diff)

            # التحقق من عدم وجود سجل مكرر في التاريخ الهدف
            existing = Attendance.query.filter_by(
                employee_id=source_att.employee_id,
                date=target_att_date,
                shift_type=source_att.shift_type
            ).first()

            if existing:
                skipped_count += 1
                continue

            # إنشاء سجل حضور جديد
            new_attendance = Attendance(
                employee_id=source_att.employee_id,
                date=target_att_date,
                status=source_att.status,
                shift_type=source_att.shift_type,
                check_in=source_att.check_in,
                check_out=source_att.check_out,
                notes=f"منقول من {source_att.date.strftime('%Y-%m-%d')}: {source_att.notes or ''}"
            )

            db.session.add(new_attendance)
            transferred_count += 1

        # إذا كان وضع الترحيل هو "نقل" (وليس نسخ)، نقوم بحذف السجلات المصدر
        if transfer_mode == 'move':
            for source_att in source_attendances:
                db.session.delete(source_att)

        db.session.commit()

        message = f'✅ تم ترحيل {transferred_count} سجل حضور بنجاح'
        if skipped_count > 0:
            message += f' (تم تخطي {skipped_count} سجل مكرر)'

        return jsonify({
            'success': True,
            'message': message,
            'transferred_count': transferred_count,
            'skipped_count': skipped_count
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in transfer_attendance: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'حدث خطأ: {str(e)}'
        }), 500

@app.route('/api/areas/<int:company_id>')
@login_required
def get_areas_by_company(company_id):
    """الحصول على المناطق التابعة لشركة معينة"""
    try:
        areas = Area.query.filter_by(company_id=company_id).all()
        areas_data = [{'id': area.id, 'name': area.name} for area in areas]
        return jsonify({'success': True, 'areas': areas_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/locations/by-area/<int:area_id>')
@login_required
def get_locations_by_area(area_id):
    """الحصول على المواقع التابعة لمنطقة معينة"""
    try:
        locations = Location.query.filter_by(area_id=area_id, is_active=True).all()
        locations_data = [{'id': loc.id, 'name': loc.name} for loc in locations]
        return jsonify({'success': True, 'locations': locations_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

from sqlalchemy.orm import joinedload


@app.route('/attendance/report')
@login_required
def attendance_report():
    if not check_permission('can_view_attendance_reports'):
        flash('غير مصرح بعرض تقارير الحضور', 'error')
        return redirect(url_for('attendance_index'))

    try:
        # ✅ [تعديل] الحصول على تواريخ الفلترة من الباراميترات
        from_date_str = request.args.get('from_date', '')
        to_date_str = request.args.get('to_date', '')

        # إذا تم تحديد تواريخ، استخدمها، وإلا استخدم الشهر الحالي
        if from_date_str and to_date_str:
            try:
                from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
                to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('صيغة التاريخ غير صحيحة', 'error')
                from_date = date.today().replace(day=1)
                to_date = date.today()
        else:
            # الحصول على الشهر والسنة من الباراميترات (للتوافق مع الإصدار القديم)
            year = request.args.get('year', date.today().year, type=int)
            month = request.args.get('month', date.today().month, type=int)

            # حساب بداية ونهاية الشهر
            from_date = date(year, month, 1)
            if month == 12:
                to_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                to_date = date(year, month + 1, 1) - timedelta(days=1)

        # استعلام مباشر للحصول على سجلات الحضور
        attendance_data = Attendance.query \
            .join(Employee) \
            .filter(
            Attendance.date >= from_date,
            Attendance.date <= to_date
        ) \
            .order_by(Attendance.date.desc()) \
            .all()

        # حساب الإحصائيات
        total_days = (to_date - from_date).days + 1
        employees = Employee.query.filter_by(is_active=True).all()

        # إنشاء تقرير مفصل
        report_data = []
        for employee in employees:
            employee_attendance = Attendance.query.filter(
                Attendance.employee_id == employee.id,
                Attendance.date >= from_date,
                Attendance.date <= to_date
            ).all()

            present_days = sum(1 for record in employee_attendance if record.status == 'present')
            absent_days = sum(1 for record in employee_attendance if record.status == 'absent')
            late_days = sum(1 for record in employee_attendance if record.status == 'late')

            report_data.append({
                'employee': employee,
                'present_days': present_days,
                'absent_days': absent_days,
                'late_days': late_days,
                'attendance_rate': (present_days / total_days) * 100 if total_days > 0 else 0
            })

        return render_template('attendance/report.html',
                               from_date=from_date,
                               to_date=to_date,
                               attendance_data=attendance_data,
                               report_data=report_data,
                               total_days=total_days)

    except Exception as e:
        app.logger.error(f"Error in attendance_report: {str(e)}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return render_template('attendance/report.html',
                               from_date=date.today(),
                               to_date=date.today(),
                               attendance_data=[],
                               report_data=[])

@app.route('/my-attendance')
@login_required
def my_attendance():
    """عرض سجل الحضور الشخصي للموظف"""
    try:
        # الحصول على بيانات الموظف المرتبط بالمستخدم
        employee = Employee.query.filter_by(user_id=current_user.id).first()

        if not employee:
            flash('لا يوجد ملف شخصي للموظف مرتبط بحسابك', 'error')
            return render_template('attendance/my_attendance.html',
                                 records=[],
                                 employee=None,
                                 stats={})

        # الحصول على التاريخ المطلوب
        selected_date = request.args.get('date', date.today().isoformat())
        try:
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except ValueError:
            selected_date = date.today()

        # الحصول على سجلات الحضور للموظف لهذا الشهر
        start_date = date(selected_date.year, selected_date.month, 1)
        if selected_date.month == 12:
            end_date = date(selected_date.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(selected_date.year, selected_date.month + 1, 1) - timedelta(days=1)

        # استعلام سجلات الحضور
        records = Attendance.query\
            .filter(
                Attendance.employee_id == employee.id,
                Attendance.date >= start_date,
                Attendance.date <= end_date
            )\
            .order_by(Attendance.date.desc())\
            .all()

        # حساب الإحصائيات
        present_days = sum(1 for record in records if record.status == 'present')
        total_days = (end_date - start_date).days + 1
        attendance_rate = (present_days / total_days) * 100 if total_days > 0 else 0

        stats = {
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': total_days - present_days,
            'attendance_rate': round(attendance_rate, 1)
        }

        return render_template('attendance/my_attendance.html',
                             records=records,
                             employee=employee,
                             stats=stats,
                             selected_date=selected_date,
                             start_date=start_date,
                             end_date=end_date)

    except Exception as e:
        app.logger.error(f"Database error in my_attendance: {str(e)}")
        flash('حدث خطأ في تحميل سجل الحضور', 'error')
        return render_template('attendance/my_attendance.html',
                             records=[],
                             employee=None,
                             stats={})


# دوال الموظفين المفقودة
@app.route('/employees/<int:id>')
@login_required
def view_employee(id):
    """عرض تفاصيل الموظف"""
    # التحقق من الصلاحيات - للمالك فقط
    if current_user.role != 'owner':
        flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))

    try:
        employee = Employee.query.get_or_404(id)

        # التحقق من الصلاحيات
        if current_user.role not in ['owner', 'supervisor']:
            if current_user.role == 'monitor':
                # المراقب يمكنه رؤية العاملين في موقعه فقط
                monitor_employee = Employee.query.filter_by(user_id=current_user.id).first()
                if not monitor_employee:
                    flash('غير مصرح بالوصول', 'error')
                    return redirect(url_for('dashboard'))

                # التحقق إذا كان الموظف يعمل في موقع يراقبه هذا المراقب
                worker_places = Place.query.filter_by(worker_id=employee.id).all()
                authorized = any(place.location.monitor_id == monitor_employee.id for place in worker_places)
                if not authorized:
                    flash('غير مصرح بالوصول إلى بيانات هذا الموظف', 'error')
                    return redirect(url_for('dashboard'))

        # الحصول على إحصائيات الحضور
        attendance_stats = db.session.query(
            db.func.count(Attendance.id),
            db.func.sum(db.case((Attendance.status == 'present', 1), else_=0)),
            db.func.sum(db.case((Attendance.status == 'absent', 1), else_=0)),
            db.func.sum(db.case((Attendance.status == 'late', 1), else_=0))
        ).filter(Attendance.employee_id == id).first()

        total_records, present_count, absent_count, late_count = attendance_stats or (0, 0, 0, 0)

        # الحصول على آخر 10 سجلات حضور
        recent_attendance = Attendance.query.filter_by(employee_id=id) \
            .order_by(Attendance.date.desc()) \
            .limit(10) \
            .all()

        return render_template('employees/view.html',
                               employee=employee,
                               today=date.today(),
                               now=datetime.now(),
                               total_records=total_records,
                               present_count=present_count,
                               absent_count=absent_count,
                               late_count=late_count,
                               recent_attendance=recent_attendance)

    except Exception as e:
        app.logger.error(f"Error viewing employee {id}: {str(e)}")
        flash('حدث خطأ في تحميل بيانات الموظف', 'error')
        return redirect(url_for('employees_list'))


# دوال الحضور المفقودة
@app.route('/attendance/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_attendance(id):
    """تعديل سجل حضور"""
    try:
        attendance = Attendance.query.get_or_404(id)

        # التحقق من الصلاحيات
        if current_user.role not in ['owner', 'supervisor', 'monitor']:
            flash('غير مصرح بتعديل سجل الحضور', 'error')
            return redirect(url_for('attendance_index'))

        if request.method == 'POST':
            try:
                # تحديث البيانات
                attendance.status = request.form.get('status')
                attendance.shift_type = request.form.get('shift_type')

                # معالجة أوقات الحضور والانصراف
                check_in = request.form.get('check_in')
                check_out = request.form.get('check_out')

                attendance.check_in = datetime.strptime(check_in, '%H:%M').time() if check_in else None
                attendance.check_out = datetime.strptime(check_out, '%H:%M').time() if check_out else None

                attendance.notes = request.form.get('notes')
                attendance.updated_at = datetime.now()

                db.session.commit()

                flash('تم تحديث سجل الحضور بنجاح', 'success')
                return redirect(url_for('attendance_index'))

            except Exception as e:
                db.session.rollback()
                flash(f'حدث خطأ أثناء التحديث: {str(e)}', 'error')

        # GET request - عرض نموذج التعديل
        employees = get_employees_for_attendance(current_user)

        return render_template('attendance/edit.html',
                               attendance=attendance,
                               employees=employees,
                               today=date.today())

    except Exception as e:
        app.logger.error(f"Error editing attendance {id}: {str(e)}")
        flash('حدث خطأ في تحميل بيانات الحضور', 'error')
        return redirect(url_for('attendance_index'))


@app.route('/attendance/delete/<int:id>', methods=['POST'])
@login_required
def delete_attendance(id):
    """حذف سجل حضور"""
    try:
        attendance = Attendance.query.get_or_404(id)

        # التحقق من الصلاحيات
        if current_user.role not in ['owner', 'supervisor']:
            return jsonify({'success': False, 'message': 'غير مصرح بهذا الإجراء'}), 403

        db.session.delete(attendance)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'تم حذف سجل الحضور بنجاح'
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting attendance {id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'حدث خطأ أثناء الحذف: {str(e)}'
        }), 500

from flask import request, jsonify, render_template
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest


# Company Management Routes
@app.route('/companies')
@login_required
def companies_list():
    if not check_permission('can_view_companies'):
        flash('غير مصرح بعرض الشركات', 'error')
        return redirect(url_for('dashboard'))
    """عرض قائمة الشركات - GET فقط"""
    try:
        # التحقق من الصلاحيات
        if current_user.role != 'owner':
            flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
            return redirect(url_for('dashboard'))

        # استعلام محسن مع إحصائيات
        companies = Company.query.order_by(Company.name).all()

        # حساب الإحصائيات
        stats = {
            'total': len(companies),
            'active': len([c for c in companies if c.is_active]),
            'inactive': len([c for c in companies if not c.is_active])
        }

        return render_template('companies/list.html',
                               companies=companies,
                               stats=stats,
                               today=date.today())

    except SQLAlchemyError as e:
        app.logger.error(f"Database error in companies_list: {str(e)}")
        flash('حدث خطأ في تحميل قائمة الشركات', 'error')
        return render_template('companies/list.html',
                               companies=[],
                               stats={'total': 0, 'active': 0, 'inactive': 0})


@app.route('/companies/add', methods=['GET', 'POST'])
@login_required
def add_company():
    """إضافة شركة جديدة - GET و POST"""
    # التحقق من الصلاحيات
    if current_user.role != 'owner':
        flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('companies_list'))

    if request.method == 'GET':
        return render_template('companies/add.html')

    # POST request handling
    try:
        # التحقق من البيانات المطلوبة
        required_fields = ['name']
        for field in required_fields:
            if not request.form.get(field):
                flash(f'حقل {field} مطلوب', 'error')
                return render_template('companies/add.html')

        # تنظيف البيانات المدخلة
        name = request.form['name'].strip()
        address = request.form.get('address', '').strip()
        contact_person = request.form.get('contact_person', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip().lower()

        # التحقق من البريد الإلكتروني إذا كان موجوداً
        if email and not is_valid_email(email):
            flash('صيغة البريد الإلكتروني غير صحيحة', 'error')
            return render_template('companies/add.html')

        # التحقق من عدم تكرار اسم الشركة
        existing_company = Company.query.filter_by(name=name).first()
        if existing_company:
            flash('اسم الشركة موجود مسبقاً', 'error')
            return render_template('companies/add.html')

        # التحقق من البريد الإلكتروني إذا كان موجوداً
        if email:
            existing_email = Company.query.filter_by(email=email).first()
            if existing_email:
                flash('البريد الإلكتروني موجود مسبقاً', 'error')
                return render_template('companies/add.html')

        # إنشاء الشركة جديدة
        company = Company(
            name=name,
            address=address or None,
            contact_person=contact_person or None,
            phone=phone or None,
            email=email or None,
            is_active=request.form.get('is_active') == 'on'
        )

        db.session.add(company)
        db.session.commit()

        flash('تم إضافة الشركة بنجاح', 'success')
        return redirect(url_for('companies_list'))

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in add_company: {str(e)}")
        flash('حدث خطأ أثناء إضافة الشركة', 'error')
        return render_template('companies/add.html')


@app.route('/companies/edit/<int:company_id>', methods=['GET', 'POST'])
@login_required
def edit_company(company_id):
    """تعديل بيانات شركة - GET و POST"""
    # التحقق من الصلاحيات
    if current_user.role != 'owner':
        flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('companies_list'))

    company = Company.query.get_or_404(company_id)

    if request.method == 'GET':
        return render_template('companies/edit.html', company=company)

    # POST request handling
    try:
        # تنظيف البيانات المدخلة
        name = request.form['name'].strip()
        address = request.form.get('address', '').strip()
        contact_person = request.form.get('contact_person', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip().lower()

        # التحقق من البريد الإلكتروني إذا كان موجوداً
        if email and not is_valid_email(email):
            flash('صيغة البريد الإلكتروني غير صحيحة', 'error')
            return render_template('companies/edit.html', company=company)

        # التحقق من عدم تكرار اسم الشركة (استثناء الشركة الحالية)
        existing_company = Company.query.filter(
            Company.name == name,
            Company.id != company_id
        ).first()
        if existing_company:
            flash('اسم الشركة موجود مسبقاً', 'error')
            return render_template('companies/edit.html', company=company)

        # تحديث بيانات الشركة
        company.name = name
        company.address = address or None
        company.contact_person = contact_person or None
        company.phone = phone or None
        company.email = email or None
        company.is_active = request.form.get('is_active') == 'on'
        company.updated_at = datetime.utcnow()

        db.session.commit()
        flash('تم تحديث الشركة بنجاح', 'success')
        return redirect(url_for('companies_list'))

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in edit_company: {str(e)}")
        flash('حدث خطأ أثناء تحديث الشركة', 'error')
        return render_template('companies/edit.html', company=company)


@app.route('/companies/toggle-status/<int:company_id>', methods=['POST'])
@login_required
def toggle_company_status(company_id):
    """تغيير حالة الشركة (تفعيل/تعطيل) - POST فقط"""
    # التحقق من الصلاحيات
    if current_user.role != 'owner':
        return jsonify({
            'success': False,
            'message': 'غير مصرح بهذا الإجراء'
        }), 403

    company = Company.query.get_or_404(company_id)

    try:
        company.is_active = not company.is_active
        company.updated_at = datetime.utcnow()
        db.session.commit()

        status = "تفعيل" if company.is_active else "تعطيل"
        return jsonify({
            'success': True,
            'message': f'تم {status} الشركة بنجاح',
            'is_active': company.is_active
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in toggle_company_status: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء تغيير حالة الشركة'
        }), 500

@app.route('/companies/delete/<int:company_id>', methods=['POST'])
@login_required
def delete_company(company_id):
    """حذف شركة - للمالك فقط"""
    # ✅ التحقق من الصلاحيات - للمالك فقط
    if current_user.role != 'owner':
        return jsonify({
            'success': False,
            'message': 'غير مصرح بهذا الإجراء - المالك فقط يمكنه الحذف'
        }), 403

    company = Company.query.get_or_404(company_id)

    try:
        # التحقق من وجود مناطق مرتبطة بالشركة
        has_areas = Area.query.filter_by(company_id=company_id, is_active=True).first()
        if has_areas:
            return jsonify({
                'success': False,
                'message': 'لا يمكن حذف الشركة لأنها تحتوي على مناطق نشطة. قم بحذف المناطق أولاً.'
            }), 400

        # التحقق من وجود موظفين مرتبطين بالشركة
        has_employees = Employee.query.filter_by(company_id=company_id, is_active=True).first()
        if has_employees:
            return jsonify({
                'success': False,
                'message': 'لا يمكن حذف الشركة لأنها تحتوي على موظفين نشطين. قم بنقل الموظفين أولاً.'
            }), 400

        # التحقق من وجود فواتير مرتبطة بالشركة
        has_invoices = CompanyInvoice.query.filter_by(company_id=company_id).first()
        if has_invoices:
            return jsonify({
                'success': False,
                'message': 'لا يمكن حذف الشركة لأنها تحتوي على فواتير سابقة. قم بحذف الفواتير أولاً.'
            }), 400

        # تعطيل الشركة بدلاً من الحذف الفعلي (Soft Delete)
        company.is_active = False
        company.updated_at = datetime.utcnow()
        db.session.commit()

        # تسجيل العملية في السجل
        app.logger.info(f"✅ تم حذف الشركة {company.name} بواسطة {current_user.username}")

        return jsonify({
            'success': True,
            'message': 'تم حذف الشركة بنجاح',
            'company_id': company_id,
            'company_name': company.name
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in delete_company: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'حدث خطأ أثناء حذف الشركة: {str(e)}'
        }), 500

def is_valid_email(email):
    """دالة مساعدة للتحقق من صحة البريد الإلكتروني"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


# Area Management
@app.route('/companies/<int:company_id>/areas')
@login_required
def company_areas(company_id):
    """عرض مناطق شركة محددة"""
    try:
        print(f"🎯 بدء تحميل مناطق الشركة {company_id}")

        # التحقق من وجود الشركة
        company = Company.query.get(company_id)
        if not company:
            print(f"❌ الشركة {company_id} غير موجودة")
            flash('الشركة غير موجودة', 'error')
            return redirect(url_for('companies_list'))

        print(f"✅ الشركة: {company.name}")

        # التحقق من الصلاحيات بشكل مبسط
        if current_user.role != 'owner':
            # إذا كان مشرفاً، تحقق إذا كان مشرفاً على أي منطقة في هذه الشركة
            if current_user.role == 'supervisor' and current_user.employee_profile:
                supervisor_areas = Area.query.filter_by(
                    supervisor_id=current_user.employee_profile.id,
                    company_id=company_id
                ).first()
                if not supervisor_areas:
                    flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
                    return redirect(url_for('companies_list'))
            else:
                flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
                return redirect(url_for('companies_list'))

        # جلب المناطق مع العلاقات
        areas = Area.query.filter_by(company_id=company_id) \
            .order_by(Area.name) \
            .options(
            db.joinedload(Area.supervisor),
            db.joinedload(Area.locations)
        ) \
            .all()

        print(f"📊 عدد المناطق: {len(areas)}")

        # الموظفون الذين يمكن تعيينهم كمشرفين
        available_supervisors = Employee.query.filter_by(
            position='supervisor',
            is_active=True
        ).all()

        print(f"👥 عدد المشرفين المتاحين: {len(available_supervisors)}")

        return render_template('companies/areas.html',
                               company=company,
                               areas=areas,
                               available_supervisors=available_supervisors)

    except Exception as e:
        print(f"❌ خطأ في تحميل المناطق: {str(e)}")
        import traceback
        print(f"🔍 تفاصيل الخطأ: {traceback.format_exc()}")

        app.logger.error(f"Error in company_areas: {str(e)}")
        flash('حدث خطأ في تحميل المناطق', 'error')
        return redirect(url_for('companies_list'))

@app.route('/companies/<int:company_id>/areas/add', methods=['GET', 'POST'])
@login_required
def add_area(company_id):
    """إضافة منطقة جديدة - الإصدار المصحح"""
    print(f"🎯 تم استدعاء add_area للشركة {company_id} بطريقة {request.method}")

    if request.method == 'GET':
        # للتصحيح فقط
        return jsonify({
            'debug': True,
            'message': 'هذا مسار GET للتصحيح',
            'company_id': company_id,
            'endpoint': 'add_area'
        })

    # معالجة طلب POST
    try:
        print(f"📨 بيانات POST المستلمة: {dict(request.form)}")

        # التحقق من وجود الشركة
        company = Company.query.get_or_404(company_id)
        print(f"✅ الشركة: {company.name}")

        # التحقق من الصلاحيات
        if current_user.role != 'owner':
            return jsonify({
                'success': False,
                'message': 'غير مصرح بهذا الإجراء'
            }), 403

        # الحصول على البيانات
        name = request.form.get('name', '').strip()
        supervisor_id = request.form.get('supervisor_id', '').strip() or None

        print(f"📝 البيانات: name='{name}', supervisor_id='{supervisor_id}'")

        # التحقق من البيانات
        if not name:
            return jsonify({
                'success': False,
                'message': 'اسم المنطقة مطلوب'
            }), 400

        # التحقق من التكرار
        existing_area = Area.query.filter(
            Area.name.ilike(name),
            Area.company_id == company_id
        ).first()

        if existing_area:
            return jsonify({
                'success': False,
                'message': f'المنطقة "{name}" موجودة مسبقاً'
            }), 400

        # إنشاء المنطقة
        area = Area(
            name=name,
            company_id=company_id,
            supervisor_id=supervisor_id,
            is_active=True
        )

        db.session.add(area)
        db.session.commit()

        print(f"✅ تم إنشاء المنطقة: {area.name} (ID: {area.id})")

        return jsonify({
            'success': True,
            'message': 'تم إضافة المنطقة بنجاح',
            'area_id': area.id,
            'area_name': area.name
        })

    except Exception as e:
        db.session.rollback()
        print(f"❌ خطأ: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'حدث خطأ: {str(e)}'
        }), 500


@app.route('/areas/<int:area_id>/edit', methods=['POST'])
@login_required
def edit_area(area_id):
    """تعديل منطقة"""
    try:
        area = Area.query.get_or_404(area_id)

        # التحقق من الصلاحيات
        if current_user.role != 'owner':
            return jsonify({
                'success': False,
                'message': 'غير مصرح بهذا الإجراء'
            }), 403

        name = request.form.get('name', '').strip()
        supervisor_id = request.form.get('supervisor_id', '').strip() or None

        # التحقق من البيانات
        if not name:
            return jsonify({
                'success': False,
                'message': 'اسم المنطقة مطلوب'
            }), 400

        # التحقق من التكرار (استثناء المنطقة الحالية)
        existing_area = Area.query.filter(
            Area.name.ilike(name),
            Area.company_id == area.company_id,
            Area.id != area_id
        ).first()

        if existing_area:
            return jsonify({
                'success': False,
                'message': f'المنطقة "{name}" موجودة مسبقاً'
            }), 400

        # تحديث المنطقة
        area.name = name
        area.supervisor_id = supervisor_id
        area.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'تم تحديث المنطقة بنجاح',
            'area_name': area.name
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in edit_area: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء تحديث المنطقة'
        }), 500

@app.route('/areas/<int:area_id>/delete', methods=['POST'])
@login_required
def delete_area(area_id):
    """حذف منطقة - للمالك فقط"""
    # ✅ التحقق من الصلاحيات - للمالك فقط
    if current_user.role != 'owner':
        return jsonify({
            'success': False,
            'message': 'غير مصرح بهذا الإجراء - المالك فقط يمكنه الحذف'
        }), 403

    area = Area.query.get_or_404(area_id)

    try:
        # التحقق من وجود مواقع مرتبطة بالمنطقة
        has_locations = Location.query.filter_by(area_id=area_id, is_active=True).first()
        if has_locations:
            return jsonify({
                'success': False,
                'message': 'لا يمكن حذف المنطقة لأنها تحتوي على مواقع نشطة. قم بحذف المواقع أولاً.'
            }), 400

        # التحقق من وجود تقييمات مرتبطة بالمنطقة عبر الأماكن
        locations = Location.query.filter_by(area_id=area_id).all()
        location_ids = [loc.id for loc in locations]
        if location_ids:
            has_places = Place.query.filter(Place.location_id.in_(location_ids), Place.is_active == True).first()
            if has_places:
                return jsonify({
                    'success': False,
                    'message': 'لا يمكن حذف المنطقة لأنها تحتوي على أماكن نشطة. قم بحذف الأماكن أولاً.'
                }), 400

        # تعطيل المنطقة بدلاً من الحذف الفعلي
        area.is_active = False
        area.updated_at = datetime.utcnow()
        db.session.commit()

        # تسجيل العملية في السجل
        app.logger.info(f"✅ تم حذف المنطقة {area.name} بواسطة {current_user.username}")

        return jsonify({
            'success': True,
            'message': 'تم حذف المنطقة بنجاح',
            'area_id': area_id,
            'area_name': area.name
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in delete_area: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'حدث خطأ أثناء حذف المنطقة: {str(e)}'
        }), 500

# Location Management
@app.route('/areas/<int:area_id>/locations')
@login_required
def area_locations(area_id):
    """عرض مواقع منطقة محددة"""
    try:
        area = Area.query.get_or_404(area_id)

        # التحقق من الصلاحيات
        if current_user.role != 'owner' and not (
                current_user.role == 'supervisor' and
                current_user.employee_profile and
                area.supervisor_id == current_user.employee_profile.id
        ):
            flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
            return redirect(url_for('companies_list'))

        locations = Location.query.filter_by(area_id=area_id).order_by(Location.name).all()

        # الموظفون الذين يمكن تعيينهم كمراقبين
        available_monitors = Employee.query.filter_by(
            position='monitor',
            is_active=True
        ).all()

        return render_template('companies/locations.html',
                               area=area,
                               locations=locations,
                               available_monitors=available_monitors)

    except Exception as e:
        app.logger.error(f"Error in area_locations: {str(e)}")
        flash('حدث خطأ في تحميل المواقع', 'error')
        return redirect(url_for('companies_list'))


@app.route('/areas/<int:area_id>/locations/add', methods=['GET', 'POST'])
@login_required
def add_location(area_id):
    """إضافة موقع جديد"""
    print(f"🎯 تم استدعاء add_location للمنطقة {area_id} بطريقة {request.method}")

    if request.method == 'GET':
        # ✅ هذا للتصحيح فقط - لكن القالب لا يستخدمه!
        return jsonify({
            'debug': True,
            'message': 'هذا المسار يعمل بشكل صحيح',
            'area_id': area_id,
            'endpoint': 'add_location',
            'note': 'هذا API وليس صفحة HTML'
        })

    # معالجة طلب POST (يتم استدعاؤها من الـ Modal)
    try:
        print(f"📨 بيانات POST المستلمة: {dict(request.form)}")

        # التحقق من وجود المنطقة
        area = Area.query.get_or_404(area_id)

        # التحقق من الصلاحيات
        if current_user.role != 'owner' and not (
                current_user.role == 'supervisor' and
                current_user.employee_profile and
                area.supervisor_id == current_user.employee_profile.id
        ):
            return jsonify({
                'success': False,
                'message': 'غير مصرح بهذا الإجراء'
            }), 403

        # الحصول على البيانات
        name = request.form.get('name', '').strip()
        monitor_id = request.form.get('monitor_id', '').strip()

        print(f"📝 البيانات: name='{name}', monitor_id='{monitor_id}'")

        # التحقق من البيانات المطلوبة
        if not name:
            return jsonify({
                'success': False,
                'message': 'اسم الموقع مطلوب'
            }), 400

        # التحقق من عدم التكرار
        existing_location = Location.query.filter(
            db.func.lower(Location.name) == db.func.lower(name),
            Location.area_id == area_id,
            Location.is_active == True
        ).first()

        if existing_location:
            return jsonify({
                'success': False,
                'message': f'الموقع "{name}" موجود مسبقاً'
            }), 400

        # معالجة monitor_id
        final_monitor_id = None
        if monitor_id and monitor_id.isdigit():
            final_monitor_id = int(monitor_id)
            monitor = Employee.query.filter_by(
                id=final_monitor_id,
                position='monitor',
                is_active=True
            ).first()
            if not monitor:
                return jsonify({
                    'success': False,
                    'message': 'المراقب المحدد غير موجود أو غير نشط'
                }), 400

        # إنشاء الموقع
        location = Location(
            name=name,
            area_id=area_id,
            monitor_id=final_monitor_id,
            is_active=True
        )

        db.session.add(location)
        db.session.commit()

        print(f"✅ تم إنشاء الموقع بنجاح: {location.name} (ID: {location.id})")

        return jsonify({
            'success': True,
            'message': 'تم إضافة الموقع بنجاح',
            'location': {
                'id': location.id,
                'name': location.name,
                'area_id': location.area_id,
                'monitor_name': location.monitor.full_name if location.monitor else None
            }
        })

    except Exception as e:
        db.session.rollback()
        print(f"❌ خطأ في إضافة الموقع: {str(e)}")
        import traceback
        print(f"🔍 تفاصيل الخطأ: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f'حدث خطأ: {str(e)}'
        }), 500

@app.route('/locations/<int:location_id>/places')
@login_required
def location_places(location_id):
    """عرض أماكن موقع محدد"""
    try:
        location = Location.query.get_or_404(location_id)

        print(f"🔍 تحقق الصلاحيات للمستخدم {current_user.username} (دور: {current_user.role})")

        # التحقق من الصلاحيات - إصلاح حالة المالك
        has_access = False

        if current_user.role == 'owner':
            has_access = True
            print("✅ صلاحيات: مالك النظام - صلاحيات كاملة")
        elif current_user.role == 'supervisor' and current_user.employee_profile:
            if location.area.supervisor_id == current_user.employee_profile.id:
                has_access = True
                print("✅ صلاحيات: مشرف المنطقة")
            else:
                print("❌ صلاحيات: المستخدم مشرف ولكن ليس مشرف هذه المنطقة")
        elif current_user.role == 'monitor' and current_user.employee_profile:
            if location.monitor_id == current_user.employee_profile.id:
                has_access = True
                print("✅ صلاحيات: مراقب الموقع")
            else:
                print("❌ صلاحيات: المستخدم مراقب ولكن ليس مراقب هذا الموقع")
        else:
            print(f"❌ صلاحيات: لا توجد صلاحيات كافية - الدور: {current_user.role}")

        print(f"🎯 النتيجة النهائية: has_access = {has_access}")

        places = Place.query.filter_by(location_id=location_id).order_by(Place.name).all()

        # الموظفون الذين يمكن تعيينهم كعمال
        available_workers = Employee.query.filter_by(
            position='worker',
            is_active=True
        ).all()

        return render_template('companies/places.html',
                               location=location,
                               places=places,
                               available_workers=available_workers,
                               has_access=has_access)

    except Exception as e:
        app.logger.error(f"Error in location_places: {str(e)}")
        flash('حدث خطأ في تحميل الأماكن', 'error')
        return redirect(url_for('companies_list'))

@app.route('/locations/<int:location_id>/places/add', methods=['GET', 'POST'])
@login_required
def add_place(location_id):
    if request.method == 'GET':
        # ✅ إرجاع قالب إضافة المكان
        location = Location.query.get_or_404(location_id)
        available_workers = Employee.query.filter_by(position='worker', is_active=True).all()
        return render_template('companies/add_place.html',
                             location=location,
                             available_workers=available_workers)

    # معالجة طلب POST
    try:
        print(f"📨 بيانات POST المستلمة: {dict(request.form)}")

        # التحقق من وجود الموقع
        location = Location.query.get_or_404(location_id)
        print(f"✅ الموقع: {location.name} (ID: {location.id})")
        print(f"📍 المنطقة: {location.area.name}")

        # التحقق من الصلاحيات
        has_access = current_user.role == 'owner'
        if not has_access and current_user.role == 'supervisor':
            has_access = location.area.supervisor_id == current_user.employee_profile.id
        elif not has_access and current_user.role == 'monitor':
            has_access = location.monitor_id == current_user.employee_profile.id

        if not has_access:
            print(f"❌ صلاحيات غير كافية: المستخدم {current_user.username} لديه دور {current_user.role}")
            return jsonify({
                'success': False,
                'message': 'غير مصرح بهذا الإجراء'
            }), 403

        # الحصول على البيانات
        name = request.form.get('name', '').strip()
        worker_id = request.form.get('worker_id', '').strip()

        print(f"📝 البيانات: name='{name}', worker_id='{worker_id}'")

        # التحقق من البيانات المطلوبة
        if not name:
            print("❌ اسم المكان مفقود")
            return jsonify({
                'success': False,
                'message': 'اسم المكان مطلوب'
            }), 400

        # التحقق من طول الاسم
        if len(name) < 2:
            return jsonify({
                'success': False,
                'message': 'اسم المكان يجب أن يكون على الأقل حرفين'
            }), 400

        # التحقق من عدم التكرار
        existing_place = Place.query.filter(
            db.func.lower(Place.name) == db.func.lower(name),
            Place.location_id == location_id,
            Place.is_active == True
        ).first()

        if existing_place:
            print(f"❌ المكان موجود مسبقاً: {name}")
            return jsonify({
                'success': False,
                'message': f'اسم المكان "{name}" موجود مسبقاً في هذا الموقع'
            }), 400

        # معالجة worker_id
        final_worker_id = None
        if worker_id and worker_id.isdigit():
            final_worker_id = int(worker_id)
            worker = Employee.query.filter_by(
                id=final_worker_id,
                position='worker',
                is_active=True
            ).first()
            if not worker:
                return jsonify({
                    'success': False,
                    'message': 'العامل المحدد غير موجود أو غير نشط'
                }), 400

        # إنشاء المكان
        place = Place(
            name=name,
            location_id=location_id,
            worker_id=final_worker_id,
            is_active=True
        )

        db.session.add(place)
        db.session.commit()

        print(f"✅ تم إنشاء المكان بنجاح: {place.name} (ID: {place.id})")

        return jsonify({
            'success': True,
            'message': 'تم إضافة المكان بنجاح',
            'place_id': place.id,
            'place_name': place.name
        })

    except Exception as e:
        db.session.rollback()
        print(f"❌ خطأ في إضافة المكان: {str(e)}")
        import traceback
        print(f"🔍 تفاصيل الخطأ: {traceback.format_exc()}")

        return jsonify({
            'success': False,
            'message': f'حدث خطأ أثناء إضافة المكان: {str(e)}'
        }), 500


# دوال التعديل والحذف للمواقع
@app.route('/locations/<int:location_id>/edit', methods=['POST'])
@login_required
def edit_location(location_id):
    """تعديل موقع"""
    try:
        location = Location.query.get_or_404(location_id)

        # التحقق من الصلاحيات
        if current_user.role != 'owner' and not (
                current_user.role == 'supervisor' and
                current_user.employee_profile and
                location.area.supervisor_id == current_user.employee_profile.id
        ):
            return jsonify({
                'success': False,
                'message': 'غير مصرح بهذا الإجراء'
            }), 403

        name = request.form['name'].strip()
        monitor_id = request.form.get('monitor_id')

        # التحقق من البيانات
        if not name:
            return jsonify({
                'success': False,
                'message': 'اسم الموقع مطلوب'
            }), 400

        # تحديث الموقع
        location.name = name
        location.monitor_id = monitor_id if monitor_id else None
        location.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'تم تحديث الموقع بنجاح'
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in edit_location: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء تحديث الموقع'
        }), 500

@app.route('/locations/<int:location_id>/delete', methods=['POST'])
@login_required
def delete_location(location_id):
    """حذف موقع - للمالك فقط"""
    # ✅ التحقق من الصلاحيات - للمالك فقط
    if current_user.role != 'owner':
        return jsonify({
            'success': False,
            'message': 'غير مصرح بهذا الإجراء - المالك فقط يمكنه الحذف'
        }), 403

    location = Location.query.get_or_404(location_id)

    try:
        # التحقق من وجود أماكن مرتبطة بالموقع
        has_places = Place.query.filter_by(location_id=location_id, is_active=True).first()
        if has_places:
            return jsonify({
                'success': False,
                'message': 'لا يمكن حذف الموقع لأنه يحتوي على أماكن نشطة. قم بحذف الأماكن أولاً.'
            }), 400

        # التحقق من وجود تقييمات مرتبطة بالموقع
        places = Place.query.filter_by(location_id=location_id).all()
        place_ids = [p.id for p in places]
        if place_ids:
            has_evaluations = CleaningEvaluation.query.filter(CleaningEvaluation.place_id.in_(place_ids)).first()
            if has_evaluations:
                return jsonify({
                    'success': False,
                    'message': 'لا يمكن حذف الموقع لأنه يحتوي على تقييمات سابقة.'
                }), 400

        # تعطيل الموقع بدلاً من الحذف الفعلي
        location.is_active = False
        location.updated_at = datetime.utcnow()
        db.session.commit()

        # تسجيل العملية في السجل
        app.logger.info(f"✅ تم حذف الموقع {location.name} بواسطة {current_user.username}")

        return jsonify({
            'success': True,
            'message': 'تم حذف الموقع بنجاح',
            'location_id': location_id,
            'location_name': location.name
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in delete_location: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'حدث خطأ أثناء حذف الموقع: {str(e)}'
        }), 500



# دوال التعديل والحذف للأماكن
@app.route('/places/<int:place_id>/edit', methods=['POST'])
@login_required
def edit_place(place_id):
    """تعديل مكان"""
    try:
        place = Place.query.get_or_404(place_id)

        # التحقق من الصلاحيات
        has_access = current_user.role == 'owner'
        if not has_access and current_user.role == 'supervisor':
            has_access = place.location.area.supervisor_id == current_user.employee_profile.id
        elif not has_access and current_user.role == 'monitor':
            has_access = place.location.monitor_id == current_user.employee_profile.id

        if not has_access:
            return jsonify({
                'success': False,
                'message': 'غير مصرح بهذا الإجراء'
            }), 403

        name = request.form['name'].strip()
        worker_id = request.form.get('worker_id')

        # التحقق من البيانات
        if not name:
            return jsonify({
                'success': False,
                'message': 'اسم المكان مطلوب'
            }), 400

        # تحديث المكان
        place.name = name
        place.worker_id = worker_id if worker_id else None
        place.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'تم تحديث المكان بنجاح'
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in edit_place: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء تحديث المكان'
        }), 500

@app.route('/places/<int:place_id>/delete', methods=['POST'])
@login_required
def delete_place(place_id):
    """حذف مكان - للمالك فقط"""
    # ✅ التحقق من الصلاحيات - للمالك فقط
    if current_user.role != 'owner':
        return jsonify({
            'success': False,
            'message': 'غير مصرح بهذا الإجراء - المالك فقط يمكنه الحذف'
        }), 403

    place = Place.query.get_or_404(place_id)

    try:
        # التحقق من وجود تقييمات مرتبطة بالمكان
        has_evaluations = CleaningEvaluation.query.filter_by(place_id=place_id).first()
        if has_evaluations:
            return jsonify({
                'success': False,
                'message': 'لا يمكن حذف المكان لأنه يحتوي على تقييمات سابقة.'
            }), 400

        # تعطيل المكان بدلاً من الحذف الفعلي
        place.is_active = False
        place.updated_at = datetime.utcnow()
        db.session.commit()

        # تسجيل العملية في السجل
        app.logger.info(f"✅ تم حذف المكان {place.name} بواسطة {current_user.username}")

        return jsonify({
            'success': True,
            'message': 'تم حذف المكان بنجاح',
            'place_id': place_id,
            'place_name': place.name
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in delete_place: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'حدث خطأ أثناء حذف المكان: {str(e)}'
        }), 500

@app.route('/check-data')
@login_required
def check_data():
    """فحص سريع للبيانات"""
    if current_user.role != 'owner':
        return "غير مصرح", 403

    data = {
        'companies_count': Company.query.count(),
        'areas_count': Area.query.count(),
        'locations_count': Location.query.count(),
        'places_count': Place.query.count(),
        'places_list': Place.query.all()
    }

    return f"""
        <h1>فحص البيانات</h1>
        <ul>
            <li>الشركات: {data['companies_count']}</li>
            <li>المناطق: {data['areas_count']}</li>
            <li>المواقع: {data['locations_count']}</li>
            <li>الأماكن: {data['places_count']}</li>
        </ul>
        <h2>قائمة الأماكن:</h2>
        <ul>
            {"".join([f"<li>{place.name} (نشط: {place.is_active})</li>" for place in data['places_list']])}
        </ul>
        <a href="/quick-fix-places" class="btn btn-primary">إنشاء أماكن تجريبية</a>
        """

@app.route('/quick-fix-places')
@login_required
def quick_fix_places():
    """إنشاء أماكن تجريبية فورية"""
    if current_user.role != 'owner':
        flash('غير مصرح', 'error')
        return redirect(url_for('dashboard'))

    try:
        # البحث عن شركة موجودة أو إنشاء واحدة
        company = Company.query.first()
        if not company:
            company = Company(
                name='شركة النظافة',
                address='عنوان افتراضي',
                is_active=True
            )
            db.session.add(company)
            db.session.flush()

        # البحث عن منطقة موجودة أو إنشاء واحدة
        area = Area.query.first()
        if not area:
            area = Area(
                name='المنطقة الرئيسية',
                company_id=company.id,
                is_active=True
            )
            db.session.add(area)
            db.session.flush()

        # البحث عن موقع موجود أو إنشاء واحد
        location = Location.query.first()
        if not location:
            location = Location(
                name='المبنى الإداري',
                area_id=area.id,
                is_active=True
            )
            db.session.add(location)
            db.session.flush()

        # إنشاء أماكن تجريبية
        sample_places = [
            'المكتب الرئيسي',
            'قاعة الاجتماعات',
            'المطبخ',
            'دورات المياه',
            'الممرات',
            'المدخل الرئيسي'
        ]

        created_count = 0
        for place_name in sample_places:
            existing_place = Place.query.filter_by(name=place_name).first()
            if not existing_place:
                place = Place(
                    name=place_name,
                    location_id=location.id,
                    is_active=True
                )
                db.session.add(place)
                created_count += 1

        db.session.commit()

        if created_count > 0:
            flash(f'تم إنشاء {created_count} مكان بنجاح', 'success')
        else:
            flash('جميع الأماكن موجودة مسبقاً', 'info')

        return redirect(url_for('add_evaluation'))

    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في إنشاء الأماكن: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

    # ... (تنفيذ مشابه)
@app.route('/api/evaluation/structure')
@login_required
def get_evaluation_structure():
    """API للحصول على الهيكل المتسلسل للخيارات"""
    try:
        structure = {
            'companies': []
        }

        companies = Company.query.filter_by(is_active=True).all()
        for company in companies:
            company_data = {
                'id': company.id,
                'name': company.name,
                'areas': []
            }

            areas = Area.query.filter_by(company_id=company.id, is_active=True).all()
            for area in areas:
                area_data = {
                    'id': area.id,
                    'name': area.name,
                    'locations': []
                }

                locations = Location.query.filter_by(area_id=area.id, is_active=True).all()
                for location in locations:
                    location_data = {
                        'id': location.id,
                        'name': location.name,
                        'places': []
                    }

                    places = Place.query.filter_by(location_id=location.id, is_active=True).all()
                    for place in places:
                        place_data = {
                            'id': place.id,
                            'name': place.name
                        }
                        location_data['places'].append(place_data)

                    area_data['locations'].append(location_data)

                company_data['areas'].append(area_data)

            structure['companies'].append(company_data)

        return jsonify({
            'success': True,
            'data': structure
        })

    except Exception as e:
        app.logger.error(f"Error in get_evaluation_structure: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ في تحميل الهيكل التنظيمي'
        }), 500



def get_employee_current_assignment(employee_id):
    """دالة مساعدة للحصول على المهمة الحالية للموظف"""
    # يمكن تطوير هذه الدالة لتعيد المهمة الحالية للموظف
    return "غير محدد"


# Evaluation Management with Updated Permissions

@app.route('/evaluations')
@login_required
def evaluations_list():
    if not check_permission('can_view_evaluations'):
        flash('غير مصرح بعرض التقييمات', 'error')
        return redirect(url_for('dashboard'))
    """عرض قائمة التقييمات مع الصلاحيات المحسنة (باستخدام الدالة المساعدة)"""
    try:
        # استخدام الدالة المركزية للحصول على التقييمات المفلترة
        evaluations_list = get_filtered_evaluations(current_user)
        app.logger.info(f"✅ تم تحميل {len(evaluations_list)} تقييم للمستخدم {current_user.username}")

        return render_template('evaluations/list.html',
                               evaluations=evaluations_list,
                               today=date.today(),
                               current_user=current_user)

    except Exception as e:
        app.logger.error(f"❌ Error in evaluations_list: {str(e)}")
        import traceback
        app.logger.error(f"🔍 تفاصيل الخطأ: {traceback.format_exc()}")
        flash('حدث خطأ في تحميل قائمة التقييمات', 'error')
        return render_template('evaluations/list.html', evaluations=[], today=date.today(), current_user=current_user)


@app.route('/evaluations/add', methods=['GET', 'POST'])
@login_required
def add_evaluation():
    """إضافة تقييم جديد مع نظام الصلاحيات المحسن ومنع التقييم المكرر"""

    # التحقق من الصلاحيات الأساسية
    if current_user.role not in ['owner', 'supervisor', 'monitor']:
        flash('غير مصرح بإضافة تقييمات', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            # ========== طباعة جميع البيانات المستلمة للتصحيح ==========
            print("\n" + "=" * 70)
            print("🔍 جميع البيانات المستلمة من النموذج:")
            for key, value in request.form.items():
                print(f"   {key}: '{value}'")
            print("=" * 70 + "\n")

            # ========== الحصول على جميع البيانات ==========
            # التاريخ
            date_str = request.form.get('date', '')

            # بيانات الهيكل التنظيمي
            company_id = request.form.get('company_id', '')
            area_id = request.form.get('area_id', '')
            location_id = request.form.get('location_id', '')
            place_id = request.form.get('place_id', '')

            # الموظف المقيّم
            evaluated_employee_id = request.form.get('evaluated_employee_id', '')

            # حقول التقييم
            cleanliness = request.form.get('cleanliness', '')
            organization = request.form.get('organization', '')
            equipment_condition = request.form.get('equipment_condition', '')
            time_value = request.form.get('time', '')
            safety_measures = request.form.get('safety_measures', '')
            comments = request.form.get('comments', '')

            # المقيم
            evaluator_id = None

            # ========== التحقق من الحقول المطلوبة الأساسية فقط ==========
            missing_fields = []

            if not date_str:
                missing_fields.append('التاريخ')
            if not company_id:
                missing_fields.append('الشركة')
            if not evaluated_employee_id:
                missing_fields.append('الموظف المقيّم')
            if not cleanliness:
                missing_fields.append('النظافة')
            if not organization:
                missing_fields.append('التنظيم')
            if not equipment_condition:
                missing_fields.append('المعدات')
            if not time_value:
                missing_fields.append('الوقت')
            if not safety_measures:
                missing_fields.append('السلامة')

            # المنطقة والموقع والمكان اختيارية الآن
            if missing_fields:
                error_message = f'يرجى ملء جميع الحقول المطلوبة. الحقول المفقودة: {", ".join(missing_fields)}'
                print(f"❌ {error_message}")
                flash(error_message, 'error')
                return redirect(url_for('add_evaluation'))

            print("✅ جميع الحقول المطلوبة الأساسية موجودة")

            # ========== تحويل التاريخ ==========
            try:
                evaluation_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('صيغة التاريخ غير صحيحة', 'error')
                return redirect(url_for('add_evaluation'))

            if evaluation_date > date.today():
                flash('لا يمكن إضافة تقييم لتاريخ مستقبلي', 'error')
                return redirect(url_for('add_evaluation'))

            # ========== تحديد المقيم ==========
            if current_user.role == 'owner':
                # للمالك: يمكنه اختيار المقيم من القائمة
                evaluator_id = request.form.get('evaluator_id')
                if not evaluator_id:
                    # استخدام أول مشرف نشط كمقيم افتراضي
                    supervisor = Employee.query.filter_by(position='supervisor', is_active=True).first()
                    if supervisor:
                        evaluator_id = supervisor.id
                        app.logger.info(f"👑 المالك يستخدم المشرف: {supervisor.full_name}")
                    else:
                        flash('لا يوجد مشرفين في النظام', 'error')
                        return redirect(url_for('add_evaluation'))
            else:
                # للمشرفين والمراقبين: استخدام حسابهم كمقيم
                employee_profile = Employee.query.filter_by(user_id=current_user.id).first()
                if employee_profile:
                    evaluator_id = employee_profile.id
                    app.logger.info(f"👤 المستخدم يستخدم حسابه: {employee_profile.full_name}")
                else:
                    flash('لا يوجد ملف شخصي للموظف مرتبط بحسابك', 'error')
                    return redirect(url_for('add_evaluation'))

            if not evaluator_id:
                flash('لا يمكن تحديد المقيم، يرجى التحقق من بيانات الموظفين', 'error')
                return redirect(url_for('add_evaluation'))

            # ========== التحقق من صحة البيانات الأساسية ==========
            try:
                company_id = int(company_id)
                evaluated_employee_id = int(evaluated_employee_id)
                evaluator_id = int(evaluator_id)

                # تحويل القيم الاختيارية إلى int إذا كانت موجودة
                if area_id and area_id.isdigit():
                    area_id = int(area_id)
                else:
                    area_id = None

                if location_id and location_id.isdigit():
                    location_id = int(location_id)
                else:
                    location_id = None

                if place_id and place_id.isdigit():
                    place_id = int(place_id)
                else:
                    place_id = None

            except ValueError:
                flash('معرفات غير صحيحة', 'error')
                return redirect(url_for('add_evaluation'))

            # التحقق من وجود الشركة
            company = Company.query.get(company_id)
            if not company:
                flash('الشركة المحددة غير موجودة', 'error')
                return redirect(url_for('add_evaluation'))

            # التحقق من وجود المنطقة إذا تم تحديدها
            if area_id:
                area = Area.query.filter_by(id=area_id, company_id=company_id).first()
                if not area:
                    flash('المنطقة المحددة غير موجودة أو لا تتبع هذه الشركة', 'error')
                    return redirect(url_for('add_evaluation'))

            # التحقق من وجود الموقع إذا تم تحديده
            if location_id:
                location = Location.query.filter_by(id=location_id).first()
                if not location:
                    flash('الموقع المحدد غير موجود', 'error')
                    return redirect(url_for('add_evaluation'))
                if area_id and location.area_id != area_id:
                    flash('الموقع المحدد لا يتبع هذه المنطقة', 'error')
                    return redirect(url_for('add_evaluation'))

            # التحقق من وجود المكان إذا تم تحديده
            if place_id:
                place = Place.query.filter_by(id=place_id).first()
                if not place:
                    flash('المكان المحدد غير موجود', 'error')
                    return redirect(url_for('add_evaluation'))
                if location_id and place.location_id != location_id:
                    flash('المكان المحدد لا يتبع هذا الموقع', 'error')
                    return redirect(url_for('add_evaluation'))

            # التحقق من وجود الموظف المقيّم
            evaluated_employee = Employee.query.get(evaluated_employee_id)
            if not evaluated_employee:
                flash('الموظف المحدد غير موجود', 'error')
                return redirect(url_for('add_evaluation'))

            # التحقق من وجود المقيم
            evaluator = Employee.query.get(evaluator_id)
            if not evaluator:
                flash('المقيم المحدد غير موجود', 'error')
                return redirect(url_for('add_evaluation'))

            # ========== التحقق من الصلاحيات ==========
            # إنشاء كائن place مؤقت للتحقق من الصلاحية
            temp_place = None
            if place_id:
                temp_place = Place.query.get(place_id)

            if not can_evaluate_employee(current_user, evaluated_employee, temp_place):
                flash('غير مصرح بتقييم هذا الموظف', 'error')
                return redirect(url_for('add_evaluation'))

            # ========== ✅ التحقق 1: منع تقييم الموظف غير المداوم ==========
            # التحقق من وجود سجل حضور للموظف في هذا التاريخ
            attendance_record = Attendance.query.filter_by(
                employee_id=evaluated_employee_id,
                date=evaluation_date
            ).first()

            # إذا كان الموظف ليس له سجل حضور
            if not attendance_record:
                flash('❌ لا يمكن تقييم هذا الموظف لأنه ليس لديه سجل حضور في هذا التاريخ', 'error')
                return redirect(url_for('add_evaluation'))

            # إذا كان الموظف غائباً
            if attendance_record.status == 'absent':
                flash('❌ لا يمكن تقييم موظف غائب في هذا التاريخ', 'error')
                return redirect(url_for('add_evaluation'))

            # إذا كان الموظف متأخراً، يمكن تقييمه مع تحذير
            if attendance_record.status == 'late':
                flash('⚠️ الموظف متأخر في هذا اليوم، ولكن يمكن تقييمه', 'warning')

            # ========== ✅ التحقق 2: منع تكرار تقييم الموظف في نفس اليوم ==========
            # التحقق من وجود تقييم سابق لنفس الموظف في نفس التاريخ
            existing_evaluation = CleaningEvaluation.query.filter_by(
                evaluated_employee_id=evaluated_employee_id,
                date=evaluation_date
            ).first()

            if existing_evaluation:
                # الحصول على اسم المقيم السابق
                previous_evaluator = Employee.query.get(existing_evaluation.evaluator_id)
                evaluator_name = previous_evaluator.full_name if previous_evaluator else 'غير معروف'

                flash(
                    f'❌ لا يمكن إضافة تقييم مكرر. الموظف لديه تقييم بالفعل في هذا التاريخ (تم إضافته بواسطة {evaluator_name})',
                    'error')
                return redirect(url_for('add_evaluation'))

            # ========== تحويل قيم التقييم ==========
            try:
                cleanliness = int(cleanliness)
                organization = int(organization)
                equipment_condition = int(equipment_condition)
                time_value = int(time_value)
                safety_measures = int(safety_measures)

                # التحقق من النطاق
                if not (1 <= cleanliness <= 5):
                    flash('قيمة النظافة يجب أن تكون بين 1 و 5', 'error')
                    return redirect(url_for('add_evaluation'))
                if not (1 <= organization <= 5):
                    flash('قيمة التنظيم يجب أن تكون بين 1 و 5', 'error')
                    return redirect(url_for('add_evaluation'))
                if not (1 <= equipment_condition <= 5):
                    flash('قيمة المعدات يجب أن تكون بين 1 و 5', 'error')
                    return redirect(url_for('add_evaluation'))
                if not (1 <= time_value <= 5):
                    flash('قيمة الوقت يجب أن تكون بين 1 و 5', 'error')
                    return redirect(url_for('add_evaluation'))
                if not (1 <= safety_measures <= 5):
                    flash('قيمة السلامة يجب أن تكون بين 1 و 5', 'error')
                    return redirect(url_for('add_evaluation'))

            except ValueError:
                flash('قيم التقييم غير صحيحة، يرجى التأكد من إدخال أرقام صحيحة', 'error')
                return redirect(url_for('add_evaluation'))

            # ========== إنشاء التقييم ==========
            evaluation = CleaningEvaluation(
                date=evaluation_date,
                place_id=place_id,  # يمكن أن يكون None
                evaluated_employee_id=evaluated_employee_id,
                evaluator_id=evaluator_id,
                cleanliness=cleanliness,
                organization=organization,
                equipment_condition=equipment_condition,
                time=time_value,
                safety_measures=safety_measures,
                overall_score=0.0,
                comments=comments or None
            )

            # حساب النتيجة الإجمالية
            evaluation.calculate_overall_score()

            db.session.add(evaluation)
            db.session.commit()

            flash('✅ تم إضافة التقييم بنجاح!', 'success')
            return redirect(url_for('evaluations_list'))

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"❌ خطأ في إضافة التقييم: {str(e)}")
            import traceback
            app.logger.error(f"🔍 تفاصيل الخطأ: {traceback.format_exc()}")
            flash(f'حدث خطأ: {str(e)}', 'error')
            return redirect(url_for('add_evaluation'))

    # ========== GET Request - عرض النموذج ==========
    try:
        # ✅ فلترة الشركات حسب دور المستخدم
        if current_user.role == 'owner':
            # المالك: يرى جميع الشركات النشطة
            companies = Company.query.filter_by(is_active=True).order_by(Company.name).all()
            app.logger.info(f"👑 المالك يرى جميع الشركات: {len(companies)} شركة")

        elif current_user.role == 'supervisor' and current_user.employee_profile:
            # المشرف: يرى فقط الشركة التي يعمل بها
            supervisor_employee = current_user.employee_profile
            if supervisor_employee.company_id:
                companies = Company.query.filter_by(
                    id=supervisor_employee.company_id,
                    is_active=True
                ).all()
                app.logger.info(
                    f"👤 المشرف يرى شركته فقط: {supervisor_employee.company.name if supervisor_employee.company else 'غير معينة'}")
            else:
                companies = []
                app.logger.warning("⚠️ المشرف ليس لديه شركة محددة")

        elif current_user.role == 'monitor' and current_user.employee_profile:
            # المراقب: يرى الشركة المرتبطة بموقعه
            monitor_employee = current_user.employee_profile
            # البحث عن موقع المراقب
            monitor_location = Location.query.filter_by(monitor_id=monitor_employee.id).first()
            if monitor_location and monitor_location.area and monitor_location.area.company:
                companies = [monitor_location.area.company]
                app.logger.info(f"👁️ المراقب يرى شركة: {monitor_location.area.company.name}")
            else:
                companies = []
                app.logger.warning("⚠️ المراقب ليس له موقع محدد")
        else:
            companies = []

        # ✅ الحصول على الموظفين المسموح للمستخدم بتقييمهم
        employees_for_evaluation = get_employees_for_evaluation(current_user)

        # ✅ المقيمون (للمالك فقط)
        evaluators = []
        supervisors = []

        if current_user.role == 'owner':
            evaluators = Employee.query.filter(
                Employee.position.in_(['supervisor', 'monitor']),
                Employee.is_active == True
            ).order_by(Employee.full_name).all()

            supervisors = Employee.query.filter_by(
                position='supervisor',
                is_active=True
            ).order_by(Employee.full_name).all()

        return render_template('evaluations/add.html',
                               today=date.today(),
                               companies=companies,
                               employees=employees_for_evaluation,
                               evaluators=evaluators,
                               supervisors=supervisors,
                               current_user=current_user,
                               user_role=current_user.role)

    except Exception as e:
        app.logger.error(f"❌ خطأ في تحميل النموذج: {str(e)}")
        import traceback
        app.logger.error(f"🔍 تفاصيل الخطأ: {traceback.format_exc()}")
        flash(f'خطأ في تحميل النموذج: {str(e)}', 'error')
        return redirect(url_for('evaluations_list'))


@app.route('/test-evaluation-form')
def test_evaluation_form():
    """صفحة اختبار لنموذج التقييم"""
    return render_template('evaluations/test_form.html')


@app.route('/financial/deductions')
@login_required
def deductions_dashboard():
    """لوحة موحدة للخصومات والإضافات (السلف، الجزاءات، الساعات الإضافية)"""
    if current_user.role != 'owner':
        flash('غير مصرح', 'error')
        return redirect(url_for('dashboard'))

    try:
        from models import EmployeeLoan, Penalty, Overtime

        # الحصول على معاملات الفلترة
        employee_id = request.args.get('employee_id', type=int)
        from_date = request.args.get('from_date', '')
        to_date = request.args.get('to_date', '')

        # بناء استعلامات مع الفلترة
        loan_query = EmployeeLoan.query
        penalty_query = Penalty.query
        overtime_query = Overtime.query

        if employee_id:
            loan_query = loan_query.filter_by(employee_id=employee_id)
            penalty_query = penalty_query.filter_by(employee_id=employee_id)
            overtime_query = overtime_query.filter_by(employee_id=employee_id)

        if from_date:
            try:
                from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
                loan_query = loan_query.filter(EmployeeLoan.loan_date >= from_date_obj)
                penalty_query = penalty_query.filter(Penalty.penalty_date >= from_date_obj)
                overtime_query = overtime_query.filter(Overtime.overtime_date >= from_date_obj)
            except:
                pass

        if to_date:
            try:
                to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
                loan_query = loan_query.filter(EmployeeLoan.loan_date <= to_date_obj)
                penalty_query = penalty_query.filter(Penalty.penalty_date <= to_date_obj)
                overtime_query = overtime_query.filter(Overtime.overtime_date <= to_date_obj)
            except:
                pass

        # تنفيذ الاستعلامات
        loans = loan_query.order_by(EmployeeLoan.loan_date.desc()).all()
        penalties = penalty_query.order_by(Penalty.penalty_date.desc()).all()
        overtimes = overtime_query.order_by(Overtime.overtime_date.desc()).all()

        # إحصائيات السلف
        loan_stats = {
            'total': sum(l.amount for l in loans),
            'paid': sum(l.paid_amount for l in loans),
            'remaining': sum(l.remaining for l in loans),
            'active': len([l for l in loans if l.status == 'active']),
            'payment_rate': round((sum(l.paid_amount for l in loans) / sum(l.amount for l in loans) * 100), 1) if loans else 0
        }

        # إحصائيات الجزاءات
        penalty_stats = {
            'total': sum(p.amount for p in penalties),
            'transferred': sum(p.amount for p in penalties if p.is_deducted),
            'pending': sum(p.amount for p in penalties if not p.is_deducted),
            'transferred_count': len([p for p in penalties if p.is_deducted]),
            'pending_count': len([p for p in penalties if not p.is_deducted]),
            'transferred_rate': round((sum(p.amount for p in penalties if p.is_deducted) / sum(p.amount for p in penalties) * 100), 1) if penalties else 0
        }

        # إحصائيات الساعات الإضافية
        overtime_stats = {
            'total_hours': sum(o.hours for o in overtimes),
            'total_cost': sum(o.cost for o in overtimes),
            'transferred_hours': sum(o.hours for o in overtimes if o.is_transferred),
            'transferred_cost': sum(o.cost for o in overtimes if o.is_transferred),
            'pending_hours': sum(o.hours for o in overtimes if not o.is_transferred),
            'pending_cost': sum(o.cost for o in overtimes if not o.is_transferred),
            'transferred_rate': round((sum(o.cost for o in overtimes if o.is_transferred) / sum(o.cost for o in overtimes) * 100), 1) if overtimes else 0
        }

        # صافي التأثير على المرتبات
        net_impact = overtime_stats['total_cost'] - (loan_stats['remaining'] + penalty_stats['pending'])

        # قائمة الموظفين للفلترة
        employees = Employee.query.filter_by(is_active=True).order_by(Employee.full_name).all()

        return render_template('financial/deductions_dashboard.html',
                               loans=loans,
                               penalties=penalties,
                               overtimes=overtimes,
                               employees=employees,
                               loan_stats=loan_stats,
                               penalty_stats=penalty_stats,
                               overtime_stats=overtime_stats,
                               net_impact=net_impact,
                               today=date.today())

    except Exception as e:
        app.logger.error(f"Error in deductions_dashboard: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        flash(f'حدث خطأ: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

# ============================================
# ✅ دوال إدارة السلف (Employee Loans)
# ============================================

@app.route('/loans')
@login_required
def loans_list():
    """عرض قائمة السلف والاقتراض"""
    if current_user.role != 'owner':
        flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))

    try:
        # استيراد نموذج السلف
        from models import EmployeeLoan, LoanInstallment

        # الحصول على معاملات الفلترة
        employee_id = request.args.get('employee_id', type=int)
        status = request.args.get('status', '')
        from_date = request.args.get('from_date', '')
        to_date = request.args.get('to_date', '')

        # بناء الاستعلام
        query = EmployeeLoan.query

        if employee_id:
            query = query.filter_by(employee_id=employee_id)

        if status:
            query = query.filter_by(status=status)

        if from_date:
            try:
                from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
                query = query.filter(EmployeeLoan.loan_date >= from_date_obj)
            except:
                pass

        if to_date:
            try:
                to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
                query = query.filter(EmployeeLoan.loan_date <= to_date_obj)
            except:
                pass

        # تنفيذ الاستعلام
        loans = query.order_by(EmployeeLoan.loan_date.desc()).all()

        # إحصائيات
        total_loans = sum(l.amount for l in loans)
        total_paid = sum(l.paid_amount for l in loans)
        total_remaining = sum(l.remaining for l in loans)
        active_loans = len([l for l in loans if l.status == 'active'])
        paid_loans = len([l for l in loans if l.status == 'paid'])

        # قائمة الموظفين للفلترة
        employees = Employee.query.filter_by(is_active=True).order_by(Employee.full_name).all()

        return render_template('financial/employee_loans.html',
                               loans=loans,
                               employees=employees,
                               selected_employee=employee_id,
                               selected_status=status,
                               from_date=from_date,
                               to_date=to_date,
                               total_loans=total_loans,
                               total_paid=total_paid,
                               total_remaining=total_remaining,
                               active_loans=active_loans,
                               paid_loans=paid_loans,
                               today=date.today())

    except Exception as e:
        app.logger.error(f"Error in loans_list: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        flash(f'حدث خطأ: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/loans/add', methods=['POST'])
@login_required
def add_loan():
    """إضافة سلفة جديدة"""
    if current_user.role != 'owner':
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403

    try:
        from models import EmployeeLoan

        # الحصول على البيانات من النموذج
        employee_id = request.form.get('employee_id')
        loan_date = request.form.get('loan_date')
        amount = request.form.get('amount')
        installments = request.form.get('installments', 1)
        reason = request.form.get('reason', '')
        description = request.form.get('description', '')

        # التحقق من البيانات المطلوبة
        if not all([employee_id, loan_date, amount]):
            return jsonify({
                'success': False,
                'message': 'الرجاء ملء جميع الحقول المطلوبة'
            }), 400

        # تحويل التاريخ
        try:
            loan_date_obj = datetime.strptime(loan_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'صيغة التاريخ غير صحيحة'
            }), 400

        # التحقق من وجود الموظف
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({
                'success': False,
                'message': 'الموظف غير موجود'
            }), 404

        # تحويل المبلغ وعدد الأقساط
        amount_float = float(amount)
        installments_int = int(installments)

        # حساب القسط الشهري
        monthly_installment = amount_float / installments_int if installments_int > 0 else amount_float

        # إنشاء السلفة ✅ مع تهيئة جميع القيم
        loan = EmployeeLoan(
            employee_id=int(employee_id),
            loan_date=loan_date_obj,
            amount=amount_float,
            installments=installments_int,
            monthly_installment=round(monthly_installment, 2),
            paid_amount=0.0,  # ✅ تهيئة بـ 0
            remaining=amount_float,  # ✅ المتبقي = المبلغ الكامل
            reason=reason,
            description=description,
            recorded_by=current_user.id,
            status='active'
        )

        db.session.add(loan)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '✅ تم إضافة السلفة بنجاح',
            'loan_id': loan.id,
            'monthly_installment': loan.monthly_installment
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in add_loan: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'حدث خطأ: {str(e)}'
        }), 500

@app.route('/loans/pay-installment', methods=['POST'])
@login_required
def pay_loan_installment():
    """تسديد قسط شهري من السلفة"""
    if current_user.role != 'owner':
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403

    try:
        from models import EmployeeLoan, LoanInstallment

        data = request.get_json()
        loan_id = data.get('loan_id')
        amount = data.get('amount')
        payment_date = data.get('payment_date', date.today().isoformat())
        payment_method = data.get('payment_method', 'payroll')

        # التحقق من البيانات
        if not loan_id or not amount:
            return jsonify({
                'success': False,
                'message': 'معرف السلفة والمبلغ مطلوبان'
            }), 400

        # الحصول على السلفة
        loan = EmployeeLoan.query.get_or_404(loan_id)

        if loan.status == 'paid':
            return jsonify({
                'success': False,
                'message': 'هذه السلفة مسددة بالكامل'
            }), 400

        # تحويل التاريخ
        try:
            payment_date_obj = datetime.strptime(payment_date, '%Y-%m-%d').date()
        except ValueError:
            payment_date_obj = date.today()

        # تسجيل القسط
        installment = LoanInstallment(
            loan_id=loan.id,
            payment_date=payment_date_obj,
            amount=float(amount),
            month=payment_date_obj.month,
            year=payment_date_obj.year,
            payment_method=payment_method
        )

        # تحديث السلفة
        loan.paid_amount += float(amount)
        loan.remaining = loan.amount - loan.paid_amount

        if loan.remaining <= 0:
            loan.status = 'paid'

        db.session.add(installment)
        db.session.commit()

        # تحديث كشف الراتب إذا كانت طريقة الدفع من الراتب
        if payment_method == 'payroll':
            update_payroll_with_loan_deduction(loan.employee_id, payment_date_obj.year, payment_date_obj.month, float(amount))

        return jsonify({
            'success': True,
            'message': '✅ تم تسديد القسط بنجاح',
            'remaining': loan.remaining,
            'paid_amount': loan.paid_amount,
            'status': loan.status
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in pay_loan_installment: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'حدث خطأ: {str(e)}'
        }), 500


@app.route('/loans/<int:loan_id>')
@login_required
def get_loan_details(loan_id):
    """الحصول على تفاصيل سلفة محددة"""
    if current_user.role != 'owner':
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403

    try:
        from models import EmployeeLoan, LoanInstallment
        from sqlalchemy.orm import joinedload

        loan = EmployeeLoan.query.options(
            joinedload(EmployeeLoan.employee),
            joinedload(EmployeeLoan.installments)
        ).get_or_404(loan_id)

        # الحصول على الأقساط المسددة
        installments = LoanInstallment.query.filter_by(loan_id=loan_id).order_by(LoanInstallment.payment_date.desc()).all()

        installments_data = [{
            'id': inst.id,
            'payment_date': inst.payment_date.strftime('%Y-%m-%d'),
            'amount': inst.amount,
            'month': inst.month,
            'year': inst.year,
            'payment_method': inst.payment_method
        } for inst in installments]

        loan_data = {
            'id': loan.id,
            'employee_id': loan.employee_id,
            'employee_name': loan.employee.full_name if loan.employee else 'غير معروف',
            'loan_date': loan.loan_date.strftime('%Y-%m-%d'),
            'amount': loan.amount,
            'installments': loan.installments,
            'monthly_installment': loan.monthly_installment,
            'paid_amount': loan.paid_amount,
            'remaining': loan.remaining,
            'status': loan.status,
            'status_ar': 'نشط' if loan.status == 'active' else 'مسدد' if loan.status == 'paid' else 'ملغي',
            'reason': loan.reason or '',
            'description': loan.description or '',
            'installments_list': installments_data
        }

        return jsonify({
            'success': True,
            'data': loan_data
        })

    except Exception as e:
        app.logger.error(f"Error in get_loan_details: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'حدث خطأ: {str(e)}'
        }), 500


@app.route('/loans/delete/<int:loan_id>', methods=['POST'])
@login_required
def delete_loan(loan_id):
    """حذف سلفة (مع الأقساط المرتبطة بها)"""
    if current_user.role != 'owner':
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403

    try:
        from models import EmployeeLoan, LoanInstallment

        loan = EmployeeLoan.query.get_or_404(loan_id)

        # حذف الأقساط أولاً
        LoanInstallment.query.filter_by(loan_id=loan_id).delete()

        # حذف السلفة
        db.session.delete(loan)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '✅ تم حذف السلفة بنجاح'
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in delete_loan: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'حدث خطأ: {str(e)}'
        }), 500

@app.route('/loans/transfer-to-payroll', methods=['POST'])
@login_required
def transfer_loans_to_payroll():
    """ترحيل السلف إلى كشف المرتبات - مع تحديث الإغلاق الشهري"""
    if current_user.role != 'owner':
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403

    try:
        from models import EmployeeLoan, LoanInstallment, Payroll

        data = request.get_json()
        loan_ids = data.get('loan_ids', [])
        transfer_all = data.get('transfer_all', False)
        month = data.get('month', date.today().month)
        year = data.get('year', date.today().year)

        # الحصول على السلف المطلوبة
        if transfer_all:
            loans = EmployeeLoan.query.filter(
                EmployeeLoan.status == 'active',
                EmployeeLoan.remaining > 0
            ).all()
        else:
            if not loan_ids:
                return jsonify({'success': False, 'message': 'لم يتم تحديد أي سلف للترحيل'}), 400
            loans = EmployeeLoan.query.filter(EmployeeLoan.id.in_(loan_ids)).all()

        if not loans:
            return jsonify({'success': False, 'message': 'لا توجد سلف نشطة للترحيل'}), 400

        transferred_count = 0
        total_deducted = 0
        affected_months = set()

        for loan in loans:
            # حساب قيمة القسط لهذا الشهر
            deduction_amount = min(loan.monthly_installment, loan.remaining)

            # البحث عن كشف الراتب
            payroll = Payroll.query.filter_by(
                employee_id=loan.employee_id,
                year=year,
                month=month
            ).first()

            if payroll:
                # تحديث كشف الراتب الموجود
                current_loan = payroll.loan_deduction or 0
                payroll.loan_deduction = current_loan + deduction_amount
                payroll.calculate_payroll()
            else:
                # إنشاء كشف راتب جديد
                employee = Employee.query.get(loan.employee_id)
                if not employee:
                    continue

                payroll = Payroll(
                    employee_id=employee.id,
                    year=year,
                    month=month,
                    base_salary=employee.salary or 0,
                    loan_deduction=deduction_amount,
                    status='pending'
                )
                payroll.calculate_payroll()
                db.session.add(payroll)
                db.session.flush()

            # تسجيل القسط
            installment = LoanInstallment(
                loan_id=loan.id,
                payment_date=date.today(),
                amount=deduction_amount,
                month=month,
                year=year,
                payment_method='payroll',
                payroll_id=payroll.id,
                notes='ترحيل تلقائي إلى كشف الراتب'
            )
            db.session.add(installment)

            # تحديث السلفة
            loan.paid_amount += deduction_amount
            loan.remaining = loan.amount - loan.paid_amount
            if loan.remaining <= 0:
                loan.status = 'paid'

            transferred_count += 1
            total_deducted += deduction_amount
            affected_months.add((year, month))

        db.session.commit()

        # ✅ تحديث الإغلاق الشهري لكل شهر تأثر
        for y, m in affected_months:
            trigger_monthly_closing_update(y, m)

        return jsonify({
            'success': True,
            'message': f'✅ تم ترحيل {transferred_count} سلفة بنجاح (إجمالي الخصم: {total_deducted:,.2f} ريال)',
            'transferred_count': transferred_count,
            'total_deducted': total_deducted
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in transfer_loans_to_payroll: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'حدث خطأ: {str(e)}'
        }), 500

# ============================================
# ✅ دوال إدارة الساعات الإضافية (Overtime)
# ============================================
@app.route('/overtime')
@login_required
def overtime_list():
    """عرض قائمة الساعات الإضافية"""
    if not check_permission('can_view_overtime'):
        flash('غير مصرح', 'error')
        return redirect(url_for('reports_index'))

    try:
        from models import Overtime

        # الحصول على معاملات الفلترة
        employee_id = request.args.get('employee_id', type=int)
        from_date_str = request.args.get('from_date', '')
        to_date_str = request.args.get('to_date', '')
        status = request.args.get('status', '')

        # تحويل النصوص إلى كائنات تاريخ
        from_date = None
        to_date = None

        if from_date_str:
            try:
                from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            except:
                from_date = None

        if to_date_str:
            try:
                to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
            except:
                to_date = None

        # بناء الاستعلام
        query = Overtime.query

        if employee_id:
            query = query.filter_by(employee_id=employee_id)

        if from_date:
            query = query.filter(Overtime.overtime_date >= from_date)

        if to_date:
            query = query.filter(Overtime.overtime_date <= to_date)

        if status == 'transferred':
            query = query.filter_by(is_transferred=True)
        elif status == 'pending':
            query = query.filter_by(is_transferred=False)

        # تنفيذ الاستعلام
        overtime_records = query.order_by(Overtime.overtime_date.desc()).all()

        # إحصائيات
        total_hours = sum(r.hours for r in overtime_records)
        total_cost = sum(r.cost for r in overtime_records)
        transferred_hours = sum(r.hours for r in overtime_records if r.is_transferred)
        transferred_cost = sum(r.cost for r in overtime_records if r.is_transferred)
        pending_hours = sum(r.hours for r in overtime_records if not r.is_transferred)
        pending_cost = sum(r.cost for r in overtime_records if not r.is_transferred)

        # تجهيز بيانات للعرض
        overtime_data = []
        for record in overtime_records:
            overtime_data.append({
                'id': record.id,
                'employee_id': record.employee_id,
                'employee_name': record.employee.full_name if record.employee else 'غير معروف',
                'employee_color': f'#{hash(record.employee.full_name or "") % 0xFFFFFF:06x}',
                'overtime_date': record.overtime_date.strftime('%Y-%m-%d'),
                'month': record.month,
                'year': record.year,
                'hours': record.hours,
                'rate': record.rate,
                'cost': record.cost,
                'reason': record.reason or '',
                'notes': record.notes or '',
                'is_transferred': record.is_transferred,
                'transferred_to_payroll_id': record.transferred_to_payroll_id
            })

        # قائمة الموظفين للفلترة
        employees = Employee.query.filter_by(is_active=True).order_by(Employee.full_name).all()

        # بيانات الرسم البياني (آخر 6 أشهر) - ✅ التأكد من أن chart_data معرف دائماً
        months = []
        chart_data = [0, 0, 0, 0, 0, 0]  # قيمة افتراضية
        today = date.today()

        try:
            for i in range(5, -1, -1):
                month_date = today - timedelta(days=30 * i)
                month_name = {
                    1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
                    5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
                    9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
                }.get(month_date.month, f'شهر {month_date.month}')
                months.append(month_name)

                month_records = Overtime.query.filter(
                    Overtime.year == month_date.year,
                    Overtime.month == month_date.month
                ).all()
                month_hours = sum(r.hours for r in month_records)
                chart_data[i] = month_hours  # تحديث القيمة في المكان الصحيح
        except Exception as chart_error:
            app.logger.error(f"Error generating chart data: {str(chart_error)}")
            # استخدم القيم الافتراضية

        return render_template('reports/overtime.html',
                               overtime_data=overtime_data[:10],  # أول 10 فقط
                               employees=employees,
                               selected_employee=employee_id,
                               from_date=from_date,
                               to_date=to_date,
                               from_date_str=from_date_str,
                               to_date_str=to_date_str,
                               selected_status=status,
                               total_overtime_hours=round(total_hours, 1),
                               avg_overtime_per_employee=round(total_hours / len(overtime_data),
                                                               1) if overtime_data else 0,
                               top_overtime_employee=overtime_data[0]['employee_name'] if overtime_data else '-',
                               top_overtime_hours=overtime_data[0]['hours'] if overtime_data else 0,
                               total_overtime_cost=round(total_cost, 2),
                               overtime_chart_data=chart_data,  # ✅ تأكد من تمرير chart_data
                               months_labels=months)

    except Exception as e:
        app.logger.error(f"Error in overtime_list: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        flash(f'حدث خطأ: {str(e)}', 'error')
        return redirect(url_for('reports_index'))
@app.route('/overtime/add', methods=['POST'])
@login_required
def add_overtime():
    """إضافة ساعة إضافية جديدة"""
    if current_user.role != 'owner':
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403

    try:
        from models import Overtime

        # الحصول على البيانات من النموذج
        employee_id = request.form.get('employee_id')
        overtime_date = request.form.get('overtime_date')
        hours = request.form.get('hours')
        rate = request.form.get('rate', 25)
        reason = request.form.get('reason', '')
        notes = request.form.get('notes', '')

        # التحقق من البيانات المطلوبة
        if not all([employee_id, overtime_date, hours]):
            return jsonify({
                'success': False,
                'message': 'الرجاء ملء جميع الحقول المطلوبة'
            }), 400

        # تحويل التاريخ
        try:
            overtime_date_obj = datetime.strptime(overtime_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'صيغة التاريخ غير صحيحة'
            }), 400

        # التحقق من وجود الموظف
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({
                'success': False,
                'message': 'الموظف غير موجود'
            }), 404

        # تحويل القيم
        hours_float = float(hours)
        rate_float = float(rate) if rate else 25.0
        cost = round(hours_float * rate_float, 2)

        # إنشاء سجل الساعات الإضافية
        overtime = Overtime(
            employee_id=int(employee_id),
            overtime_date=overtime_date_obj,
            year=overtime_date_obj.year,
            month=overtime_date_obj.month,
            hours=hours_float,
            rate=rate_float,
            cost=cost,  # ✅ حساب التكلفة مباشرة
            reason=reason,
            notes=notes,
            is_transferred=False
        )

        db.session.add(overtime)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '✅ تم إضافة الساعة الإضافية بنجاح',
            'overtime_id': overtime.id,
            'hours': overtime.hours,
            'cost': overtime.cost
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in add_overtime: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'حدث خطأ: {str(e)}'
        }), 500


@app.route('/overtime/transfer-to-payroll', methods=['POST'])
@login_required
def transfer_overtime_to_payroll():
    """ترحيل الساعات الإضافية إلى كشف المرتبات - مع تحديث الإغلاق الشهري"""
    if current_user.role != 'owner':
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403

    try:
        from models import Overtime, Payroll

        data = request.get_json()
        overtime_ids = data.get('overtime_ids', [])
        transfer_all = data.get('transfer_all', False)
        month = data.get('month', date.today().month)
        year = data.get('year', date.today().year)

        # بناء الاستعلام
        query = Overtime.query.filter_by(is_transferred=False)

        if not transfer_all and overtime_ids:
            query = query.filter(Overtime.id.in_(overtime_ids))
        elif not transfer_all and not overtime_ids:
            return jsonify({
                'success': False,
                'message': 'لم يتم تحديد أي ساعات إضافية للترحيل'
            }), 400

        overtimes = query.all()

        if not overtimes:
            return jsonify({
                'success': False,
                'message': 'لا توجد ساعات إضافية غير مرحّلة'
            }), 400

        # تجميع الساعات الإضافية حسب الموظف
        overtime_summary = {}
        for overtime in overtimes:
            key = f"{overtime.employee_id}_{year}_{month}"

            if key not in overtime_summary:
                overtime_summary[key] = {
                    'employee_id': overtime.employee_id,
                    'year': year,
                    'month': month,
                    'total_hours': 0,
                    'total_cost': 0,
                    'ids': []
                }

            overtime_summary[key]['total_hours'] += overtime.hours
            overtime_summary[key]['total_cost'] += overtime.cost
            overtime_summary[key]['ids'].append(overtime.id)

        # تحديث كشوف الرواتب
        transferred_count = 0
        affected_months = set()

        for key, summary in overtime_summary.items():
            # البحث عن كشف الراتب
            payroll = Payroll.query.filter_by(
                employee_id=summary['employee_id'],
                year=year,
                month=month
            ).first()

            if payroll:
                # تحديث كشف الراتب الموجود
                payroll.overtime_hours = (payroll.overtime_hours or 0) + summary['total_hours']
                payroll.overtime_pay = (payroll.overtime_pay or 0) + summary['total_cost']
                payroll.calculate_payroll()
            else:
                # إنشاء كشف راتب جديد
                employee = Employee.query.get(summary['employee_id'])
                if employee:
                    payroll = Payroll(
                        employee_id=employee.id,
                        year=year,
                        month=month,
                        base_salary=employee.salary or 0,
                        overtime_hours=summary['total_hours'],
                        overtime_pay=summary['total_cost'],
                        status='pending'
                    )
                    payroll.calculate_payroll()
                    db.session.add(payroll)
                    db.session.flush()

            # تحديث حالة الساعات الإضافية
            for oid in summary['ids']:
                overtime = Overtime.query.get(oid)
                if overtime:
                    overtime.is_transferred = True
                    overtime.transferred_to_payroll_id = payroll.id
                    transferred_count += 1

            affected_months.add((year, month))

        db.session.commit()

        # ✅ تحديث الإغلاق الشهري لكل شهر تأثر
        for y, m in affected_months:
            trigger_monthly_closing_update(y, m)

        return jsonify({
            'success': True,
            'message': f'✅ تم ترحيل {transferred_count} ساعة إضافية بنجاح',
            'transferred_count': transferred_count
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in transfer_overtime_to_payroll: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/debug/overtime-transfer', methods=['GET'])
@login_required
def debug_overtime_transfer():
    """صفحة تشخيص لمشكلة ترحيل الساعات الإضافية"""
    if current_user.role != 'owner':
        return "غير مصرح", 403

    try:
        from models import Overtime, Payroll

        # إحصائيات
        total_overtime = Overtime.query.count()
        transferred = Overtime.query.filter_by(is_transferred=True).count()
        pending = Overtime.query.filter_by(is_transferred=False).count()

        # آخر 10 سجلات غير مرحّلة
        pending_records = Overtime.query.filter_by(is_transferred=False).order_by(Overtime.overtime_date.desc()).limit(
            10).all()

        # كشوف الرواتب
        payrolls = Payroll.query.order_by(Payroll.year.desc(), Payroll.month.desc()).limit(10).all()

        html = f"""
        <!DOCTYPE html>
        <html dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>🔍 تشخيص ترحيل الساعات الإضافية</title>
            <style>
                body {{ font-family: 'Cairo', sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: right; }}
                th {{ background-color: #f2f2f2; }}
                .success {{ background-color: #d4edda; color: #155724; }}
                .warning {{ background-color: #fff3cd; color: #856404; }}
                .danger {{ background-color: #f8d7da; color: #721c24; }}
                .btn {{ padding: 10px 15px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; }}
                .btn-primary {{ background-color: #007bff; color: white; }}
                .pre {{ background-color: #f8f9fa; padding: 10px; border-radius: 5px; overflow: auto; }}
            </style>
        </head>
        <body>
            <h1>🔍 تشخيص مشكلة ترحيل الساعات الإضافية</h1>

            <div style="display: flex; gap: 20px; margin: 20px 0;">
                <div style="flex:1; background: #007bff; color: white; padding: 20px; border-radius: 10px;">
                    <h3>إجمالي الساعات</h3>
                    <h2>{total_overtime}</h2>
                </div>
                <div style="flex:1; background: #28a745; color: white; padding: 20px; border-radius: 10px;">
                    <h3>تم الترحيل</h3>
                    <h2>{transferred}</h2>
                </div>
                <div style="flex:1; background: #ffc107; color: black; padding: 20px; border-radius: 10px;">
                    <h3>غير مرحّل</h3>
                    <h2>{pending}</h2>
                </div>
            </div>

            <h2>📋 آخر السجلات غير المرحّلة</h2>
            <table>
                <tr>
                    <th>ID</th>
                    <th>الموظف</th>
                    <th>التاريخ</th>
                    <th>الساعات</th>
                    <th>التكلفة</th>
                    <th>تم الترحيل؟</th>
                    <th>إجراء</th>
                </tr>
        """

        for record in pending_records:
            html += f"""
                <tr>
                    <td>{record.id}</td>
                    <td>{record.employee.full_name if record.employee else 'غير معروف'}</td>
                    <td>{record.overtime_date}</td>
                    <td>{record.hours}</td>
                    <td>{record.cost}</td>
                    <td class="warning">لا</td>
                    <td>
                        <button class="btn btn-primary" onclick="testTransfer({record.id})">
                            اختبار الترحيل
                        </button>
                    </td>
                </tr>
            """

        html += """
            </table>

            <h2>📊 آخر كشوف الرواتب</h2>
            <table>
                <tr>
                    <th>ID</th>
                    <th>الموظف</th>
                    <th>الشهر/السنة</th>
                    <th>ساعات إضافية</th>
                    <th>قيمة إضافية</th>
                    <th>صافي الراتب</th>
                </tr>
        """

        for payroll in payrolls:
            html += f"""
                <tr>
                    <td>{payroll.id}</td>
                    <td>{payroll.employee.full_name if payroll.employee else 'غير معروف'}</td>
                    <td>{payroll.month}/{payroll.year}</td>
                    <td>{payroll.overtime_hours or 0}</td>
                    <td>{payroll.overtime_pay or 0}</td>
                    <td>{payroll.net_salary}</td>
                </tr>
            """

        html += """
            </table>

            <div id="result" style="margin-top: 20px; padding: 20px; border: 1px solid #ccc; border-radius: 5px;"></div>

            <script>
            function testTransfer(id) {
                const resultDiv = document.getElementById('result');
                resultDiv.innerHTML = '<div style="background: #e9ecef; padding: 10px;">جاري الترحيل...</div>';

                fetch('/overtime/transfer-to-payroll', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        overtime_ids: [id],
                        month: new Date().getMonth() + 1,
                        year: new Date().getFullYear()
                    })
                })
                .then(response => response.json())
                .then(data => {
                    resultDiv.innerHTML = '<pre class="pre">' + JSON.stringify(data, null, 2) + '</pre>';
                    if (data.success) {
                        setTimeout(() => location.reload(), 2000);
                    }
                })
                .catch(error => {
                    resultDiv.innerHTML = '<div class="danger">خطأ: ' + error + '</div>';
                });
            }
            </script>
        </body>
        </html>
        """

        return html

    except Exception as e:
        return f"<h1>خطأ: {str(e)}</h1>"

@app.route('/overtime/delete/<int:overtime_id>', methods=['POST'])
@login_required
def delete_overtime(overtime_id):
    """حذف سجل ساعة إضافية"""
    if current_user.role != 'owner':
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403

    try:
        from models import Overtime

        overtime = Overtime.query.get_or_404(overtime_id)

        if overtime.is_transferred:
            return jsonify({
                'success': False,
                'message': 'لا يمكن حذف ساعة إضافية تم ترحيلها بالفعل'
            }), 400

        db.session.delete(overtime)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '✅ تم حذف الساعة الإضافية بنجاح'
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in delete_overtime: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'حدث خطأ: {str(e)}'
        }), 500


# ============================================
# ✅ دوال مساعدة
# ============================================

def update_payroll_with_loan_deduction(employee_id, year, month, amount):
    """تحديث كشف الراتب بخصم السلفة"""
    try:
        from models import Payroll

        payroll = Payroll.query.filter_by(
            employee_id=employee_id,
            year=year,
            month=month
        ).first()

        if payroll:
            payroll.loan_deduction = (payroll.loan_deduction or 0) + amount
            payroll.calculate_payroll()
            db.session.commit()
            return True
        return False
    except Exception as e:
        app.logger.error(f"Error updating payroll with loan: {str(e)}")
        return False


def get_top_overtime_employee():
    """الحصول على الموظف الأكثر ساعات إضافية"""
    try:
        from models import Overtime
        from sqlalchemy import func

        result = db.session.query(
            Overtime.employee_id,
            func.sum(Overtime.hours).label('total_hours')
        ).group_by(Overtime.employee_id).order_by(func.sum(Overtime.hours).desc()).first()

        if result and result[0]:
            employee = Employee.query.get(result[0])
            return employee.full_name if employee else 'غير معروف'
        return 'لا يوجد'
    except:
        return 'لا يوجد'


def get_top_overtime_hours():
    """الحصول على أعلى عدد ساعات إضافية"""
    try:
        from models import Overtime
        from sqlalchemy import func

        result = db.session.query(
            func.sum(Overtime.hours)
        ).group_by(Overtime.employee_id).order_by(func.sum(Overtime.hours).desc()).first()

        return round(result[0], 1) if result and result[0] else 0
    except:
        return 0


# ============================================
# ✅ تحديث دالة report_overtime الحالية
# ============================================
@app.route('/reports/overtime')
@login_required
def report_overtime():
    """تقرير ساعات العمل الإضافية (محدث)"""
    if not check_permission('can_view_overtime'):
        flash('غير مصرح بعرض تقارير الساعات الإضافية', 'error')
        return redirect(url_for('reports_index'))

    try:
        from models import Overtime
        from datetime import datetime, date, timedelta

        # الحصول على معاملات الفلترة
        employee_id = request.args.get('employee_id', type=int)
        from_date_str = request.args.get('from_date', '')
        to_date_str = request.args.get('to_date', '')

        # بناء الاستعلام
        query = Overtime.query

        if employee_id:
            query = query.filter_by(employee_id=employee_id)

        if from_date_str:
            try:
                from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
                query = query.filter(Overtime.overtime_date >= from_date)
            except:
                from_date = date.today().replace(day=1)
        else:
            from_date = date.today().replace(day=1)

        if to_date_str:
            try:
                to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
                query = query.filter(Overtime.overtime_date <= to_date)
            except:
                to_date = date.today()
        else:
            to_date = date.today()

        # تنفيذ الاستعلام - جلب جميع السجلات
        overtime_records = query.order_by(Overtime.overtime_date.desc()).all()

        # ============================================
        # 1. تجهيز بيانات الجدول (كل سجل على حدة)
        # ============================================
        overtime_data = []
        total_hours = 0
        total_cost = 0

        for record in overtime_records:
            if not record.employee:
                continue

            # حساب النسبة التقريبية من الراتب (افتراضي 200 ساعة عمل في الشهر)
            monthly_hours = 200
            percentage = min(round((record.hours / monthly_hours) * 100), 100) if record.hours > 0 else 0

            overtime_data.append({
                'id': record.id,
                'employee_id': record.employee_id,
                'employee_name': record.employee.full_name,
                'employee_color': f'#{hash(record.employee.full_name) % 0xFFFFFF:06x}',
                'department': record.employee.position or 'غير محدد',
                'month': f'{record.month}/{record.year}',
                'month_num': record.month,
                'year': record.year,
                'hours': record.hours,
                'cost': record.cost,
                'hourly_rate': record.rate,
                'percentage': percentage,
                'is_transferred': record.is_transferred,
                'overtime_date': record.overtime_date.strftime('%Y-%m-%d') if record.overtime_date else ''
            })

            total_hours += record.hours
            total_cost += record.cost

        # ============================================
        # 2. تجميع البيانات للتحليل (حسب الموظف)
        # ============================================
        employee_totals = {}
        for record in overtime_records:
            if not record.employee:
                continue
            emp_id = record.employee_id
            if emp_id not in employee_totals:
                employee_totals[emp_id] = {
                    'employee_name': record.employee.full_name,
                    'total_hours': 0,
                    'total_cost': 0
                }
            employee_totals[emp_id]['total_hours'] += record.hours
            employee_totals[emp_id]['total_cost'] += record.cost

        # الموظف الأكثر ساعات
        top_employee = 'لا يوجد'
        top_hours = 0
        if employee_totals:
            top_emp = max(employee_totals.items(), key=lambda x: x[1]['total_hours'])
            top_employee = top_emp[1]['employee_name']
            top_hours = top_emp[1]['total_hours']

        # ============================================
        # 3. بيانات الرسم البياني (آخر 6 أشهر)
        # ============================================
        months = []
        chart_data = []
        today = date.today()

        # أسماء الأشهر بالعربية
        month_names_ar = {
            1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
            5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
            9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
        }

        # إنشاء بيانات الرسم البياني لآخر 6 أشهر
        for i in range(5, -1, -1):
            # حساب الشهر المطلوب
            month_date = today - timedelta(days=30 * i)
            month_name = month_names_ar.get(month_date.month, f'شهر {month_date.month}')
            months.append(month_name)

            # البحث عن سجلات هذا الشهر
            month_records = [r for r in overtime_records
                             if r.year == month_date.year and r.month == month_date.month]

            month_hours = sum(r.hours for r in month_records)
            chart_data.append(round(month_hours, 1))

        # إذا كانت كل القيم صفر، نضيف بعض البيانات التجريبية للعرض
        if all(v == 0 for v in chart_data):
            # استخدام بيانات تجريبية للعرض فقط
            chart_data = [12, 19, 15, 22, 18, 24]  # قيم تجريبية
            app.logger.info("📊 استخدام بيانات تجريبية للرسم البياني")

        # قائمة الموظفين للفلترة
        employees = Employee.query.filter_by(is_active=True).order_by(Employee.full_name).all()

        # ============================================
        # 4. تجهيز المتغيرات للقالب
        # ============================================
        context = {
            'overtime_data': overtime_data,  # بيانات الجدول (كل سجل على حدة)
            'employees': employees,
            'selected_employee': employee_id,
            'from_date': from_date,
            'to_date': to_date,
            'from_date_str': from_date.strftime('%Y-%m-%d') if from_date else '',
            'to_date_str': to_date.strftime('%Y-%m-%d') if to_date else '',
            'total_overtime_hours': round(total_hours, 1),
            'avg_overtime_per_employee': round(total_hours / len(employee_totals), 1) if employee_totals else 0,
            'top_overtime_employee': top_employee,
            'top_overtime_hours': round(top_hours, 1),
            'total_overtime_cost': round(total_cost, 2),
            'overtime_chart_data': chart_data,
            'months_labels': months
        }

        return render_template('reports/overtime.html', **context)

    except Exception as e:
        app.logger.error(f"Error in report_overtime: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))
# ============================================
# تقارير التقييمات الشهرية المتقدمة (المسار المفقود)
# ============================================

@app.route('/reports/monthly-trends-advanced')
@login_required
def report_monthly_trends_advanced():
    """تقرير اتجاهات التقييم الشهرية المتقدمة - يعتمد على بيانات حقيقية ومفلترة"""
    try:
        app.logger.info("=" * 50)
        app.logger.info(f"📊 تقرير الاتجاهات الشهرية المتقدمة - المستخدم: {current_user.username}")

        # الحصول على التقييمات المفلترة
        all_evaluations = get_filtered_evaluations(current_user)

        # الحصول على آخر 6 أشهر
        months = []
        month_labels = []
        month_averages = []
        monthly_counts = []
        monthly_data = []

        today_date = date.today()
        for i in range(5, -1, -1):  # آخر 6 أشهر
            month_date = today_date - timedelta(days=30 * i)
            month_num = month_date.month
            year = month_date.year

            # اسم الشهر
            month_names = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
                           'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
            month_name = month_names[month_num - 1]
            months.append(month_name)
            month_labels.append(month_name)

            # حساب متوسط التقييم لهذا الشهر
            month_start = date(year, month_num, 1)
            if month_num == 12:
                month_end = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(year, month_num + 1, 1) - timedelta(days=1)

            month_evaluations = [e for e in all_evaluations
                                 if e.date and e.date >= month_start and e.date <= month_end]

            count = len(month_evaluations)
            monthly_counts.append(count)

            if count > 0:
                scores = [e.overall_score for e in month_evaluations if e.overall_score]
                avg = sum(scores) / len(scores) if scores else 0
                avg_score = round(avg, 1)
            else:
                avg_score = 0

            month_averages.append(avg_score * 20)  # تحويل إلى نسبة مئوية

            # أفضل موظف في الشهر
            top_employee = "لا يوجد"
            if count > 0:
                # تجميع التقييمات لكل موظف
                employee_scores = {}
                for e in month_evaluations:
                    if e.evaluated_employee_id and e.overall_score:
                        if e.evaluated_employee_id not in employee_scores:
                            employee_scores[e.evaluated_employee_id] = []
                        employee_scores[e.evaluated_employee_id].append(e.overall_score)

                # حساب متوسط كل موظف
                best_avg = 0
                best_emp_id = None
                for emp_id, scores in employee_scores.items():
                    emp_avg = sum(scores) / len(scores)
                    if emp_avg > best_avg:
                        best_avg = emp_avg
                        best_emp_id = emp_id

                if best_emp_id:
                    employee = Employee.query.get(best_emp_id)
                    if employee:
                        top_employee = employee.full_name

            # أفضل شركة في الشهر
            top_company = "غير محدد"
            if count > 0:
                company_scores = {}
                for e in month_evaluations:
                    if e.place and e.place.location and e.place.location.area and e.place.location.area.company:
                        company_id = e.place.location.area.company_id
                        if company_id not in company_scores:
                            company_scores[company_id] = []
                        if e.overall_score:
                            company_scores[company_id].append(e.overall_score)

                best_company_avg = 0
                best_comp_id = None
                for comp_id, scores in company_scores.items():
                    comp_avg = sum(scores) / len(scores)
                    if comp_avg > best_company_avg:
                        best_company_avg = comp_avg
                        best_comp_id = comp_id

                if best_comp_id:
                    company = Company.query.get(best_comp_id)
                    if company:
                        top_company = company.name

            # تحديد لون الشهر بناءً على التقييم
            if avg_score >= 4.5:
                color = 'success'
            elif avg_score >= 4:
                color = 'info'
            elif avg_score >= 3:
                color = 'warning'
            else:
                color = 'danger'

            # ✅ إضافة البيانات مع حقل change (قيمة مؤقتة)
            monthly_data.append({
                'name': month_name,
                'count': count,
                'avg': avg_score,
                'color': color,
                'top_employee': top_employee,
                'top_company': top_company,
                'change': 0  # قيمة افتراضية
            })

        # ✅ حساب التغيير بين الأشهر وتحديث القيم
        for i in range(1, len(monthly_data)):
            if monthly_data[i - 1]['count'] > 0:
                change = round(
                    ((monthly_data[i]['count'] - monthly_data[i - 1]['count']) / monthly_data[i - 1]['count']) * 100, 1)
                monthly_data[i]['change'] = change
            else:
                monthly_data[i]['change'] = 0

        # أفضل شهر
        if monthly_counts:
            best_month_idx = monthly_counts.index(max(monthly_counts))
            best_month = {
                'name': months[best_month_idx] if months else 'غير محدد',
                'avg': month_averages[best_month_idx] if month_averages else 0
            }
        else:
            best_month = {'name': 'غير محدد', 'avg': 0}

        # متوسط آخر 3 أشهر
        last_3_months = month_averages[-3:] if len(month_averages) >= 3 else month_averages
        three_month_avg = round(sum(last_3_months) / len(last_3_months)) if last_3_months else 0

        # النمو السنوي
        if len(month_averages) >= 2 and month_averages[0] > 0:
            yearly_growth = round(((month_averages[-1] - month_averages[0]) / month_averages[0]) * 100)
        else:
            yearly_growth = 0

        # اتجاه العام
        if len(month_averages) >= 2:
            if month_averages[-1] > month_averages[0]:
                trend_direction = 'تصاعدي'
            elif month_averages[-1] < month_averages[0]:
                trend_direction = 'تنازلي'
            else:
                trend_direction = 'ثابت'
        else:
            trend_direction = 'غير محدد'

        # بيانات توزيع التقييمات
        distribution_labels = ['ممتاز (4.5-5)', 'جيد جداً (4-4.4)', 'جيد (3-3.9)', 'مقبول (2-2.9)', 'ضعيف (1-1.9)']
        distribution_data = [0, 0, 0, 0, 0]

        for e in all_evaluations:
            if e.overall_score:
                if e.overall_score >= 4.5:
                    distribution_data[0] += 1
                elif e.overall_score >= 4:
                    distribution_data[1] += 1
                elif e.overall_score >= 3:
                    distribution_data[2] += 1
                elif e.overall_score >= 2:
                    distribution_data[3] += 1
                else:
                    distribution_data[4] += 1

        app.logger.info(f"📊 تم تجهيز التقرير الشهري بنجاح")
        app.logger.info("=" * 50)

        # ✅ استخدام القالب المناسب
        return render_template('reports/monthly_trends.html',  # أو monthly_trends_advanced.html حسب الموجود
                               best_month=best_month,
                               three_month_avg=three_month_avg,
                               yearly_growth=yearly_growth,
                               trend_direction=trend_direction,
                               month_labels=month_labels,
                               month_averages=month_averages,
                               monthly_data=monthly_data,
                               distribution_labels=distribution_labels,
                               distribution_data=distribution_data)

    except Exception as e:
        app.logger.error(f"❌ Error in report_monthly_trends_advanced: {str(e)}")
        import traceback
        app.logger.error(f"🔍 تفاصيل الخطأ: {traceback.format_exc()}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))


# ==================================

def get_supervised_employees(user):
    """الحصول على جميع الموظفين التابعين للمستخدم الحالي (محسنة)"""
    try:
        if user.role == 'owner':
            # المالك يرى جميع الموظفين
            return Employee.query.filter_by(is_active=True).all()

        elif user.role == 'supervisor':
            # المشرف يرى جميع الموظفين التابعين له
            supervisor_emp = Employee.query.filter_by(user_id=user.id).first()
            if supervisor_emp:
                supervised_ids = []

                # 1. التابعين المباشرين
                direct_subs = Employee.query.filter_by(
                    supervisor_id=supervisor_emp.id,
                    is_active=True
                ).all()
                supervised_ids.extend([emp.id for emp in direct_subs])

                # 2. الموظفين في المناطق التي يشرف عليها
                supervised_areas = Area.query.filter_by(
                    supervisor_id=supervisor_emp.id,
                    is_active=True
                ).all()

                for area in supervised_areas:
                    # المراقبين في مواقع هذه المنطقة
                    locations = Location.query.filter_by(
                        area_id=area.id,
                        is_active=True
                    ).all()

                    for location in locations:
                        if location.monitor_id:
                            supervised_ids.append(location.monitor_id)

                        # العمال في أماكن هذا الموقع
                        places = Place.query.filter_by(
                            location_id=location.id,
                            is_active=True
                        ).all()

                        for place in places:
                            if place.worker_id:
                                supervised_ids.append(place.worker_id)

                # إزالة التكرارات
                supervised_ids = list(set(supervised_ids))

                if supervised_ids:
                    return Employee.query.filter(Employee.id.in_(supervised_ids)).all()

            return []

        elif user.role == 'monitor':
            # المراقب يرى العمال في موقعه فقط
            monitor_emp = Employee.query.filter_by(user_id=user.id).first()
            if monitor_emp:
                # الحصول على الأماكن المرتبطة بالمراقب
                places = Place.query.join(Location).filter(
                    Location.monitor_id == monitor_emp.id,
                    Place.is_active == True
                ).all()

                worker_ids = [p.worker_id for p in places if p.worker_id]
                if worker_ids:
                    return Employee.query.filter(Employee.id.in_(worker_ids)).all()
            return []

        else:
            # العامل يرى نفسه فقط
            emp = Employee.query.filter_by(user_id=user.id).first()
            return [emp] if emp else []

    except Exception as e:
        app.logger.error(f"❌ Error in get_supervised_employees: {str(e)}")
        return []


def get_employees_for_evaluation(user):
    """الحصول على قائمة الموظفين المسموح للمستخدم بتقييمهم (محسنة)"""

    if user.role == 'owner':
        # المالك: جميع الموظفين النشطين
        return Employee.query.filter_by(is_active=True).order_by(Employee.full_name).all()

    elif user.role == 'supervisor':
        # المشرف: المراقبون والعمال التابعين له فقط (نفس الشركة)
        supervisor_employee = Employee.query.filter_by(user_id=user.id).first()
        if not supervisor_employee:
            return []

        # الحصول على شركة المشرف
        supervisor_company_id = supervisor_employee.company_id

        supervised_ids = []

        # 1. التابعين المباشرين في نفس الشركة
        direct_subordinates = Employee.query.filter_by(
            supervisor_id=supervisor_employee.id,
            company_id=supervisor_company_id,
            is_active=True
        ).all()

        for emp in direct_subordinates:
            supervised_ids.append(emp.id)
            app.logger.info(f"📌 تابع مباشر في نفس الشركة: {emp.full_name}")

        # 2. الموظفين في المناطق التي يشرف عليها (نفس الشركة)
        supervised_areas = Area.query.filter_by(
            supervisor_id=supervisor_employee.id,
            company_id=supervisor_company_id,
            is_active=True
        ).all()

        for area in supervised_areas:
            # الحصول على المواقع في هذه المنطقة
            locations = Location.query.filter_by(
                area_id=area.id,
                is_active=True
            ).all()

            for location in locations:
                # إضافة المراقب إذا وجد وفي نفس الشركة
                if location.monitor_id:
                    monitor = Employee.query.get(location.monitor_id)
                    if monitor and monitor.company_id == supervisor_company_id:
                        supervised_ids.append(location.monitor_id)

                # الحصول على الأماكن في هذا الموقع
                places = Place.query.filter_by(
                    location_id=location.id,
                    is_active=True
                ).all()

                for place in places:
                    if place.worker_id:
                        worker = Employee.query.get(place.worker_id)
                        if worker and worker.company_id == supervisor_company_id:
                            supervised_ids.append(place.worker_id)

        # إزالة التكرارات
        supervised_ids = list(set(supervised_ids))

        if supervised_ids:
            employees = Employee.query.filter(
                Employee.id.in_(supervised_ids),
                Employee.company_id == supervisor_company_id,  # تأكيد نفس الشركة
                Employee.is_active == True
            ).order_by(Employee.full_name).all()

            return employees

        return []

    elif user.role == 'monitor':
        # المراقب: العمال في موقعه فقط
        monitor_employee = Employee.query.filter_by(user_id=user.id).first()
        if not monitor_employee:
            return []

        # الحصول على المواقع التي يراقبها
        monitored_locations = Location.query.filter_by(
            monitor_id=monitor_employee.id,
            is_active=True
        ).all()

        location_ids = [loc.id for loc in monitored_locations]

        if location_ids:
            # الحصول على العمال في هذه المواقع
            places = Place.query.filter(
                Place.location_id.in_(location_ids),
                Place.is_active == True,
                Place.worker_id.isnot(None)
            ).all()

            worker_ids = [place.worker_id for place in places]

            if worker_ids:
                workers = Employee.query.filter(
                    Employee.id.in_(worker_ids),
                    Employee.is_active == True
                ).order_by(Employee.full_name).all()
                return workers

        return []

    return []

def can_evaluate_employee(evaluator_user, evaluated_employee, place):
    """التحقق من صلاحية المستخدم في تقييم موظف معين (محسنة)"""

    if evaluator_user.role == 'owner':
        # المالك: يقيّم جميع الموظفين
        app.logger.info(f"👑 المالك يقيّم {evaluated_employee.full_name}")
        return True

    elif evaluator_user.role == 'supervisor':
        # المشرف: يقيّم المراقبين والعمال التابعين له
        supervisor_employee = Employee.query.filter_by(user_id=evaluator_user.id).first()
        if not supervisor_employee:
            app.logger.warning("❌ المشرف ليس لديه ملف موظف")
            return False

        supervisor_id = supervisor_employee.id
        app.logger.info(f"🔍 التحقق من صلاحية المشرف {supervisor_id} لتقييم {evaluated_employee.full_name}")

        # 1. التحقق من التبعية المباشرة
        if evaluated_employee.supervisor_id == supervisor_id:
            app.logger.info(f"✅ تابع مباشر: {evaluated_employee.full_name}")
            return evaluated_employee.position in ['monitor', 'worker']

        # 2. التحقق من خلال المناطق
        if place and place.location and place.location.area:
            # هل المنطقة تابع للمشرف؟
            if place.location.area.supervisor_id == supervisor_id:
                app.logger.info(f"✅ المنطقة تابع للمشرف: {place.location.area.name}")

                # إذا كان الموظف مراقباً في هذه المنطقة
                if evaluated_employee.position == 'monitor':
                    if place.location.monitor_id == evaluated_employee.id:
                        app.logger.info(f"✅ مراقب في المنطقة: {evaluated_employee.full_name}")
                        return True

                # إذا كان الموظف عاملاً في هذه المنطقة
                elif evaluated_employee.position == 'worker':
                    # البحث إذا كان هذا العامل يعمل في مكان بالمنطقة
                    worker_places = Place.query.filter_by(
                        worker_id=evaluated_employee.id,
                        is_active=True
                    ).join(Location).filter(
                        Location.area_id == place.location.area.id
                    ).first()

                    if worker_places:
                        app.logger.info(f"✅ عامل في المنطقة: {evaluated_employee.full_name}")
                        return True

        app.logger.warning(f"❌ لا توجد صلاحية لتقييم {evaluated_employee.full_name}")
        return False

    elif evaluator_user.role == 'monitor':
        # المراقب: يقيّم العمال في موقعه فقط
        monitor_employee = Employee.query.filter_by(user_id=evaluator_user.id).first()
        if not monitor_employee:
            return False

        # التحقق من أن الموظف عامل
        if evaluated_employee.position != 'worker':
            return False

        # التحقق من أن المكان يقع في موقع يراقبه المراقب
        if place and place.location and place.location.monitor_id == monitor_employee.id:
            # التحقق من أن العامل هو نفسه المعين في هذا المكان
            if place.worker_id == evaluated_employee.id:
                return True

        return False

    return False

# ============================================
# دوال مساعدة للفلترة حسب الصلاحيات (محسنة)
# ============================================

def get_filtered_evaluations(user):
    """
    جلب التقييمات التي يُسمح للمستخدم بمشاهدتها بناءً على صلاحياته.
    هذه الدالة مركزية لتوحيد منطق الفلترة في جميع أنحاء التطبيق.
    """
    try:
        from sqlalchemy.orm import joinedload

        base_query = CleaningEvaluation.query.options(
            joinedload(CleaningEvaluation.place),
            joinedload(CleaningEvaluation.evaluator),
            joinedload(CleaningEvaluation.evaluated_employee)
        )

        if user.role == 'owner':
            # المالك: يرى جميع التقييمات
            return base_query.order_by(CleaningEvaluation.date.desc()).all()

        elif user.role == 'supervisor':
            # المشرف: يرى تقييمات الموظفين التابعين له
            if user.employee_profile:
                supervisor_id = user.employee_profile.id
                supervised_employees_ids = []

                # 1. التابعين المباشرين
                direct_subs = Employee.query.filter_by(supervisor_id=supervisor_id, is_active=True).all()
                supervised_employees_ids.extend([emp.id for emp in direct_subs])

                # 2. الموظفين في المناطق التي يشرف عليها
                supervised_areas = Area.query.filter_by(supervisor_id=supervisor_id, is_active=True).all()
                for area in supervised_areas:
                    # المراقبين في مواقع المنطقة
                    locations = Location.query.filter_by(area_id=area.id, is_active=True).all()
                    for location in locations:
                        if location.monitor_id:
                            supervised_employees_ids.append(location.monitor_id)
                        # العمال في أماكن الموقع
                        places = Place.query.filter_by(location_id=location.id, is_active=True).all()
                        for place in places:
                            if place.worker_id:
                                supervised_employees_ids.append(place.worker_id)

                supervised_employees_ids = list(set(supervised_employees_ids))

                if supervised_employees_ids:
                    return base_query.filter(
                        db.or_(
                            CleaningEvaluation.evaluated_employee_id.in_(supervised_employees_ids),
                            CleaningEvaluation.evaluator_id.in_(supervised_employees_ids)
                        )
                    ).order_by(CleaningEvaluation.date.desc()).all()
            return []

        elif user.role == 'monitor':
            # المراقب: يرى تقييمات العمال في موقعه فقط
            if user.employee_profile:
                monitor_id = user.employee_profile.id
                monitored_locations = Location.query.filter_by(monitor_id=monitor_id, is_active=True).all()
                location_ids = [loc.id for loc in monitored_locations]

                if location_ids:
                    # الحصول على أماكن هذه المواقع
                    places = Place.query.filter(Place.location_id.in_(location_ids), Place.is_active == True).all()
                    place_ids = [place.id for place in places]

                    if place_ids:
                        # الحصول على تقييمات هذه الأماكن (الموظف المقيّم هو العامل في المكان)
                        # ملاحظة: قد يكون التقييم مرتبطاً بالمكان مباشرة
                        return base_query.filter(
                            CleaningEvaluation.place_id.in_(place_ids)
                        ).order_by(CleaningEvaluation.date.desc()).all()
            return []

        elif user.role == 'worker':
            # العامل: يرى تقييماته فقط
            if user.employee_profile:
                worker_id = user.employee_profile.id
                return base_query.filter(
                    CleaningEvaluation.evaluated_employee_id == worker_id
                ).order_by(CleaningEvaluation.date.desc()).all()
            return []

        else:
            return []

    except Exception as e:
        app.logger.error(f"❌ Error in get_filtered_evaluations: {str(e)}")
        return []

@app.route('/api/employees/evaluatable')
@login_required
def get_evaluatable_employees():
    """API محسن للحصول على الموظفين المسموح للمستخدم الحالي بتقييمهم"""
    try:
        employees = get_employees_for_evaluation(current_user)

        employees_data = [{
            'id': emp.id,
            'full_name': emp.full_name,
            'position': emp.position,
            'position_ar': 'مشرف' if emp.position == 'supervisor'
                          else 'مراقب' if emp.position == 'monitor'
                          else 'عامل',
            'supervisor_id': emp.supervisor_id,
            'is_active': emp.is_active
        } for emp in employees]

        app.logger.info(f"📊 API: تم إرجاع {len(employees_data)} موظف للتقييم للمستخدم {current_user.username}")

        return jsonify({
            'success': True,
            'data': employees_data,
            'count': len(employees_data)
        })

    except Exception as e:
        app.logger.error(f"❌ Error in get_evaluatable_employees: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ في تحميل بيانات الموظفين',
            'data': [],
            'count': 0
        }), 500


# ============================================
# تقييمات المشرفين - جديدة
# ============================================

@app.route('/supervisor-evaluations')
@login_required
def supervisor_evaluations_list():
    """عرض قائمة تقييمات المشرفين"""
    try:
        from sqlalchemy.orm import joinedload

        # التحقق من الصلاحيات - للمالك فقط
        if current_user.role != 'owner':
            flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
            return redirect(url_for('dashboard'))

        # استعلام تقييمات المشرفين مع تحميل العلاقات
        evaluations = SupervisorEvaluation.query \
            .options(
            joinedload(SupervisorEvaluation.supervisor),
            joinedload(SupervisorEvaluation.evaluator),
            joinedload(SupervisorEvaluation.company)
        ) \
            .order_by(SupervisorEvaluation.date.desc()) \
            .all()

        return render_template('evaluations/supervisor_list.html',
                               evaluations=evaluations,
                               today=date.today())

    except Exception as e:
        app.logger.error(f"❌ Error in supervisor_evaluations_list: {str(e)}")
        flash('حدث خطأ في تحميل قائمة التقييمات', 'error')
        return render_template('evaluations/supervisor_list.html', evaluations=[])


@app.route('/supervisor-evaluations/add', methods=['GET', 'POST'])
@login_required
def add_supervisor_evaluation():
    """إضافة تقييم جديد لمشرف (المقيم هو المالك)"""

    # التحقق من الصلاحيات - للمالك فقط
    if current_user.role != 'owner':
        flash('غير مصرح بإضافة تقييمات للمشرفين', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            # استخراج البيانات من النموذج
            date_str = request.form.get('date', '')
            supervisor_id = request.form.get('supervisor_id', '')
            company_id = request.form.get('company_id', '')

            # حقول التقييم
            workers_followup = request.form.get('workers_followup', '')
            work_efficiency = request.form.get('work_efficiency', '')
            reports_submission = request.form.get('reports_submission', '')
            policies_compliance = request.form.get('policies_compliance', '')
            safety_procedures = request.form.get('safety_procedures', '')
            attendance_commitment = request.form.get('attendance_commitment', '')
            leadership_skills = request.form.get('leadership_skills', '')
            problem_solving = request.form.get('problem_solving', '')

            # الملاحظات
            workers_followup_notes = request.form.get('workers_followup_notes', '')
            efficiency_notes = request.form.get('efficiency_notes', '')
            reports_notes = request.form.get('reports_notes', '')
            policies_notes = request.form.get('policies_notes', '')
            safety_notes = request.form.get('safety_notes', '')
            attendance_notes = request.form.get('attendance_notes', '')
            leadership_notes = request.form.get('leadership_notes', '')
            problem_solving_notes = request.form.get('problem_solving_notes', '')
            general_comments = request.form.get('general_comments', '')

            app.logger.info(f"📨 بيانات تقييم المشرف المستلمة:")
            app.logger.info(f"   - التاريخ: {date_str}")
            app.logger.info(f"   - المشرف: {supervisor_id}")
            app.logger.info(f"   - الشركة: {company_id}")

            # التحقق من البيانات المطلوبة
            if not all([date_str, supervisor_id, company_id,
                        workers_followup, work_efficiency, reports_submission,
                        policies_compliance, safety_procedures, attendance_commitment,
                        leadership_skills, problem_solving]):
                flash('يرجى ملء جميع الحقول المطلوبة', 'error')
                return redirect(url_for('add_supervisor_evaluation'))

            # تحويل التاريخ
            evaluation_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            if evaluation_date > date.today():
                flash('لا يمكن إضافة تقييم لتاريخ مستقبلي', 'error')
                return redirect(url_for('add_supervisor_evaluation'))

            # ✅ المالك هو المقيم
            # البحث عن ملف الموظف المرتبط بحساب المالك
            evaluator = Employee.query.filter_by(user_id=current_user.id).first()

            if not evaluator:
                # إذا لم يكن للمالك ملف موظف، نستخدم أول مشرف كمقيم (كمخرج طارئ)
                app.logger.warning("⚠️ المالك ليس لديه ملف موظف، سيتم استخدام أول مشرف كمقيم")
                evaluator = Employee.query.filter_by(position='supervisor', is_active=True).first()

                if not evaluator:
                    # إذا لم يكن هناك مشرف، نستخدم أول موظف
                    evaluator = Employee.query.filter_by(is_active=True).first()

                    if not evaluator:
                        flash('لا يوجد موظفين في النظام لاستخدامهم كمقيمين', 'error')
                        return redirect(url_for('add_supervisor_evaluation'))

            app.logger.info(f"👑 المالك يقوم بالتقييم كمقيم: {evaluator.full_name} (ID: {evaluator.id})")

            # التحقق من وجود المشرف
            supervisor = Employee.query.get(supervisor_id)
            if not supervisor or supervisor.position != 'supervisor':
                flash('المشرف المحدد غير موجود', 'error')
                return redirect(url_for('add_supervisor_evaluation'))

            # التحقق من وجود الشركة
            company = Company.query.get(company_id)
            if not company:
                flash('الشركة المحددة غير موجودة', 'error')
                return redirect(url_for('add_supervisor_evaluation'))

            # إنشاء التقييم
            evaluation = SupervisorEvaluation(
                date=evaluation_date,
                supervisor_id=int(supervisor_id),
                evaluator_id=evaluator.id,  # المقيم هو المالك
                company_id=int(company_id),

                workers_followup=int(workers_followup),
                workers_followup_notes=workers_followup_notes,

                work_efficiency=int(work_efficiency),
                efficiency_notes=efficiency_notes,

                reports_submission=int(reports_submission),
                reports_notes=reports_notes,

                policies_compliance=int(policies_compliance),
                policies_notes=policies_notes,

                safety_procedures=int(safety_procedures),
                safety_notes=safety_notes,

                attendance_commitment=int(attendance_commitment),
                attendance_notes=attendance_notes,

                leadership_skills=int(leadership_skills),
                leadership_notes=leadership_notes,

                problem_solving=int(problem_solving),
                problem_solving_notes=problem_solving_notes,

                general_comments=general_comments or None,
                overall_score=0.0
            )

            # حساب النتيجة الإجمالية
            evaluation.calculate_overall_score()

            db.session.add(evaluation)
            db.session.commit()

            flash('✅ تم إضافة تقييم المشرف بنجاح!', 'success')
            return redirect(url_for('supervisor_evaluations_list'))

        except ValueError as e:
            db.session.rollback()
            app.logger.error(f"❌ خطأ في تحويل القيم: {str(e)}")
            flash('قيم التقييم غير صحيحة، يرجى التأكد من إدخال أرقام صحيحة', 'error')
            return redirect(url_for('add_supervisor_evaluation'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"❌ خطأ في إضافة تقييم المشرف: {str(e)}")
            import traceback
            app.logger.error(f"🔍 تفاصيل الخطأ: {traceback.format_exc()}")
            flash(f'حدث خطأ: {str(e)}', 'error')
            return redirect(url_for('add_supervisor_evaluation'))

    # GET Request - عرض النموذج
    try:
        # الحصول على قائمة المشرفين النشطين
        supervisors = Employee.query.filter_by(
            position='supervisor',
            is_active=True
        ).order_by(Employee.full_name).all()

        # الحصول على قائمة الشركات النشطة
        companies = Company.query.filter_by(is_active=True).order_by(Company.name).all()

        return render_template('evaluations/add_supervisor.html',
                               today=date.today(),
                               supervisors=supervisors,
                               companies=companies)

    except Exception as e:
        app.logger.error(f"❌ خطأ في تحميل النموذج: {str(e)}")
        flash(f'خطأ في تحميل النموذج: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/api/supervisor-evaluation/<int:evaluation_id>')
@login_required
def get_supervisor_evaluation(evaluation_id):
    """API للحصول على بيانات تقييم مشرف محدد"""
    try:
        from sqlalchemy.orm import joinedload

        evaluation = SupervisorEvaluation.query \
            .options(
            joinedload(SupervisorEvaluation.supervisor),
            joinedload(SupervisorEvaluation.evaluator),
            joinedload(SupervisorEvaluation.company)
        ) \
            .filter(SupervisorEvaluation.id == evaluation_id) \
            .first()

        if not evaluation:
            return jsonify({
                'success': False,
                'message': 'التقييم غير موجود'
            }), 404

        # حساب متوسط الدرجات
        scores = [
            evaluation.workers_followup,
            evaluation.work_efficiency,
            evaluation.reports_submission,
            evaluation.policies_compliance,
            evaluation.safety_procedures,
            evaluation.attendance_commitment,
            evaluation.leadership_skills,
            evaluation.problem_solving
        ]
        avg_score = sum(scores) / len(scores)

        evaluation_data = {
            'id': evaluation.id,
            'date': evaluation.date.strftime('%Y-%m-%d'),
            'supervisor': evaluation.supervisor.full_name if evaluation.supervisor else 'غير محدد',
            'evaluator': evaluation.evaluator.full_name if evaluation.evaluator else 'غير محدد',
            'company': evaluation.company.name if evaluation.company else 'غير محدد',

            'workers_followup': evaluation.workers_followup,
            'workers_followup_notes': evaluation.workers_followup_notes or '',

            'work_efficiency': evaluation.work_efficiency,
            'efficiency_notes': evaluation.efficiency_notes or '',

            'reports_submission': evaluation.reports_submission,
            'reports_notes': evaluation.reports_notes or '',

            'policies_compliance': evaluation.policies_compliance,
            'policies_notes': evaluation.policies_notes or '',

            'safety_procedures': evaluation.safety_procedures,
            'safety_notes': evaluation.safety_notes or '',

            'attendance_commitment': evaluation.attendance_commitment,
            'attendance_notes': evaluation.attendance_notes or '',

            'leadership_skills': evaluation.leadership_skills,
            'leadership_notes': evaluation.leadership_notes or '',

            'problem_solving': evaluation.problem_solving,
            'problem_solving_notes': evaluation.problem_solving_notes or '',

            'general_comments': evaluation.general_comments or 'لا توجد ملاحظات',
            'overall_score': float(evaluation.overall_score),
            'avg_score': float(avg_score),
            'created_at': evaluation.created_at.strftime('%Y-%m-%d %H:%M') if evaluation.created_at else 'غير محدد'
        }

        return jsonify({
            'success': True,
            'data': evaluation_data
        })

    except Exception as e:
        app.logger.error(f"Error in get_supervisor_evaluation: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ في تحميل بيانات التقييم'
        }), 500

@app.route('/api/supervisors/company/<int:supervisor_id>')
@login_required
def get_supervisor_company(supervisor_id):
    """API للحصول على شركة مشرف معين"""
    try:
        supervisor = Employee.query.get(supervisor_id)
        if not supervisor or supervisor.position != 'supervisor':
            return jsonify({
                'success': False,
                'message': 'المشرف غير موجود'
            }), 404

        return jsonify({
            'success': True,
            'company_id': supervisor.company_id,
            'company_name': supervisor.company.name if supervisor.company else ''
        })

    except Exception as e:
        app.logger.error(f"Error in get_supervisor_company: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ في تحميل بيانات الشركة'
        }), 500

@app.route('/create-sample-places')
@login_required
def create_sample_places():
    """إنشاء أماكن تجريبية - النسخة التي يطلبها القالب"""
    if current_user.role != 'owner':
        flash('غير مصرح', 'error')
        return redirect(url_for('dashboard'))

    try:
        # البحث عن شركة موجودة أو إنشاء واحدة
        company = Company.query.first()
        if not company:
            company = Company(
                name='شركة النظافة',
                address='عنوان افتراضي',
                is_active=True
            )
            db.session.add(company)
            db.session.flush()

        # البحث عن منطقة موجودة أو إنشاء واحدة
        area = Area.query.first()
        if not area:
            area = Area(
                name='المنطقة الرئيسية',
                company_id=company.id,
                is_active=True
            )
            db.session.add(area)
            db.session.flush()

        # البحث عن موقع موجود أو إنشاء واحد
        location = Location.query.first()
        if not location:
            location = Location(
                name='المبنى الإداري',
                area_id=area.id,
                is_active=True
            )
            db.session.add(location)
            db.session.flush()

        # إنشاء أماكن تجريبية
        sample_places = [
            'المكتب الرئيسي',
            'قاعة الاجتماعات',
            'المطبخ',
            'دورات المياه',
            'الممرات',
            'المدخل الرئيسي',
            'غرفة الأرشيف',
            'المكتبة'
        ]

        created_count = 0
        for place_name in sample_places:
            existing_place = Place.query.filter_by(name=place_name).first()
            if not existing_place:
                place = Place(
                    name=place_name,
                    location_id=location.id,
                    is_active=True
                )
                db.session.add(place)
                created_count += 1

        db.session.commit()

        if created_count > 0:
            flash(f'تم إنشاء {created_count} مكان بنجاح', 'success')
        else:
            flash('جميع الأماكن موجودة مسبقاً', 'info')

        return redirect(url_for('add_evaluation'))

    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في إنشاء الأماكن: {str(e)}', 'error')
        return redirect(url_for('dashboard'))


@app.route('/api/my-evaluations')
@login_required
def get_my_evaluations():
    """API للحصول على التقييمات الخاصة بالمستخدم الحالي"""
    try:
        from sqlalchemy.orm import joinedload

        if current_user.role == 'worker' and current_user.employee_profile:
            # العامل: تقييماته فقط
            evaluations = CleaningEvaluation.query \
                .options(
                joinedload(CleaningEvaluation.place),
                joinedload(CleaningEvaluation.evaluator)
            ) \
                .filter(CleaningEvaluation.evaluated_employee_id == current_user.employee_profile.id) \
                .order_by(CleaningEvaluation.date.desc()) \
                .all()
        else:
            evaluations = []

        evaluations_data = []
        for evaluation in evaluations:
            eval_data = {
                'id': evaluation.id,
                'date': evaluation.date.strftime('%Y-%m-%d'),
                'place': evaluation.place.name if evaluation.place else 'غير محدد',
                'overall_score': float(evaluation.overall_score),
                'comments': evaluation.comments or 'لا توجد ملاحظات'
            }
            # إخفاء اسم المقيم للعامل
            if current_user.role != 'owner':
                eval_data['evaluator'] = 'الإدارة'
            else:
                eval_data['evaluator'] = evaluation.evaluator.full_name if evaluation.evaluator else 'غير محدد'

            evaluations_data.append(eval_data)

        return jsonify({
            'success': True,
            'data': evaluations_data,
            'count': len(evaluations_data)
        })

    except Exception as e:
        app.logger.error(f"Error in get_my_evaluations: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ في تحميل التقييمات'
        }), 500


# Reports

@app.route('/reports')
@login_required
def reports_index():
    """صفحة التقارير الرئيسية (محسنة بصلاحيات المشاهد)"""
    try:
        # الحصول على التقييمات المفلترة
        filtered_evaluations = get_filtered_evaluations(current_user)
        filtered_evaluation_ids = [e.id for e in filtered_evaluations]

        # إذا لم يكن هناك تقييمات، استخدم قائمة فارغة للاستعلامات اللاحقة
        if not filtered_evaluation_ids:
            filtered_evaluation_ids = [0]  # قيمة وهمية لتجنب أخطاء SQL

        # إحصائيات أساسية (مع الأخذ بالاعتبار التقييمات المفلترة فقط)
        total_evaluations = len(filtered_evaluations)

        # حساب متوسط التقييم (للتقييمات المفلترة فقط)
        if filtered_evaluation_ids:
            avg_score_result = db.session.query(db.func.avg(CleaningEvaluation.overall_score)) \
                .filter(CleaningEvaluation.id.in_(filtered_evaluation_ids)).scalar()
            avg_score = float(avg_score_result) if avg_score_result is not None else 0.0
        else:
            avg_score = 0.0

        # إحصائيات التقييمات لليوم (مع الفلترة)
        today = date.today()
        evaluations_today = len([e for e in filtered_evaluations if e.date == today]) if filtered_evaluations else 0

        # إحصائيات هذا الأسبوع (مع الفلترة)
        week_ago = today - timedelta(days=7)
        evaluations_this_week = len([e for e in filtered_evaluations if e.date >= week_ago]) if filtered_evaluations else 0

        # إحصائيات هذا الشهر (مع الفلترة)
        month_ago = today - timedelta(days=30)
        evaluations_this_month = len([e for e in filtered_evaluations if e.date >= month_ago]) if filtered_evaluations else 0

        # إحصائيات الموظفين (يمكن أن تبقى كما هي، أو يمكن فلترتها إذا لزم الأمر)
        total_employees = Employee.query.count() or 0
        active_employees = Employee.query.filter_by(is_active=True).count() or 0
        total_companies = Company.query.filter_by(is_active=True).count() or 0
        total_areas = Area.query.filter_by(is_active=True).count() or 0

        # إحصائيات الحضور (يجب فلترتها حسب الموظفين المسموح رؤيتهم)
        # هذا الجزء أكثر تعقيداً ويتطلب دالة مشابهة get_filtered_employees
        # للتبسيط، سأتركه كما هو الآن، لكن يجب تحسينه لاحقاً.
        present_today = Attendance.query.filter_by(date=today, status='present').count() or 0

        # حساب النسبة المئوية للنمو (بدون استخدام |)
        monthly_growth = 0
        if total_evaluations > 0:
            monthly_growth = int((evaluations_this_month / total_evaluations) * 100)

        # إنشاء قاموس الإحصائيات
        stats = {
            'total_employees': total_employees,
            'total_companies': total_companies,
            'total_evaluations': total_evaluations,
            'avg_score': avg_score,
            'total_zones': total_areas,
            'monthly_growth': monthly_growth
        }

        return render_template('reports/index.html',
                               today=today,
                               now=datetime.now(),
                               stats=stats,
                               total_employees=total_employees,
                               active_employees=active_employees,
                               total_companies=total_companies,
                               total_areas=total_areas,
                               total_evaluations=total_evaluations,
                               avg_score=avg_score,
                               evaluations_today=evaluations_today,
                               evaluations_this_week=evaluations_this_week,
                               evaluations_this_month=evaluations_this_month,
                               present_today=present_today)
    except Exception as e:
        app.logger.error(f"Error in reports_index: {str(e)}")
        # في حالة الخطأ، استخدم قالب آمن
        return render_template('reports/index.html',
                               today=date.today(),
                               now=datetime.now(),
                               stats={'total_employees': 0, 'total_companies': 0, 'total_evaluations': 0,
                                      'avg_score': 0, 'total_zones': 0, 'monthly_growth': 0},
                               total_employees=0,
                               active_employees=0,
                               total_companies=0,
                               total_areas=0,
                               total_evaluations=0,
                               avg_score=0,
                               evaluations_today=0,
                               evaluations_this_week=0,
                               evaluations_this_month=0,
                               present_today=0)

# ============================================
# مسارات التقارير الجديدة (بأسماء فريدة)
# ============================================

@app.route('/reports/employees-performance')
@login_required
def report_employees_performance():
    if not check_permission('can_view_performance'):
        flash('غير مصرح بعرض تقارير الأداء', 'error')
        return redirect(url_for('reports_index'))
    """تقرير أداء الموظفين الشامل"""
    try:
        employees = Employee.query.filter_by(is_active=True).all()

        employees_data = []
        performances = []

        for emp in employees:
            evaluations = CleaningEvaluation.query.filter_by(evaluated_employee_id=emp.id).all()
            if evaluations:
                avg_perf = sum(e.overall_score for e in evaluations) / len(evaluations) * 20
            else:
                avg_perf = 0

            performances.append(avg_perf)

            # تحديد اسم الوظيفة بالعربية
            if emp.position == 'supervisor':
                position_ar = 'مشرف'
            elif emp.position == 'monitor':
                position_ar = 'مراقب'
            elif emp.position == 'worker':
                position_ar = 'عامل'
            else:
                position_ar = emp.position

            employees_data.append({
                'id': emp.id,
                'full_name': emp.full_name,
                'position_ar': position_ar,
                'company': emp.company,
                'evaluations_count': len(evaluations),
                'performance': avg_perf,
                'attendance_rate': 95  # يمكن تحسينها لاحقاً
            })

        avg_performance = sum(performances) / len(performances) if performances else 0
        max_performance = max(performances) if performances else 0
        excellent_count = len([p for p in performances if p >= 90])
        improvement_needed = len([p for p in performances if p < 60])

        return render_template('reports/employees_performance.html',
                               employees=employees_data,
                               avg_performance=avg_performance,
                               max_performance=max_performance,
                               excellent_count=excellent_count,
                               improvement_needed=improvement_needed,
                               chart_labels=['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو'],
                               chart_data=[85, 88, 92, 87, 91, 94],
                               distribution_data=[excellent_count, 5, 3, 2, improvement_needed])
    except Exception as e:
        app.logger.error(f"Error in report_employees_performance: {str(e)}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))


@app.route('/reports/employees-efficiency')
@login_required
def report_employees_efficiency():
    if not check_permission('can_view_employee_efficiency'):
        flash('غير مصرح بعرض تقارير الكفاءة', 'error')
        return redirect(url_for('reports_index'))
    """تحليل كفاءة الموظفين"""
    try:
        employees = Employee.query.filter_by(is_active=True).all()

        high = 0
        medium = 0
        low = 0

        for emp in employees:
            evaluations = CleaningEvaluation.query.filter_by(evaluated_employee_id=emp.id).count()
            if evaluations > 10:
                high += 1
            elif evaluations > 5:
                medium += 1
            else:
                low += 1

        return render_template('reports/employees_efficiency.html',
                               high_efficiency=high,
                               medium_efficiency=medium,
                               low_efficiency=low,
                               productivity_rate=85,
                               efficiency_labels=['الكفاءة', 'الإنتاجية', 'الجودة', 'الالتزام', 'المبادرة'],
                               efficiency_data=[85, 90, 88, 92, 78])
    except Exception as e:
        app.logger.error(f"Error in report_employees_efficiency: {str(e)}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))


@app.route('/reports/top-employees')
@login_required
def report_top_employees():
    """تقرير أفضل الموظفين أداءً مع فلترة متقدمة"""
    if not check_permission('can_view_top_employees'):
        flash('غير مصرح بعرض تقرير أفضل الموظفين', 'error')
        return redirect(url_for('reports_index'))

    try:
        from models import Employee, CleaningEvaluation, Attendance, Company
        from datetime import datetime, date, timedelta
        from sqlalchemy import func

        today = date.today()

        # ============================================
        # 1. استقبال معاملات الفلترة
        # ============================================
        from_date_str = request.args.get('from_date', '')
        to_date_str = request.args.get('to_date', '')
        selected_year = request.args.get('year', type=int)
        selected_month = request.args.get('month', type=int)
        selected_company = request.args.get('company_id', type=int)

        # معالجة التواريخ
        if from_date_str and to_date_str:
            try:
                from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
                to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
            except:
                from_date = today - timedelta(days=30)
                to_date = today
        elif selected_year and selected_month:
            from_date = date(selected_year, selected_month, 1)
            if selected_month == 12:
                to_date = date(selected_year + 1, 1, 1) - timedelta(days=1)
            else:
                to_date = date(selected_year, selected_month + 1, 1) - timedelta(days=1)
        else:
            # افتراضي: آخر 30 يوم
            from_date = today - timedelta(days=30)
            to_date = today

        days_in_period = (to_date - from_date).days + 1

        # ============================================
        # 2. أسماء الأشهر للعرض
        # ============================================
        month_names = {
            1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
            5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
            9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
        }

        # السنوات المتاحة
        years = list(range(2020, today.year + 2))

        # ============================================
        # 3. جلب جميع الشركات
        # ============================================
        companies = Company.query.filter_by(is_active=True).order_by(Company.name).all()

        # ============================================
        # 4. بناء استعلام الموظفين
        # ============================================
        employees_query = Employee.query.filter_by(is_active=True)
        if selected_company:
            employees_query = employees_query.filter_by(company_id=selected_company)
        employees = employees_query.all()

        # ============================================
        # 5. حساب أداء كل موظف
        # ============================================
        employees_data = []
        total_performance = 0
        max_performance = 0
        total_evaluations = 0

        # تجميع أفضل موظف لكل شركة
        top_per_company = {}
        for company in companies:
            top_per_company[company.id] = {
                'company_name': company.name,
                'color': ['primary', 'success', 'info', 'warning', 'danger'][company.id % 5],
                'employee': None,
                'performance': 0
            }

        for employee in employees:
            # ============================================
            # أ. حساب التقييمات في الفترة
            # ============================================
            evaluations = CleaningEvaluation.query.filter(
                CleaningEvaluation.evaluated_employee_id == employee.id,
                CleaningEvaluation.date >= from_date,
                CleaningEvaluation.date <= to_date
            ).all()

            evaluations_count = len(evaluations)
            if evaluations_count > 0:
                avg_score = sum(e.overall_score for e in evaluations) / evaluations_count
                performance = avg_score * 20  # تحويل إلى نسبة مئوية
            else:
                performance = 0

            # ============================================
            # ب. حساب نسبة الحضور
            # ============================================
            attendance_records = Attendance.query.filter(
                Attendance.employee_id == employee.id,
                Attendance.date >= from_date,
                Attendance.date <= to_date
            ).all()

            present_days = len([a for a in attendance_records if a.status in ['present', 'late']])
            attendance_rate = round((present_days / days_in_period) * 100) if days_in_period > 0 else 0

            # ============================================
            # ج. تحديد اسم الوظيفة بالعربية
            # ============================================
            position_ar = {
                'supervisor': 'مشرف',
                'monitor': 'مراقب',
                'worker': 'عامل',
                'admin': 'إداري',
                'owner': 'مالك'
            }.get(employee.position, employee.position)

            # ============================================
            # د. بيانات الموظف
            # ============================================
            employee_info = {
                'id': employee.id,
                'full_name': employee.full_name,
                'position_ar': position_ar,
                'company_name': employee.company.name if employee.company else 'غير محدد',
                'company_id': employee.company_id,
                'avatar': None,
                'performance': round(performance, 1),
                'evaluations_count': evaluations_count,
                'attendance_rate': attendance_rate
            }

            employees_data.append(employee_info)

            # تحديث الإحصائيات العامة
            total_performance += performance
            if performance > max_performance:
                max_performance = performance
            total_evaluations += evaluations_count

            # تحديث أفضل موظف في الشركة
            if employee.company_id and performance > top_per_company[employee.company_id]['performance']:
                top_per_company[employee.company_id]['employee'] = employee_info
                top_per_company[employee.company_id]['performance'] = performance

        # ============================================
        # 6. ترتيب الموظفين تنازلياً حسب الأداء
        # ============================================
        employees_data.sort(key=lambda x: x['performance'], reverse=True)
        top_employees = employees_data[:20]  # أفضل 20 موظف

        # ============================================
        # 7. حساب متوسط الأداء
        # ============================================
        avg_performance = total_performance / len(employees_data) if employees_data else 0

        # ============================================
        # 8. تحويل top_per_company إلى قائمة
        # ============================================
        top_per_company_list = []
        for company_id, data in top_per_company.items():
            top_per_company_list.append(data)

        # ============================================
        # 9. بيانات الرسم البياني (توزيع المستويات)
        # ============================================
        levels = {
            'أسطورة (95%+)': 0,
            'ممتاز (90-94%)': 0,
            'جيد جداً (80-89%)': 0,
            'جيد (70-79%)': 0,
            'مقبول (<70%)': 0
        }

        for emp in employees_data:
            if emp['performance'] >= 95:
                levels['أسطورة (95%+)'] += 1
            elif emp['performance'] >= 90:
                levels['ممتاز (90-94%)'] += 1
            elif emp['performance'] >= 80:
                levels['جيد جداً (80-89%)'] += 1
            elif emp['performance'] >= 70:
                levels['جيد (70-79%)'] += 1
            else:
                levels['مقبول (<70%)'] += 1

        chart_data = [{'level': k, 'count': v} for k, v in levels.items() if v > 0]

        # ============================================
        # 10. تجهيز المتغيرات للقالب
        # ============================================
        context = {
            # بيانات الفلترة
            'from_date': from_date,
            'to_date': to_date,
            'from_date_str': from_date.strftime('%Y-%m-%d'),
            'to_date_str': to_date.strftime('%Y-%m-%d'),
            'selected_year': selected_year,
            'selected_month': selected_month,
            'selected_company': selected_company,
            'years': years,
            'months': month_names,  # ✅ هذا المتغير كان مفقوداً
            'companies': companies,
            'days_in_period': days_in_period,

            # بيانات الموظفين
            'top_employees': top_employees,
            'top_per_company': top_per_company_list,
            'total_employees': len(employees_data),
            'avg_performance': round(avg_performance, 1),
            'max_performance': round(max_performance, 1),
            'total_evaluations': total_evaluations,

            # بيانات الرسم البياني
            'chart_data': chart_data
        }

        return render_template('reports/top_employees.html', **context)

    except Exception as e:
        app.logger.error(f"Error in report_top_employees: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        flash(f'حدث خطأ في تحميل التقرير: {str(e)}', 'error')
        return redirect(url_for('reports_index'))


@app.route('/reports/attendance-record')
@login_required
def report_attendance_record():
    if not check_permission('can_view_attendance_reports'):
        flash('غير مصرح بعرض تقارير الحضور المتقدمة', 'error')
        return redirect(url_for('reports_index'))
    """تقرير سجل حضور الموظفين"""
    try:
        from datetime import datetime, date, timedelta

        selected_date = request.args.get('date', date.today().isoformat())
        try:
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except:
            selected_date = date.today()

        attendance_records = Attendance.query.filter_by(date=selected_date).all()

        present_count = len([a for a in attendance_records if a.status == 'present'])
        absent_count = len([a for a in attendance_records if a.status == 'absent'])
        late_count = len([a for a in attendance_records if a.status == 'late'])
        total = present_count + absent_count + late_count
        attendance_rate = (present_count / total * 100) if total > 0 else 0

        companies = Company.query.filter_by(is_active=True).all()
        employees = Employee.query.filter_by(is_active=True).all()

        return render_template('reports/attendance_record.html',
                               attendance_records=attendance_records,
                               selected_date=selected_date,
                               present_count=present_count,
                               absent_count=absent_count,
                               late_count=late_count,
                               attendance_rate=round(attendance_rate, 1),
                               companies=companies,
                               employees=employees,
                               selected_company=request.args.get('company', ''),
                               selected_employee=request.args.get('employee', ''))
    except Exception as e:
        app.logger.error(f"Error in report_attendance_record: {str(e)}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))


@app.route('/reports/late-employees')
@login_required
def report_late_employees():
    if not check_permission('can_view_attendance_reports'):
        flash('غير مصرح بعرض تقارير المتأخرين', 'error')
        return redirect(url_for('reports_index'))
    """تقرير الموظفين المتأخرون"""
    try:
        from datetime import date, timedelta

        late_employees = []
        thirty_days_ago = date.today() - timedelta(days=30)

        late_records = Attendance.query.filter(
            Attendance.status == 'late',
            Attendance.date >= thirty_days_ago
        ).all()

        late_counts = {}
        for record in late_records:
            if record.employee_id not in late_counts:
                late_counts[record.employee_id] = {
                    'count': 0,
                    'name': record.employee.full_name,
                    'department': record.employee.position,
                    'records': []
                }
            late_counts[record.employee_id]['count'] += 1
            late_counts[record.employee_id]['records'].append(record)

        for emp_id, data in late_counts.items():
            if data['count'] >= 2:  # من تأخروا مرتين على الأقل
                latest = data['records'][-1]
                late_employees.append({
                    'id': emp_id,
                    'name': data['name'],
                    'department': data['department'],
                    'late_date': latest.date.strftime('%Y-%m-%d'),
                    'check_in': latest.check_in.strftime('%H:%M') if latest.check_in else '-',
                    'late_minutes': 15,  # يمكن تحسينها لاحقاً
                    'late_count': data['count']
                })

        return render_template('reports/late_employees.html',
                               late_employees=late_employees[:10],
                               avg_late_minutes=18,
                               top_late_employee=late_employees[0]['name'] if late_employees else 'لا يوجد',
                               total_late_count=len(late_records))
    except Exception as e:
        app.logger.error(f"Error in report_late_employees: {str(e)}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))


@app.route('/reports/monthly-trends')
@login_required
def report_monthly_trends():
    """تقرير اتجاهات التقييم الشهرية"""
    try:
        from datetime import date, timedelta

        months = []
        evaluations_count = []

        for i in range(6):
            month_date = date.today() - timedelta(days=30 * i)
            month_name = month_date.strftime('%B')
            months.append(month_name)

            count = CleaningEvaluation.query.filter(
                CleaningEvaluation.date >= month_date - timedelta(days=30),
                CleaningEvaluation.date < month_date
            ).count()
            evaluations_count.append(count)

        return render_template('reports/monthly_trends.html',
                               months=months,
                               evaluations_count=evaluations_count)
    except Exception as e:
        app.logger.error(f"Error in report_monthly_trends: {str(e)}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))


@app.route('/reports/kpis')
@login_required
def report_kpis():
    if not check_permission('can_view_kpis'):
        flash('غير مصرح بعرض مؤشرات الأداء', 'error')
        return redirect(url_for('reports_index'))
    """تقرير مؤشرات الأداء الرئيسية"""
    try:
        total_employees = Employee.query.filter_by(is_active=True).count()
        total_evaluations = CleaningEvaluation.query.count()
        total_companies = Company.query.filter_by(is_active=True).count()

        kpis = {
            'employee_productivity': 85,
            'attendance_rate': 92,
            'evaluation_coverage': 78,
            'customer_satisfaction': 88,
            'task_completion': 82,
            'quality_score': 90
        }

        return render_template('reports/kpis.html',
                               kpis=kpis,
                               total_employees=total_employees,
                               total_evaluations=total_evaluations,
                               total_companies=total_companies)
    except Exception as e:
        app.logger.error(f"Error in report_kpis: {str(e)}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))




#تقارير التقييمات
@app.route('/reports/daily-evaluations-advanced')
@login_required
def report_daily_evaluations_advanced():
    if not check_permission('can_view_detailed_evaluations'):
        flash('غير مصرح بعرض تقييمات تفصيلية', 'error')
        return redirect(url_for('reports_index'))
    """تقرير التقييمات اليومية المتقدم - يعتمد على بيانات حقيقية ومفلترة"""
    try:
        app.logger.info("=" * 50)
        app.logger.info(f"📊 تقرير التقييمات اليومية المتقدم - المستخدم: {current_user.username}")

        today = date.today()
        selected_date_param = request.args.get('date', today.isoformat())

        try:
            selected_date = datetime.strptime(selected_date_param, '%Y-%m-%d').date()
        except ValueError:
            selected_date = today
            flash('صيغة التاريخ غير صحيحة، تم استخدام تاريخ اليوم', 'warning')

        # استخدام الدالة المساعدة لجلب جميع التقييمات المفلترة أولاً
        all_filtered_evaluations = get_filtered_evaluations(current_user)

        # ثم فلترتها حسب التاريخ المطلوب
        evaluations = [e for e in all_filtered_evaluations if e.date == selected_date]

        app.logger.info(f"📅 التاريخ: {selected_date}")
        app.logger.info(f"📊 عدد التقييمات في هذا التاريخ: {len(evaluations)}")

        # تجهيز بيانات التقييمات للعرض
        evaluations_data = []
        hourly_counts = [0, 0, 0, 0, 0]  # لفترات اليوم

        for eval_obj in evaluations:
            # اسم الموظف
            employee_name = "غير محدد"
            if eval_obj.evaluated_employee:
                employee_name = eval_obj.evaluated_employee.full_name

            # الموقع
            location_name = "غير محدد"
            if eval_obj.place:
                if eval_obj.place.location:
                    location_name = eval_obj.place.location.name
                else:
                    location_name = eval_obj.place.name

            # حساب الفترة الزمنية
            if eval_obj.created_at:
                hour = eval_obj.created_at.hour
                if 8 <= hour < 10:
                    hourly_counts[0] += 1
                elif 10 <= hour < 12:
                    hourly_counts[1] += 1
                elif 12 <= hour < 14:
                    hourly_counts[2] += 1
                elif 14 <= hour < 16:
                    hourly_counts[3] += 1
                elif 16 <= hour < 18:
                    hourly_counts[4] += 1

            evaluations_data.append({
                'id': eval_obj.id,
                'created_at': eval_obj.created_at or datetime.now(),
                'employee': {
                    'full_name': employee_name,
                    'avatar': None
                },
                'location': location_name,
                'cleanliness': eval_obj.cleanliness or 0,
                'organization': eval_obj.organization or 0,
                'equipment': eval_obj.equipment_condition or 0,
                'safety': eval_obj.safety_measures or 0,
                'overall_score': float(eval_obj.overall_score) if eval_obj.overall_score else 0
            })

        # إحصائيات يومية حقيقية
        total = len(evaluations)
        if total > 0:
            scores = [e.overall_score for e in evaluations if e.overall_score]
            avg_score = sum(scores) / len(scores) if scores else 0
            max_score = max(scores) if scores else 0
            excellent_count = len([e for e in evaluations if e.overall_score and e.overall_score >= 4.5])
            poor_count = len([e for e in evaluations if e.overall_score and e.overall_score <= 3])
            excellent_percent = round((excellent_count / total) * 100) if total > 0 else 0
            poor_percent = round((poor_count / total) * 100) if total > 0 else 0
        else:
            avg_score = 0
            max_score = 0
            excellent_count = 0
            poor_count = 0
            excellent_percent = 0
            poor_percent = 0

        # حساب التغيير عن الأمس (مع الأخذ بالاعتبار الفلترة)
        yesterday = selected_date - timedelta(days=1)
        yesterday_evaluations = [e for e in all_filtered_evaluations if e.date == yesterday]
        yesterday_count = len(yesterday_evaluations)

        trend = 0
        if yesterday_count > 0 and total > 0:
            trend = round(((total - yesterday_count) / yesterday_count) * 100)

        daily_stats = {
            'total': total,
            'avg_score': round(avg_score, 1),
            'max_score': round(max_score, 1),
            'excellent_count': excellent_count,
            'poor_count': poor_count,
            'excellent_percent': excellent_percent,
            'poor_percent': poor_percent,
            'trend': trend
        }

        # حساب متوسطات المعايير الحقيقية
        if total > 0:
            cleanliness_avg = sum(e.cleanliness for e in evaluations if e.cleanliness) / total
            organization_avg = sum(e.organization for e in evaluations if e.organization) / total
            equipment_avg = sum(e.equipment_condition for e in evaluations if e.equipment_condition) / total
            safety_avg = sum(e.safety_measures for e in evaluations if e.safety_measures) / total
        else:
            cleanliness_avg = organization_avg = equipment_avg = safety_avg = 0

        criteria_stats = [
            {'name': 'النظافة', 'avg': round(cleanliness_avg, 1),
             'color': 'success' if cleanliness_avg >= 4 else 'warning' if cleanliness_avg >= 3 else 'danger',
             'badge_color': 'success' if cleanliness_avg >= 4 else 'warning' if cleanliness_avg >= 3 else 'danger',
             'status': 'ممتاز' if cleanliness_avg >= 4.5 else 'جيد' if cleanliness_avg >= 3.5 else 'مقبول' if cleanliness_avg >= 2.5 else 'ضعيف'},
            {'name': 'التنظيم', 'avg': round(organization_avg, 1),
             'color': 'success' if organization_avg >= 4 else 'warning' if organization_avg >= 3 else 'danger',
             'badge_color': 'success' if organization_avg >= 4 else 'warning' if organization_avg >= 3 else 'danger',
             'status': 'ممتاز' if organization_avg >= 4.5 else 'جيد' if organization_avg >= 3.5 else 'مقبول' if organization_avg >= 2.5 else 'ضعيف'},
            {'name': 'المعدات', 'avg': round(equipment_avg, 1),
             'color': 'success' if equipment_avg >= 4 else 'warning' if equipment_avg >= 3 else 'danger',
             'badge_color': 'success' if equipment_avg >= 4 else 'warning' if equipment_avg >= 3 else 'danger',
             'status': 'ممتاز' if equipment_avg >= 4.5 else 'جيد' if equipment_avg >= 3.5 else 'مقبول' if equipment_avg >= 2.5 else 'ضعيف'},
            {'name': 'السلامة', 'avg': round(safety_avg, 1),
             'color': 'success' if safety_avg >= 4 else 'warning' if safety_avg >= 3 else 'danger',
             'badge_color': 'success' if safety_avg >= 4 else 'warning' if safety_avg >= 3 else 'danger',
             'status': 'ممتاز' if safety_avg >= 4.5 else 'جيد' if safety_avg >= 3.5 else 'مقبول' if safety_avg >= 2.5 else 'ضعيف'}
        ]

        # توزيع التقييمات
        distribution_data = [
            excellent_count,
            len([e for e in evaluations if e.overall_score and 3.5 <= e.overall_score < 4.5]),
            len([e for e in evaluations if e.overall_score and 2.5 <= e.overall_score < 3.5]),
            poor_count
        ]

        # توصيات ذكية مبنية على البيانات
        recommendations = []
        if cleanliness_avg < 3.5:
            recommendations.append({
                'type': 'danger',
                'icon': 'broom',
                'title': 'تحسين النظافة',
                'message': 'معدل النظافة منخفض، يحتاج إلى متابعة مكثفة'
            })
        if organization_avg < 3.5:
            recommendations.append({
                'type': 'warning',
                'icon': 'clipboard',
                'title': 'تنظيم العمل',
                'message': 'التنظيم يحتاج إلى تحسين، يرجى مراجعة إجراءات العمل'
            })
        if excellent_count > poor_count:
            recommendations.append({
                'type': 'success',
                'icon': 'trophy',
                'title': 'أداء متميز',
                'message': f'عدد التقييمات الممتازة ({excellent_count}) يفوق الضعيفة ({poor_count})'
            })
        else:
            recommendations.append({
                'type': 'info',
                'icon': 'lightbulb',
                'title': 'فرصة للتحسين',
                'message': 'يوجد مجال لتحسين الأداء العام'
            })

        # إضافة توصية عامة
        if total == 0:
            recommendations.append({
                'type': 'info',
                'icon': 'info-circle',
                'title': 'لا توجد تقييمات لهذا اليوم',
                'message': 'لم يتم تسجيل أي تقييمات في هذا التاريخ'
            })

        app.logger.info(f"📊 تم تجهيز التقرير بنجاح")
        app.logger.info("=" * 50)

        return render_template('reports/daily_evaluations_advanced.html',
                               daily_stats=daily_stats,
                               evaluations=evaluations_data,
                               selected_date=selected_date.strftime('%Y-%m-%d'),
                               hourly_labels=['8-10', '10-12', '12-14', '14-16', '16-18'],
                               hourly_data=hourly_counts,
                               distribution_data=distribution_data,
                               criteria_stats=criteria_stats,
                               criteria_labels=['النظافة', 'التنظيم', 'المعدات', 'السلامة'],
                               criteria_averages=[cleanliness_avg, organization_avg, equipment_avg, safety_avg],
                               recommendations=recommendations[:3])  # أقصى 3 توصيات

    except Exception as e:
        app.logger.error(f"❌ Error in report_daily_evaluations_advanced: {str(e)}")
        import traceback
        app.logger.error(f"🔍 تفاصيل الخطأ: {traceback.format_exc()}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))


@app.route('/reports/evaluation-details-advanced')
@login_required
def report_evaluation_details_advanced():
    """تقرير تفاصيل التقييمات حسب المعايير - يعتمد على بيانات حقيقية ومفلترة"""
    try:
        app.logger.info("=" * 50)
        app.logger.info(f"📊 تقرير تفاصيل التقييمات - المستخدم: {current_user.username}")

        # استخدام الدالة المساعدة لجلب جميع التقييمات المفلترة
        all_evaluations = get_filtered_evaluations(current_user)
        total_evaluations = len(all_evaluations)

        app.logger.info(f"📊 إجمالي التقييمات المفلترة: {total_evaluations}")

        if total_evaluations == 0:
            # بيانات افتراضية عند عدم وجود تقييمات
            criteria = [
                {'name': 'النظافة', 'avg': 0, 'color': 'secondary', 'max': 0, 'min': 0},
                {'name': 'التنظيم', 'avg': 0, 'color': 'secondary', 'max': 0, 'min': 0},
                {'name': 'المعدات', 'avg': 0, 'color': 'secondary', 'max': 0, 'min': 0},
                {'name': 'السلامة', 'avg': 0, 'color': 'secondary', 'max': 0, 'min': 0},
            ]
            criteria_details = []
            for c in criteria:
                criteria_details.append({
                    'name': c['name'],
                    'excellent': 0,
                    'good': 0,
                    'average': 0,
                    'poor': 0,
                    'very_poor': 0,
                    'total': 0
                })
        else:
            # حساب إحصائيات النظافة
            cleanliness_values = [e.cleanliness for e in all_evaluations if e.cleanliness]
            cleanliness_avg = sum(cleanliness_values) / len(cleanliness_values) if cleanliness_values else 0
            cleanliness_max = max(cleanliness_values) if cleanliness_values else 0
            cleanliness_min = min(cleanliness_values) if cleanliness_values else 0

            # حساب إحصائيات التنظيم
            organization_values = [e.organization for e in all_evaluations if e.organization]
            organization_avg = sum(organization_values) / len(organization_values) if organization_values else 0
            organization_max = max(organization_values) if organization_values else 0
            organization_min = min(organization_values) if organization_values else 0

            # حساب إحصائيات المعدات
            equipment_values = [e.equipment_condition for e in all_evaluations if e.equipment_condition]
            equipment_avg = sum(equipment_values) / len(equipment_values) if equipment_values else 0
            equipment_max = max(equipment_values) if equipment_values else 0
            equipment_min = min(equipment_values) if equipment_values else 0

            # حساب إحصائيات الوقت
            time_values = [e.time for e in all_evaluations if e.time]
            time_avg = sum(time_values) / len(time_values) if time_values else 0
            time_max = max(time_values) if time_values else 0
            time_min = min(time_values) if time_values else 0

            # حساب إحصائيات السلامة
            safety_values = [e.safety_measures for e in all_evaluations if e.safety_measures]
            safety_avg = sum(safety_values) / len(safety_values) if safety_values else 0
            safety_max = max(safety_values) if safety_values else 0
            safety_min = min(safety_values) if safety_values else 0

            criteria = [
                {'name': 'النظافة', 'avg': round(cleanliness_avg, 1),
                 'color': 'success' if cleanliness_avg >= 4 else 'warning' if cleanliness_avg >= 3 else 'danger',
                 'max': cleanliness_max, 'min': cleanliness_min},
                {'name': 'التنظيم', 'avg': round(organization_avg, 1),
                 'color': 'success' if organization_avg >= 4 else 'warning' if organization_avg >= 3 else 'danger',
                 'max': organization_max, 'min': organization_min},
                {'name': 'المعدات', 'avg': round(equipment_avg, 1),
                 'color': 'success' if equipment_avg >= 4 else 'warning' if equipment_avg >= 3 else 'danger',
                 'max': equipment_max, 'min': equipment_min},
                {'name': 'الوقت', 'avg': round(time_avg, 1),
                 'color': 'success' if time_avg >= 4 else 'warning' if time_avg >= 3 else 'danger',
                 'max': time_max, 'min': time_min},
                {'name': 'السلامة', 'avg': round(safety_avg, 1),
                 'color': 'success' if safety_avg >= 4 else 'warning' if safety_avg >= 3 else 'danger',
                 'max': safety_max, 'min': safety_min},
            ]

            # تفاصيل المعايير
            criteria_details = []
            for criterion_name in ['النظافة', 'التنظيم', 'المعدات', 'الوقت', 'السلامة']:
                excellent = good = average = poor = very_poor = 0

                for eval_obj in all_evaluations:
                    value = None
                    if criterion_name == 'النظافة':
                        value = eval_obj.cleanliness
                    elif criterion_name == 'التنظيم':
                        value = eval_obj.organization
                    elif criterion_name == 'المعدات':
                        value = eval_obj.equipment_condition
                    elif criterion_name == 'الوقت':
                        value = eval_obj.time
                    elif criterion_name == 'السلامة':
                        value = eval_obj.safety_measures

                    if value == 5:
                        excellent += 1
                    elif value == 4:
                        good += 1
                    elif value == 3:
                        average += 1
                    elif value == 2:
                        poor += 1
                    elif value == 1:
                        very_poor += 1

                criteria_details.append({
                    'name': criterion_name,
                    'excellent': excellent,
                    'good': good,
                    'average': average,
                    'poor': poor,
                    'very_poor': very_poor,
                    'total': excellent + good + average + poor + very_poor
                })

        app.logger.info(f"📊 تم تجهيز تفاصيل {len(criteria)} معايير")
        app.logger.info("=" * 50)

        return render_template('reports/evaluation_details.html',
                               criteria=criteria,
                               criteria_names=[c['name'] for c in criteria],
                               criteria_averages=[c['avg'] for c in criteria],
                               criteria_max=[c['max'] for c in criteria],
                               criteria_min=[c['min'] for c in criteria],
                               criteria_details=criteria_details)

    except Exception as e:
        app.logger.error(f"❌ Error in report_evaluation_details_advanced: {str(e)}")
        import traceback
        app.logger.error(f"🔍 تفاصيل الخطأ: {traceback.format_exc()}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))


@app.route('/reports/kpis-advanced')
@login_required
def report_kpis_advanced():
    if not check_permission('can_view_kpis'):
        flash('غير مصرح بعرض مؤشرات الأداء', 'error')
        return redirect(url_for('reports_index'))

    """تقرير مؤشرات الأداء الرئيسية - مع دعم الفلاتر المتقدمة"""
    try:
        from models import Employee, CleaningEvaluation, Attendance, Company, Penalty, Overtime, Payroll
        from sqlalchemy import func
        from datetime import date, timedelta, datetime

        today = date.today()

        # ============================================
        # 1. استقبال معاملات الفلترة
        # ============================================
        from_date_str = request.args.get('from_date', '')
        to_date_str = request.args.get('to_date', '')
        company_id = request.args.get('company_id', type=int)
        quick = request.args.get('quick', '')

        # معالجة التواريخ بناءً على الفلترة
        if from_date_str and to_date_str:
            try:
                from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
                to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
            except:
                from_date = today
                to_date = today
        elif quick:
            # اختصارات سريعة
            if quick == 'today':
                from_date = today
                to_date = today
            elif quick == 'week':
                from_date = today - timedelta(days=today.weekday())
                to_date = today
            elif quick == 'month':
                from_date = date(today.year, today.month, 1)
                to_date = today
            elif quick == 'quarter':
                # حساب بداية الربع الحالي
                quarter = (today.month - 1) // 3 + 1
                from_date = date(today.year, (quarter - 1) * 3 + 1, 1)
                to_date = today
            elif quick == 'year':
                from_date = date(today.year, 1, 1)
                to_date = today
            else:
                from_date = today - timedelta(days=30)
                to_date = today
        else:
            # افتراضي: آخر 30 يوم
            from_date = today - timedelta(days=30)
            to_date = today

        days_in_period = (to_date - from_date).days + 1

        # ============================================
        # 2. قائمة الشركات للفلترة
        # ============================================
        companies = Company.query.filter_by(is_active=True).order_by(Company.name).all()

        # اسم الشركة المحددة للعرض
        selected_company_name = ''
        if company_id:
            selected_company = Company.query.get(company_id)
            if selected_company:
                selected_company_name = selected_company.name

        # ============================================
        # 3. بناء استعلام الموظفين مع فلترة الشركة
        # ============================================
        employees_query = Employee.query.filter_by(is_active=True)
        if company_id:
            employees_query = employees_query.filter_by(company_id=company_id)
        employees = employees_query.all()
        total_employees = len(employees)

        # قائمة معرفات الموظفين للفلترة
        employee_ids = [e.id for e in employees]

        # ============================================
        # 4. إحصائيات التقييمات في الفترة
        # ============================================
        evaluations_query = CleaningEvaluation.query

        if company_id and employee_ids:
            evaluations_query = evaluations_query.filter(
                CleaningEvaluation.evaluated_employee_id.in_(employee_ids)
            )

        evaluations_in_period = evaluations_query.filter(
            CleaningEvaluation.date >= from_date,
            CleaningEvaluation.date <= to_date
        ).all()

        total_evaluations = len(evaluations_in_period)

        # متوسط التقييم في الفترة
        if total_evaluations > 0:
            avg_score = sum(e.overall_score for e in evaluations_in_period) / total_evaluations
        else:
            avg_score = 0

        # ============================================
        # 5. إحصائيات الحضور في الفترة
        # ============================================
        attendance_query = Attendance.query

        if company_id and employee_ids:
            attendance_query = attendance_query.filter(Attendance.employee_id.in_(employee_ids))

        attendance_in_period = attendance_query.filter(
            Attendance.date >= from_date,
            Attendance.date <= to_date
        ).all()

        present_count = len([a for a in attendance_in_period if a.status == 'present'])
        late_count = len([a for a in attendance_in_period if a.status == 'late'])
        absent_count = len([a for a in attendance_in_period if a.status == 'absent'])
        total_attendance = len(attendance_in_period)

        # معدل الحضور
        attendance_rate = 0
        if total_attendance > 0:
            attendance_rate = round((present_count / total_attendance) * 100, 1)

        # ============================================
        # 6. تغطية التقييمات (✅ تصحيح الخطأ هنا)
        # ============================================
        evaluated_employees = len(set(e.evaluated_employee_id for e in evaluations_in_period))
        evaluation_coverage = 0
        if total_employees > 0:
            evaluation_coverage = round((evaluated_employees / total_employees) * 100, 1)

        # ============================================
        # 7. جودة العمل
        # ============================================
        quality_score = round(avg_score * 20, 1) if avg_score else 0

        # ============================================
        # 8. إنتاجية الموظفين
        # ============================================
        if total_employees > 0:
            employee_productivity = round((total_evaluations / total_employees) * 10, 1)
            employee_productivity = min(employee_productivity, 100)
        else:
            employee_productivity = 0

        # ============================================
        # 9. رضا العملاء (تقييمات ممتازة)
        # ============================================
        excellent_evaluations = len([e for e in evaluations_in_period if e.overall_score >= 4.5])
        customer_satisfaction = 0
        if total_evaluations > 0:
            customer_satisfaction = round((excellent_evaluations / total_evaluations) * 100, 1)

        # ============================================
        # 10. إنجاز المهام
        # ============================================
        task_completion = evaluation_coverage

        # ============================================
        # 11. استخدام الوقت
        # ============================================
        if total_attendance > 0:
            time_utilization = round((present_count / total_attendance) * 100, 1)
        else:
            time_utilization = 0

        # ============================================
        # 12. تطوير المهارات
        # ============================================
        skill_development = customer_satisfaction

        # ============================================
        # 13. حساب نسب التغير (مقارنة بالفترة السابقة)
        # ============================================
        # الفترة السابقة بنفس الطول
        period_length = (to_date - from_date).days + 1
        prev_from_date = from_date - timedelta(days=period_length)
        prev_to_date = from_date - timedelta(days=1)

        # تقييمات الفترة السابقة
        prev_evaluations_query = CleaningEvaluation.query

        if company_id and employee_ids:
            prev_evaluations_query = prev_evaluations_query.filter(
                CleaningEvaluation.evaluated_employee_id.in_(employee_ids)
            )

        prev_evaluations = prev_evaluations_query.filter(
            CleaningEvaluation.date >= prev_from_date,
            CleaningEvaluation.date <= prev_to_date
        ).count()

        # حضور الفترة السابقة
        prev_attendance_query = Attendance.query

        if company_id and employee_ids:
            prev_attendance_query = prev_attendance_query.filter(Attendance.employee_id.in_(employee_ids))

        prev_attendance = prev_attendance_query.filter(
            Attendance.date >= prev_from_date,
            Attendance.date <= prev_to_date
        ).all()

        prev_present = len([a for a in prev_attendance if a.status == 'present'])
        prev_total = len(prev_attendance)
        prev_attendance_rate = round((prev_present / prev_total * 100), 1) if prev_total > 0 else 0

        # جودة الفترة السابقة
        prev_avg_query = db.session.query(func.avg(CleaningEvaluation.overall_score))

        if company_id and employee_ids:
            prev_avg_query = prev_avg_query.filter(
                CleaningEvaluation.evaluated_employee_id.in_(employee_ids)
            )

        prev_avg_result = prev_avg_query.filter(
            CleaningEvaluation.date >= prev_from_date,
            CleaningEvaluation.date <= prev_to_date
        ).scalar() or 0

        prev_quality = round(prev_avg_result * 20, 1) if prev_avg_result else 0

        # حساب نسب التغير
        if prev_evaluations > 0:
            productivity_change = round(((total_evaluations - prev_evaluations) / prev_evaluations) * 100, 1)
        else:
            productivity_change = 0

        quality_change = round(quality_score - prev_quality, 1)
        attendance_change = round(attendance_rate - prev_attendance_rate, 1)

        # ============================================
        # 14. تجميع مؤشرات الأداء
        # ============================================
        kpis = {
            'employee_productivity': employee_productivity,
            'attendance_rate': attendance_rate,
            'evaluation_coverage': evaluation_coverage,
            'customer_satisfaction': customer_satisfaction,
            'task_completion': task_completion,
            'quality_score': quality_score,
            'time_utilization': time_utilization,
            'skill_development': skill_development,
            'productivity_change': productivity_change,
            'quality_change': quality_change,
            'attendance_change': attendance_change
        }

        # ============================================
        # 15. أفضل الموظفين أداءً
        # ============================================
        employee_scores = []
        for employee in employees[:20]:  # حد أقصى 20 موظف
            emp_evaluations = [e for e in evaluations_in_period if e.evaluated_employee_id == employee.id]
            if emp_evaluations:
                emp_avg = sum(e.overall_score for e in emp_evaluations) / len(emp_evaluations)
                employee_scores.append({
                    'name': employee.full_name,
                    'department': employee.position,
                    'company': employee.company.name if employee.company else '-',
                    'score': emp_avg,
                    'score_percentage': round(emp_avg * 20, 1)
                })

        # ترتيب تنازلي
        employee_scores.sort(key=lambda x: x['score'], reverse=True)
        top_performers = employee_scores[:5]
        needs_improvement = [e for e in employee_scores if e['score'] < 3][:5]

        # ============================================
        # 16. بيانات الرسم البياني لآخر 6 أشهر
        # ============================================
        kpi_labels = []
        productivity_trend = []
        quality_trend = []
        attendance_trend = []

        for i in range(5, -1, -1):
            month_date = today - timedelta(days=30 * i)
            month_name = {
                1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
                5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
                9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
            }.get(month_date.month, f'شهر {month_date.month}')
            kpi_labels.append(month_name)

            # بداية ونهاية الشهر
            month_start = date(month_date.year, month_date.month, 1)
            if month_date.month == 12:
                month_end = date(month_date.year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(month_date.year, month_date.month + 1, 1) - timedelta(days=1)

            # إنتاجية الشهر
            month_evals_query = CleaningEvaluation.query

            if company_id and employee_ids:
                month_evals_query = month_evals_query.filter(
                    CleaningEvaluation.evaluated_employee_id.in_(employee_ids)
                )

            month_evals = month_evals_query.filter(
                CleaningEvaluation.date >= month_start,
                CleaningEvaluation.date <= month_end
            ).count()

            month_productivity = round((month_evals / total_employees) * 10, 1) if total_employees > 0 else 0
            productivity_trend.append(min(month_productivity, 100))

            # جودة الشهر
            month_avg_query = db.session.query(func.avg(CleaningEvaluation.overall_score))

            if company_id and employee_ids:
                month_avg_query = month_avg_query.filter(
                    CleaningEvaluation.evaluated_employee_id.in_(employee_ids)
                )

            month_avg_result = month_avg_query.filter(
                CleaningEvaluation.date >= month_start,
                CleaningEvaluation.date <= month_end
            ).scalar() or 0

            month_quality = round(month_avg_result * 20, 1) if month_avg_result else 0
            quality_trend.append(month_quality)

            # حضور الشهر
            month_att_query = Attendance.query

            if company_id and employee_ids:
                month_att_query = month_att_query.filter(Attendance.employee_id.in_(employee_ids))

            month_att = month_att_query.filter(
                Attendance.date >= month_start,
                Attendance.date <= month_end,
                Attendance.status == 'present'
            ).count()

            month_total = month_att_query.filter(
                Attendance.date >= month_start,
                Attendance.date <= month_end
            ).count()

            month_attendance = round((month_att / month_total * 100), 1) if month_total > 0 else 0
            attendance_trend.append(month_attendance)

        # ============================================
        # 17. توزيع مستويات الأداء
        # ============================================
        excellent_count = len([e for e in employee_scores if e['score'] >= 4.5])
        very_good_count = len([e for e in employee_scores if 4 <= e['score'] < 4.5])
        good_count = len([e for e in employee_scores if 3 <= e['score'] < 4])
        acceptable_count = len([e for e in employee_scores if 2 <= e['score'] < 3])
        poor_count = len([e for e in employee_scores if e['score'] < 2])

        return render_template('reports/kpis.html',
                               kpis=kpis,
                               companies=companies,
                               selected_company=company_id,
                               selected_company_name=selected_company_name,
                               from_date=from_date,
                               to_date=to_date,
                               from_date_str=from_date.strftime('%Y-%m-%d'),
                               to_date_str=to_date.strftime('%Y-%m-%d'),
                               days_in_period=days_in_period,
                               total_employees=total_employees,
                               total_evaluations=total_evaluations,
                               total_companies=len(companies),
                               avg_score=round(avg_score, 2),
                               present_count=present_count,
                               late_count=late_count,
                               absent_count=absent_count,
                               attendance_rate_today=attendance_rate,
                               evaluated_employees=evaluated_employees,
                               excellent_evaluations=excellent_evaluations,
                               top_performers=top_performers,
                               needs_improvement=needs_improvement,
                               excellent_count=excellent_count,
                               very_good_count=very_good_count,
                               good_count=good_count,
                               acceptable_count=acceptable_count,
                               poor_count=poor_count,
                               kpi_labels=kpi_labels,
                               productivity_trend=productivity_trend,
                               quality_trend=quality_trend,
                               attendance_trend=attendance_trend)

    except Exception as e:
        app.logger.error(f"Error in report_kpis_advanced: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))

#تقييم الشركات والمناطق
@app.route('/reports/companies-zones')
@login_required
def report_companies_zones():
    """تقرير الشركات والمناطق مع الرسوم البيانية"""
    # التحقق من الصلاحية
    if not check_permission('can_view_companies'):
        flash('غير مصرح بعرض تقارير الشركات', 'error')
        return redirect(url_for('reports_index'))

    try:
        # الشركات النشطة فقط
        companies = Company.query.filter_by(is_active=True).all()

        # إحصائيات عامة
        total_companies = len(companies)
        active_companies = sum(1 for c in companies if c.is_active)

        # إحصائيات المناطق والمواقع
        total_areas = Area.query.filter_by(is_active=True).count()
        total_locations = Location.query.filter_by(is_active=True).count()
        total_places = Place.query.filter_by(is_active=True).count()

        # إحصائيات الموظفين
        total_employees_in_companies = Employee.query.filter_by(is_active=True).count()
        total_supervisors = Employee.query.filter_by(position='supervisor', is_active=True).count()

        # حساب المتوسطات
        avg_areas_per_company = total_areas / total_companies if total_companies > 0 else 0
        avg_locations_per_area = total_locations / total_areas if total_areas > 0 else 0

        # تجميع بيانات الشركات
        companies_data = []
        all_ratings = []

        for company in companies:
            # مناطق الشركة
            areas = Area.query.filter_by(company_id=company.id, is_active=True).all()
            areas_count = len(areas)

            # عدد الموظفين في الشركة
            employees_count = Employee.query.filter_by(company_id=company.id, is_active=True).count()

            # حساب تقييم الشركة
            ratings = []
            areas_list = []

            for area in areas:
                locations = Location.query.filter_by(area_id=area.id, is_active=True).all()
                locations_count = len(locations)

                # جمع مواقع المنطقة
                locations_list = []
                for location in locations:
                    places = Place.query.filter_by(location_id=location.id, is_active=True).all()
                    places_count = len(places)

                    # حساب تقييم الموقع
                    location_ratings = []
                    for place in places:
                        evals = CleaningEvaluation.query.filter_by(place_id=place.id).all()
                        for e in evals:
                            if e.overall_score:
                                location_ratings.append(e.overall_score)
                                ratings.append(e.overall_score)

                    locations_list.append({
                        'id': location.id,
                        'name': location.name,
                        'places_count': places_count,
                        'rating': sum(location_ratings) / len(location_ratings) if location_ratings else 0
                    })

                # ✅ إصلاح: حساب عدد العمال في المنطقة - من خلال المواقع والأماكن
                # بدلاً من البحث عن Employee.area_id (غير موجود)
                workers_count = 0
                for location in locations:
                    places_in_location = Place.query.filter_by(location_id=location.id, is_active=True).all()
                    for place in places_in_location:
                        if place.worker_id:  # إذا كان للمكان عامل معين
                            workers_count += 1

                # ✅ إصلاح: اسم المشرف - البحث في علاقة supervisor في نموذج Area
                supervisor_name = None
                if area.supervisor_id:
                    supervisor = Employee.query.get(area.supervisor_id)
                    if supervisor:
                        supervisor_name = supervisor.full_name

                # حساب تقييم المنطقة
                area_ratings = []
                for location in locations:
                    places = Place.query.filter_by(location_id=location.id, is_active=True).all()
                    for place in places:
                        evals = CleaningEvaluation.query.filter_by(place_id=place.id).all()
                        for e in evals:
                            if e.overall_score:
                                area_ratings.append(e.overall_score)

                area_rating = sum(area_ratings) / len(area_ratings) if area_ratings else 0

                areas_list.append({
                    'id': area.id,
                    'name': area.name,
                    'supervisor_name': supervisor_name,
                    'locations_count': locations_count,
                    'places_count': sum(l['places_count'] for l in locations_list),
                    'workers_count': workers_count,
                    'rating': area_rating,
                    'performance': min(100, (area_rating / 5) * 100) if area_rating else 0,
                    'locations': locations_list
                })

            # متوسط تقييم الشركة
            avg_rating = sum(ratings) / len(ratings) if ratings else 0
            all_ratings.extend(ratings)

            # حساب مؤشر الأداء
            performance = min(100, (avg_rating / 5) * 100) if avg_rating else 0

            # عدد المواقع في الشركة
            company_locations = sum(a['locations_count'] for a in areas_list)

            # عدد الأماكن في الشركة
            company_places = sum(a['places_count'] for a in areas_list)

            companies_data.append({
                'id': company.id,
                'name': company.name,
                'contact_person': company.contact_person,
                'color': f'#{hash(company.name) % 0xFFFFFF:06x}',
                'areas_count': areas_count,
                'locations_count': company_locations,
                'places_count': company_places,
                'employees_count': employees_count,
                'rating': avg_rating,
                'performance': performance,
                'performance_color': 'success' if performance >= 80 else 'warning' if performance >= 60 else 'danger',
                'is_active': company.is_active,
                'areas': areas_list
            })

        # ترتيب الشركات حسب التقييم
        companies_data.sort(key=lambda x: x['rating'], reverse=True)

        # حساب متوسط التقييم العام
        avg_company_rating = sum(all_ratings) / len(all_ratings) if all_ratings else 0

        # أعلى شركة تقييماً
        top_rated_company = companies_data[0]['name'] if companies_data else '-'

        # وقت التحديث
        from datetime import datetime
        now = datetime.now()

        return render_template('reports/companies_zones.html',
                               companies=companies_data,
                               companies_data=companies_data,  # للرسوم البيانية
                               total_companies=total_companies,
                               active_companies=active_companies,
                               total_areas=total_areas,
                               total_locations=total_locations,
                               total_places=total_places,
                               total_employees_in_companies=total_employees_in_companies,
                               total_supervisors=total_supervisors,
                               avg_areas_per_company=round(avg_areas_per_company, 1),
                               avg_locations_per_area=round(avg_locations_per_area, 1),
                               avg_company_rating=round(avg_company_rating, 1),
                               top_rated_company=top_rated_company,
                               now=now)

    except Exception as e:
        app.logger.error(f"Error in report_companies_zones: {str(e)}")
        import traceback
        app.logger.error(f"🔍 تفاصيل الخطأ: {traceback.format_exc()}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))

@app.route('/reports/employees-distribution')
@login_required
def report_employees_distribution():
    if not check_permission('can_view_companies'):
        flash('غير مصرح بعرض توزيع الموظفين', 'error')
        return redirect(url_for('reports_index'))
    """تقرير توزيع الموظفين على الشركات"""
    try:
        companies = Company.query.filter_by(is_active=True).all()
        distribution_data = []

        for company in companies:
            employees = Employee.query.filter_by(company_id=company.id, is_active=True).all()
            total = len(employees)
            supervisors = sum(1 for e in employees if e.position == 'supervisor')
            monitors = sum(1 for e in employees if e.position == 'monitor')
            workers = sum(1 for e in employees if e.position == 'worker')

            areas_count = Area.query.filter_by(company_id=company.id).count()

            distribution_data.append({
                'id': company.id,
                'name': company.name,
                'color': f'#{hash(company.name) % 0xFFFFFF:06x}',
                'total_employees': total,
                'supervisors': supervisors,
                'monitors': monitors,
                'workers': workers,
                'areas_count': areas_count
            })

        return render_template('reports/employees_distribution.html',
                               distribution_data=distribution_data)
    except Exception as e:
        app.logger.error(f"Error in report_employees_distribution: {str(e)}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))


@app.route('/reports/companies-ratings')
@login_required
def report_companies_ratings():
    """تقرير تقييم الشركات حسب المناطق"""
    if not check_permission('can_view_company_stats'):
        flash('غير مصرح بعرض تقييمات الشركات', 'error')
        return redirect(url_for('reports_index'))

    try:
        from models import Company, Area, Location, Place, CleaningEvaluation, Employee
        from sqlalchemy import func

        # جلب جميع الشركات النشطة
        companies = Company.query.filter_by(is_active=True).all()

        ratings_data = []
        areas_ratings = []

        for company in companies:
            # جلب مناطق الشركة
            areas = Area.query.filter_by(company_id=company.id, is_active=True).all()
            company_ratings = []

            for area in areas:
                # جلب تقييمات المنطقة
                area_ratings = []
                locations = Location.query.filter_by(area_id=area.id, is_active=True).all()

                for location in locations:
                    places = Place.query.filter_by(location_id=location.id, is_active=True).all()
                    for place in places:
                        evaluations = CleaningEvaluation.query.filter_by(place_id=place.id).all()
                        for e in evaluations:
                            if e.overall_score:
                                area_ratings.append(e.overall_score)
                                company_ratings.append(e.overall_score)

                # حساب متوسط تقييم المنطقة
                avg_rating = sum(area_ratings) / len(area_ratings) if area_ratings else 0
                last_evaluation = None
                if area_ratings and evaluations:
                    last_evaluation = max([e.date for e in evaluations if e.date])

                # إضافة المنطقة للتقرير التفصيلي
                if area_ratings:
                    areas_ratings.append({
                        'company_name': company.name,
                        'name': area.name,
                        'supervisor_name': area.supervisor.full_name if area.supervisor else None,
                        'evaluations_count': len(area_ratings),
                        'rating': avg_rating,
                        'last_evaluation_date': last_evaluation
                    })

            # حساب متوسط تقييم الشركة
            avg_company_rating = sum(company_ratings) / len(company_ratings) if company_ratings else 0

            # تحديد لون التقييم
            if avg_company_rating >= 4.5:
                rating_color = 'excellent'
            elif avg_company_rating >= 4:
                rating_color = 'good'
            elif avg_company_rating >= 3:
                rating_color = 'average'
            else:
                rating_color = 'poor'

            # تحديد أعلى وأدنى منطقة
            if areas_ratings:
                company_areas = [a for a in areas_ratings if a['company_name'] == company.name]
                if company_areas:
                    max_area = max(company_areas, key=lambda x: x['rating'])
                    min_area = min(company_areas, key=lambda x: x['rating'])
                    max_area_name = max_area['name']
                    min_area_name = min_area['name']
                    max_rating = round(max_area['rating'], 1)
                    min_rating = round(min_area['rating'], 1)
                else:
                    max_area_name = '-'
                    min_area_name = '-'
                    max_rating = 0
                    min_rating = 0
            else:
                max_area_name = '-'
                min_area_name = '-'
                max_rating = 0
                min_rating = 0

            ratings_data.append({
                'id': company.id,
                'name': company.name,
                'areas_count': len(areas),
                'avg_rating': round(avg_company_rating, 1),
                'rating_color': rating_color,
                'max_area': max_area_name,
                'max_rating': max_rating,
                'min_area': min_area_name,
                'min_rating': min_rating
            })

        # ترتيب الشركات حسب التقييم
        ratings_data.sort(key=lambda x: x['avg_rating'], reverse=True)

        return render_template('reports/companies_ratings.html',
                               ratings_data=ratings_data,
                               areas_ratings=areas_ratings)

    except Exception as e:
        app.logger.error(f"Error in report_companies_ratings: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        flash(f'حدث خطأ في تحميل التقرير: {str(e)}', 'error')
        return redirect(url_for('reports_index'))


@app.route('/reports/heatmap')
@login_required
def report_heatmap():
    """تقرير تحليل أداء المناطق والأماكن مع المعايير"""
    if not check_permission('can_view_heatmap'):
        flash('غير مصرح بعرض تحليل الأداء', 'error')
        return redirect(url_for('reports_index'))

    try:
        # بيانات المناطق النشطة
        areas = Area.query.filter_by(is_active=True).all()

        # إحصائيات المناطق
        excellent_zones = 0
        good_zones = 0
        average_zones = 0
        poor_zones = 0

        # قوائم المناطق حسب الأداء
        excellent_zones_list = []
        good_zones_list = []
        average_zones_list = []
        poor_zones_list = []

        # بيانات المناطق للرسوم البيانية
        zones_data = []

        # ✅ بيانات الأماكن مع المعايير (جديد)
        top_places = []

        # بيانات الشركات
        companies = Company.query.filter_by(is_active=True).all()
        companies_data = []

        # بيانات الاتجاهات الشهرية
        from datetime import datetime, timedelta
        import calendar

        # آخر 6 أشهر
        months_data = []
        excellent_trend = []
        good_trend = []
        poor_trend = []

        today = datetime.now()
        for i in range(5, -1, -1):
            month_date = today - timedelta(days=30 * i)
            month_name = calendar.month_name[month_date.month][:3] + f" {month_date.year}"
            months_data.append(month_name)

            # إحصائيات الشهر (محسوبة من البيانات الفعلية)
            month_start = month_date.replace(day=1)
            if month_date.month == 12:
                month_end = month_date.replace(year=month_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = month_date.replace(month=month_date.month + 1, day=1) - timedelta(days=1)

            # حساب عدد المناطق الممتازة في هذا الشهر
            month_excellent = 0
            month_good = 0
            month_poor = 0

            # هذا مثال، يمكن تحسينه بناءً على بياناتك الفعلية
            month_excellent = 3 + i * 0.3
            month_good = 5 + i * 0.2
            month_poor = max(0, 2 - i * 0.1)

            excellent_trend.append(month_excellent)
            good_trend.append(month_good)
            poor_trend.append(month_poor)

        trends_data = {
            'months': months_data,
            'excellent': [round(x, 1) for x in excellent_trend],
            'good': [round(x, 1) for x in good_trend],
            'poor': [round(x, 1) for x in poor_trend]
        }

        # تجميع بيانات المناطق
        for area in areas:
            # حساب أداء المنطقة
            ratings = []
            evaluations = []
            locations = Location.query.filter_by(area_id=area.id, is_active=True).all()

            total_places = 0
            total_workers = 0

            for location in locations:
                places = Place.query.filter_by(location_id=location.id, is_active=True).all()
                total_places += len(places)

                for place in places:
                    # عدد العمال في المكان
                    if place.worker_id:
                        total_workers += 1

                    evals = CleaningEvaluation.query.filter_by(place_id=place.id).order_by(
                        CleaningEvaluation.date.desc()).all()
                    for e in evals:
                        if e.overall_score:
                            ratings.append(e.overall_score)
                            evaluations.append({
                                'date': e.date,
                                'score': e.overall_score
                            })

            # متوسط التقييم
            avg_rating = sum(ratings) / len(ratings) if ratings else 0
            performance = avg_rating * 20  # تحويل من /5 إلى %

            # آخر تقييم
            last_evaluation = None
            if evaluations:
                last_evaluation = max(evaluations, key=lambda x: x['date'])['date']

            # اسم المشرف
            supervisor_name = None
            if area.supervisor_id:
                supervisor = Employee.query.get(area.supervisor_id)
                if supervisor:
                    supervisor_name = supervisor.full_name

            # اسم الشركة
            company_name = area.company.name if area.company else '-'

            # إضافة المنطقة إلى القائمة المناسبة
            zone_data = {
                'id': area.id,
                'name': area.name,
                'company_name': company_name,
                'supervisor_name': supervisor_name,
                'performance': round(performance, 1),
                'rating': round(avg_rating, 1),
                'evaluations_count': len(ratings),
                'places_count': total_places,
                'workers_count': total_workers,
                'last_evaluation': last_evaluation.strftime('%Y-%m-%d') if last_evaluation else '-'
            }

            zones_data.append(zone_data)

            # تصنيف المنطقة
            if performance >= 80:
                excellent_zones += 1
                excellent_zones_list.append(zone_data)
            elif performance >= 70:
                good_zones += 1
                good_zones_list.append(zone_data)
            elif performance >= 60:
                average_zones += 1
                average_zones_list.append(zone_data)
            else:
                poor_zones += 1
                poor_zones_list.append(zone_data)

        # ✅ تجميع بيانات الأماكن مع المعايير (جديد)
        all_places = Place.query.filter_by(is_active=True).limit(20).all()
        for place in all_places:
            # حساب متوسط كل معيار للمكان
            cleanliness_scores = []
            organization_scores = []
            equipment_scores = []
            safety_scores = []

            evals = CleaningEvaluation.query.filter_by(place_id=place.id).all()
            for e in evals:
                if e.cleanliness:
                    cleanliness_scores.append(e.cleanliness)
                if e.organization:
                    organization_scores.append(e.organization)
                if e.equipment_condition:
                    equipment_scores.append(e.equipment_condition)
                if e.safety_measures:
                    safety_scores.append(e.safety_measures)

            avg_cleanliness = sum(cleanliness_scores) / len(cleanliness_scores) if cleanliness_scores else 0
            avg_organization = sum(organization_scores) / len(organization_scores) if organization_scores else 0
            avg_equipment = sum(equipment_scores) / len(equipment_scores) if equipment_scores else 0
            avg_safety = sum(safety_scores) / len(safety_scores) if safety_scores else 0

            # متوسط التقييم العام
            all_scores = cleanliness_scores + organization_scores + equipment_scores + safety_scores
            avg_score = sum(all_scores) / len(all_scores) if all_scores else 0

            # اسم الموقع
            location_name = place.location.name if place.location else '-'

            top_places.append({
                'id': place.id,
                'name': place.name,
                'location_name': location_name,
                'avg_score': round(avg_score, 1),
                'cleanliness': round(avg_cleanliness, 1),
                'organization': round(avg_organization, 1),
                'equipment': round(avg_equipment, 1),
                'safety': round(avg_safety, 1),
                'evaluations_count': len(evals)
            })

        # ترتيب الأماكن حسب التقييم
        top_places.sort(key=lambda x: x['avg_score'], reverse=True)
        top_places = top_places[:12]  # أخذ أفضل 12 مكان

        # بيانات الشركات للمقارنة
        for company in companies:
            # حساب متوسط أداء الشركة
            company_areas = Area.query.filter_by(company_id=company.id, is_active=True).all()
            if not company_areas:
                continue

            company_performances = []
            for ca in company_areas:
                ca_ratings = []
                ca_locations = Location.query.filter_by(area_id=ca.id, is_active=True).all()
                for loc in ca_locations:
                    places = Place.query.filter_by(location_id=loc.id, is_active=True).all()
                    for p in places:
                        evals = CleaningEvaluation.query.filter_by(place_id=p.id).all()
                        ca_ratings.extend([e.overall_score for e in evals if e.overall_score])

                if ca_ratings:
                    ca_avg = sum(ca_ratings) / len(ca_ratings)
                    company_performances.append(ca_avg * 20)

            if company_performances:
                companies_data.append({
                    'name': company.name,
                    'avg_performance': round(sum(company_performances) / len(company_performances), 1)
                })

        # ترتيب المناطق حسب الأداء
        excellent_zones_list.sort(key=lambda x: x['performance'], reverse=True)
        good_zones_list.sort(key=lambda x: x['performance'], reverse=True)
        average_zones_list.sort(key=lambda x: x['performance'], reverse=True)
        poor_zones_list.sort(key=lambda x: x['performance'], reverse=True)

        # ترتيب المناطق للرسم البياني (أعلى 10)
        zones_data.sort(key=lambda x: x['performance'], reverse=True)
        top_zones = zones_data[:10]

        return render_template('reports/heatmap.html',
                               zones_data=top_zones,
                               companies_data=companies_data,
                               trends_data=trends_data,
                               top_places=top_places,  # ✅ المتغير الجديد
                               excellent_zones=excellent_zones,
                               good_zones=good_zones,
                               average_zones=average_zones,
                               poor_zones=poor_zones,
                               excellent_zones_list=excellent_zones_list,
                               good_zones_list=good_zones_list,
                               average_zones_list=average_zones_list,
                               poor_zones_list=poor_zones_list)

    except Exception as e:
        app.logger.error(f"Error in report_heatmap: {str(e)}")
        import traceback
        app.logger.error(f"🔍 تفاصيل الخطأ: {traceback.format_exc()}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))

#تقارير الحضور والانصراف
@app.route('/reports/attendance-record-advanced')
@login_required
def report_attendance_record_advanced():
    """تقرير سجل الحضور والانصراف المتقدم"""
    try:
        today = date.today()
        selected_date = request.args.get('date', today.isoformat())
        try:
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except:
            selected_date = today

        # التأكد من أن الاستعلام لا يرجع None
        attendance_records = Attendance.query.filter_by(date=selected_date).all() or []

        # إحصائيات اليوم
        present_today = len([a for a in attendance_records if a and a.status == 'present'])
        absent_today = len([a for a in attendance_records if a and a.status == 'absent'])
        late_today = len([a for a in attendance_records if a and a.status == 'late'])
        total_today = present_today + absent_today + late_today

        attendance_rate_today = 0
        absence_rate_today = 0
        if total_today > 0:
            attendance_rate_today = round((present_today / total_today * 100))
            absence_rate_today = round((absent_today / total_today * 100))

        # حساب متوسط التأخير
        late_minutes = []
        for record in attendance_records:
            if record and record.status == 'late' and record.check_in:
                try:
                    # حساب وقت التأخير (افتراضي 9 صباحاً)
                    scheduled = datetime.strptime('09:00', '%H:%M').time()
                    check_in = record.check_in
                    if check_in > scheduled:
                        diff = datetime.combine(today, check_in) - datetime.combine(today, scheduled)
                        late_minutes.append(diff.seconds // 60)
                except:
                    pass

        avg_late_minutes = 0
        if late_minutes:
            avg_late_minutes = round(sum(late_minutes) / len(late_minutes))

        # بيانات الرسم البياني لآخر 30 يوم
        dates = []
        daily_present = []
        daily_absent = []
        daily_late = []

        for i in range(30):
            day = today - timedelta(days=i)
            day_records = Attendance.query.filter_by(date=day).all() or []
            dates.append(day.strftime('%d/%m'))
            daily_present.append(len([r for r in day_records if r and r.status == 'present']))
            daily_absent.append(len([r for r in day_records if r and r.status == 'absent']))
            daily_late.append(len([r for r in day_records if r and r.status == 'late']))

        attendance_chart_data = {
            'dates': dates[::-1],
            'daily_present': daily_present[::-1],
            'daily_absent': daily_absent[::-1],
            'daily_late': daily_late[::-1]
        }

        # تجهيز بيانات الجدول
        attendance_data = []
        for record in attendance_records:
            if not record:
                continue

            late_minutes = 0
            if record.status == 'late' and record.check_in:
                try:
                    scheduled = datetime.strptime('09:00', '%H:%M').time()
                    if record.check_in > scheduled:
                        diff = datetime.combine(today, record.check_in) - datetime.combine(today, scheduled)
                        late_minutes = diff.seconds // 60
                except:
                    pass

            # الحصول على بيانات الموظف بأمان
            employee_name = record.employee.full_name if record.employee else 'غير معروف'
            employee_position = record.employee.position if record.employee else ''
            employee_company = record.employee.company.name if record.employee and record.employee.company else '-'

            attendance_data.append({
                'id': record.id,
                'employee': {
                    'full_name': employee_name,
                    'position_ar': employee_position,
                    'color': f'#{hash(employee_name) % 0xFFFFFF:06x}',
                    'department': employee_position,
                    'company_name': employee_company
                },
                'date': record.date,
                'check_in': record.check_in,
                'check_out': record.check_out,
                'status': record.status,
                'late_minutes': late_minutes,
                'notes': record.notes or ''
            })

        companies = Company.query.filter_by(is_active=True).all() or []
        employees = Employee.query.filter_by(is_active=True).all() or []

        active_employees_count = Employee.query.filter_by(is_active=True).count() or 0
        total_employees_count = Employee.query.count() or 0

        return render_template('reports/attendance_record_advanced.html',
                               present_today=present_today,
                               absent_today=absent_today,
                               late_today=late_today,
                               attendance_rate_today=attendance_rate_today,
                               absence_rate_today=absence_rate_today,
                               avg_late_minutes=avg_late_minutes,
                               active_employees=active_employees_count,
                               total_employees=total_employees_count,
                               attendance_records=attendance_data,
                               attendance_chart_data=attendance_chart_data,
                               selected_date=selected_date,
                               companies=companies,
                               employees=employees,
                               selected_company=request.args.get('company', ''),
                               selected_employee=request.args.get('employee', ''),
                               today=today)
    except Exception as e:
        app.logger.error(f"Error in report_attendance_record_advanced: {str(e)}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))


@app.route('/reports/monthly-summary')
@login_required
def report_monthly_summary():
    if not check_permission('can_view_attendance_reports'):
        flash('غير مصرح بعرض الملخص الشهري', 'error')
        return redirect(url_for('reports_index'))
    """تقرير ملخص الحضور الشهري"""
    try:
        year = request.args.get('year', date.today().year, type=int)
        month = request.args.get('month', date.today().month, type=int)

        month_names = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
                       'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']

        years = list(range(2020, date.today().year + 1))
        months = [{'number': i + 1, 'name': month_names[i]} for i in range(12)]

        # حساب أيام العمل في الشهر
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)

        working_days = month_end.day

        # إحصائيات الشهر
        month_records = Attendance.query.filter(
            Attendance.date >= month_start,
            Attendance.date <= month_end
        ).all()

        total_present = len([r for r in month_records if r.status == 'present'])
        total_absent = len([r for r in month_records if r.status == 'absent'])
        total_late = len([r for r in month_records if r.status == 'late'])

        monthly_attendance_rate = round((total_present / (total_present + total_absent + total_late) * 100)
                                        if (total_present + total_absent + total_late) > 0 else 0)

        # بيانات الرسم البياني اليومي
        daily_present = []
        days_labels = []
        for day in range(1, working_days + 1):
            current_date = date(year, month, day)
            day_records = Attendance.query.filter_by(date=current_date).all()
            daily_present.append(len([r for r in day_records if r.status == 'present']))
            days_labels.append(str(day))

        # ملخص الموظفين
        monthly_summary = []
        employees = Employee.query.filter_by(is_active=True).all()
        for emp in employees:
            emp_records = Attendance.query.filter(
                Attendance.employee_id == emp.id,
                Attendance.date >= month_start,
                Attendance.date <= month_end
            ).all()

            present_days = len([r for r in emp_records if r.status == 'present'])
            absent_days = len([r for r in emp_records if r.status == 'absent'])
            late_days = len([r for r in emp_records if r.status == 'late'])

            attendance_rate = round((present_days / working_days * 100) if working_days > 0 else 0)

            monthly_summary.append({
                'name': emp.full_name,
                'color': f'#{hash(emp.full_name) % 0xFFFFFF:06x}',
                'department': emp.position,
                'present_days': present_days,
                'absent_days': absent_days,
                'late_days': late_days,
                'attendance_rate': attendance_rate
            })

        return render_template('reports/monthly_summary.html',
                               years=years,
                               months=months,
                               selected_year=year,
                               selected_month=month,
                               working_days=working_days,
                               total_present=total_present,
                               total_absent=total_absent,
                               total_late=total_late,
                               monthly_attendance_rate=monthly_attendance_rate,
                               daily_present_data=daily_present,
                               days_labels=days_labels,
                               monthly_summary=monthly_summary)
    except Exception as e:
        app.logger.error(f"Error in report_monthly_summary: {str(e)}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))


@app.route('/reports/absence-rates')
@login_required
def report_absence_rates():
    """تقرير نسب الغياب والتأخير"""
    try:
        employees = Employee.query.filter_by(is_active=True).all() or []

        # حساب الإحصائيات
        total_records = Attendance.query.count() or 1  # تجنب القسمة على صفر
        total_absent = Attendance.query.filter_by(status='absent').count() or 0
        total_late = Attendance.query.filter_by(status='late').count() or 0

        avg_absence_rate = round((total_absent / total_records * 100)) if total_records > 0 else 0
        avg_late_rate = round((total_late / total_records * 100)) if total_records > 0 else 0

        # الموظف الأكثر غياباً
        absence_counts = {}
        for emp in employees:
            if emp:
                count = Attendance.query.filter_by(employee_id=emp.id, status='absent').count() or 0
                if count > 0:
                    absence_counts[emp.full_name or 'غير معروف'] = count

        top_absent = max(absence_counts.items(), key=lambda x: x[1]) if absence_counts else ('لا يوجد', 0)

        # قائمة الأكثر غياباً
        top_absent_employees = []
        for emp in employees:
            if not emp:
                continue

            absent_days = Attendance.query.filter_by(employee_id=emp.id, status='absent').count() or 0
            late_days = Attendance.query.filter_by(employee_id=emp.id, status='late').count() or 0

            if absent_days > 0:
                last_absence = Attendance.query.filter_by(employee_id=emp.id, status='absent') \
                    .order_by(Attendance.date.desc()).first()

                top_absent_employees.append({
                    'id': emp.id,
                    'name': emp.full_name or 'غير معروف',
                    'color': f'#{hash(emp.full_name or "") % 0xFFFFFF:06x}',
                    'department': emp.position or 'غير محدد',
                    'absent_days': absent_days,
                    'absence_rate': round((absent_days / 30 * 100)) if absent_days > 0 else 0,
                    'late_days': late_days,
                    'last_absence': last_absence.date if last_absence else None
                })

        # ترتيب تنازلي
        top_absent_employees.sort(key=lambda x: x['absent_days'], reverse=True)

        # بيانات الرسم البياني
        months = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو']
        absence_trend = [8, 10, 7, 12, 9, 11]
        absence_reasons = [45, 25, 15, 10, 5]  # مرضي، شخصي، غير مبرر، إجازة، أخرى

        return render_template('reports/absence_rates.html',
                               avg_absence_rate=avg_absence_rate,
                               avg_late_rate=avg_late_rate,
                               top_absent_employee=top_absent[0],
                               top_absent_days=top_absent[1],
                               top_absent_employees=top_absent_employees[:10],
                               months_labels=months,
                               absence_trend_data=absence_trend,
                               absence_reasons_data=absence_reasons)
    except Exception as e:
        app.logger.error(f"Error in report_absence_rates: {str(e)}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))


@app.route('/api/reports/statistics')
@login_required
def reports_statistics():
    """API للحصول على إحصائيات التقارير (مع الفلترة)"""
    try:
        # الحصول على التقييمات المفلترة
        filtered_evaluations = get_filtered_evaluations(current_user)
        filtered_evaluation_ids = [e.id for e in filtered_evaluations]

        if not filtered_evaluation_ids:
            filtered_evaluation_ids = [0]

        total_evaluations = len(filtered_evaluations)

        if filtered_evaluation_ids and filtered_evaluation_ids != [0]:
            avg_score_result = db.session.query(db.func.avg(CleaningEvaluation.overall_score)) \
                .filter(CleaningEvaluation.id.in_(filtered_evaluation_ids)).scalar()
            avg_score = float(avg_score_result) if avg_score_result is not None else 0
        else:
            avg_score = 0

        excellent_count = len([e for e in filtered_evaluations if e.overall_score and e.overall_score >= 4.5])
        improvement_count = len([e for e in filtered_evaluations if e.overall_score and e.overall_score < 3])

        return jsonify({
            'success': True,
            'total_evaluations': total_evaluations,
            'avg_score': float(avg_score),
            'excellent_count': excellent_count,
            'improvement_count': improvement_count
        })
    except Exception as e:
        app.logger.error(f"❌ Error in reports_statistics: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ في تحميل الإحصائيات'
        }), 500

# ============================================
# مسارات تقارير المشرفين
# ============================================

@app.route('/reports/supervisor-performance')
@login_required
def report_supervisor_performance():
    """تقرير أداء المشرفين الشامل"""
    try:
        # الحصول على جميع المشرفين النشطين
        supervisors = Employee.query.filter_by(position='supervisor', is_active=True).all()

        supervisors_data = []
        total_ratings = []
        performance_trend = []

        for sup in supervisors:
            # الحصول على تقييمات المشرف
            evaluations = SupervisorEvaluation.query.filter_by(supervisor_id=sup.id).all()

            if evaluations:
                # حساب متوسطات المعايير
                workers_followup = sum(e.workers_followup for e in evaluations) / len(evaluations) * 20
                work_efficiency = sum(e.work_efficiency for e in evaluations) / len(evaluations) * 20
                reports_quality = sum(e.reports_submission for e in evaluations) / len(evaluations) * 20
                compliance = sum(e.policies_compliance for e in evaluations) / len(evaluations) * 20
                safety = sum(e.safety_procedures for e in evaluations) / len(evaluations) * 20
                attendance = sum(e.attendance_commitment for e in evaluations) / len(evaluations) * 20
                leadership = sum(e.leadership_skills for e in evaluations) / len(evaluations) * 20
                problem_solving = sum(e.problem_solving for e in evaluations) / len(evaluations) * 20

                overall = (workers_followup + work_efficiency + reports_quality +
                           compliance + safety + attendance + leadership + problem_solving) / 8
                total_ratings.append(overall)

                # تحديد المستوى
                if overall >= 90:
                    level = 'ممتاز'
                    level_color = 'success'
                    rank = 'ذهبي'
                    rank_color = 'warning'
                elif overall >= 80:
                    level = 'جيد جداً'
                    level_color = 'info'
                    rank = 'فضي'
                    rank_color = 'secondary'
                elif overall >= 70:
                    level = 'جيد'
                    level_color = 'primary'
                    rank = 'برونزي'
                    rank_color = 'bronze'
                else:
                    level = 'مقبول'
                    level_color = 'warning'
                    rank = 'عادي'
                    rank_color = 'light'

                # آخر تقييم
                last_eval = evaluations[-1] if evaluations else None

                supervisors_data.append({
                    'id': sup.id,
                    'name': sup.full_name,
                    'color': f'#{hash(sup.full_name) % 0xFFFFFF:06x}',
                    'company': sup.company.name if sup.company else 'غير محدد',
                    'company_id': sup.company.id if sup.company else None,
                    'team_size': Employee.query.filter_by(supervisor_id=sup.id).count(),
                    'workers_followup': round(workers_followup),
                    'work_efficiency': round(work_efficiency),
                    'reports_quality': round(reports_quality),
                    'compliance': round(compliance),
                    'safety': round(safety),
                    'attendance': round(attendance),
                    'leadership': round(leadership),
                    'problem_solving': round(problem_solving),
                    'rating': round(overall / 20, 1),  # تحويل إلى /5
                    'overall': round(overall),
                    'level': level,
                    'level_color': level_color,
                    'rank': rank,
                    'rank_color': rank_color,
                    'last_evaluation': last_eval.date if last_eval else None
                })

        # إحصائيات عامة
        total_supervisors = len(supervisors)
        active_supervisors = sum(1 for s in supervisors if s.is_active)
        avg_performance = sum(total_ratings) / len(total_ratings) if total_ratings else 0

        # أفضل مشرف
        top_supervisor = max(supervisors_data, key=lambda x: x['overall']) if supervisors_data else {'name': '-',
                                                                                                     'rating': 0}

        # توزيع المستويات
        levels = {
            'ممتاز': sum(1 for s in supervisors_data if s['overall'] >= 90),
            'جيد جداً': sum(1 for s in supervisors_data if 80 <= s['overall'] < 90),
            'جيد': sum(1 for s in supervisors_data if 70 <= s['overall'] < 80),
            'مقبول': sum(1 for s in supervisors_data if s['overall'] < 70)
        }

        # توصيات ذكية
        recommendations = []

        if levels['ممتاز'] < 2:
            recommendations.append({
                'type': 'info',
                'icon': 'lightbulb',
                'title': 'تطوير القيادات',
                'message': 'عدد المشرفين المتميزين قليل، يوصى ببرنامج تطويري للمشرفين الواعدين',
                'action': 'openTrainingProgram()'
            })

        if avg_performance < 75:
            recommendations.append({
                'type': 'warning',
                'icon': 'exclamation-triangle',
                'title': 'تحسين الأداء',
                'message': 'معدل أداء المشرفين أقل من المستهدف، يوصى بعقد ورش عمل تطويرية',
                'action': 'openWorkshops()'
            })

        # بيانات الرسم البياني
        months = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو']
        performance_trend = [82, 85, 84, 88, 87, round(avg_performance)]

        return render_template('reports/supervisor_performance.html',
                               total_supervisors=total_supervisors,
                               active_supervisors=active_supervisors,
                               avg_performance=round(avg_performance),
                               performance_change=5,
                               top_supervisor={'name': top_supervisor['name'], 'rating': top_supervisor['rating']},
                               total_teams=len(supervisors),
                               avg_team_size=round(sum(s['team_size'] for s in supervisors_data) / len(
                                   supervisors_data)) if supervisors_data else 0,
                               supervisors=supervisors_data,
                               performance_levels=[
                                   {'name': 'ممتاز', 'count': levels['ممتاز'], 'color': 'success'},
                                   {'name': 'جيد جداً', 'count': levels['جيد جداً'], 'color': 'info'},
                                   {'name': 'جيد', 'count': levels['جيد'], 'color': 'primary'},
                                   {'name': 'مقبول', 'count': levels['مقبول'], 'color': 'warning'}
                               ],
                               performance_trend=performance_trend,
                               months_labels=months,
                               distribution_labels=['ممتاز', 'جيد جداً', 'جيد', 'مقبول'],
                               distribution_values=[levels['ممتاز'], levels['جيد جداً'], levels['جيد'],
                                                    levels['مقبول']],
                               supervisors_data=supervisors_data,
                               recommendations=recommendations,
                               companies=Company.query.filter_by(is_active=True).all())
    except Exception as e:
        app.logger.error(f"Error in report_supervisor_performance: {str(e)}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))


@app.route('/reports/supervisor-detailed-evaluation')
@login_required
def report_supervisor_detailed_evaluation():
    """تقرير تقييم المشرفين التفصيلي"""
    try:
        supervisors = Employee.query.filter_by(position='supervisor', is_active=True).all() or []

        supervisors_data = []
        criteria_totals = {
            'workers_followup': [], 'work_efficiency': [], 'reports_quality': [],
            'compliance': [], 'safety': [], 'attendance': [], 'leadership': [], 'problem_solving': []
        }

        for sup in supervisors:
            if not sup:
                continue

            evaluations = SupervisorEvaluation.query.filter_by(supervisor_id=sup.id).all() or []

            if evaluations:
                workers_followup = sum(e.workers_followup for e in evaluations) / len(evaluations) * 20
                work_efficiency = sum(e.work_efficiency for e in evaluations) / len(evaluations) * 20
                reports_quality = sum(e.reports_submission for e in evaluations) / len(evaluations) * 20
                compliance = sum(e.policies_compliance for e in evaluations) / len(evaluations) * 20
                safety = sum(e.safety_procedures for e in evaluations) / len(evaluations) * 20
                attendance = sum(e.attendance_commitment for e in evaluations) / len(evaluations) * 20
                leadership = sum(e.leadership_skills for e in evaluations) / len(evaluations) * 20
                problem_solving = sum(e.problem_solving for e in evaluations) / len(evaluations) * 20

                overall = (workers_followup + work_efficiency + reports_quality +
                           compliance + safety + attendance + leadership + problem_solving) / 8

                # إضافة إلى المجاميع
                criteria_totals['workers_followup'].append(workers_followup)
                criteria_totals['work_efficiency'].append(work_efficiency)
                criteria_totals['reports_quality'].append(reports_quality)
                criteria_totals['compliance'].append(compliance)
                criteria_totals['safety'].append(safety)
                criteria_totals['attendance'].append(attendance)
                criteria_totals['leadership'].append(leadership)
                criteria_totals['problem_solving'].append(problem_solving)

                # ألوان التقييمات
                def get_color(val):
                    if val >= 90:
                        return 'success'
                    elif val >= 80:
                        return 'info'
                    elif val >= 70:
                        return 'primary'
                    elif val >= 60:
                        return 'warning'
                    else:
                        return 'danger'

                supervisors_data.append({
                    'id': sup.id,
                    'name': sup.full_name or 'غير معروف',
                    'workers_followup': round(workers_followup),
                    'workers_followup_color': get_color(workers_followup),
                    'work_efficiency': round(work_efficiency),
                    'work_efficiency_color': get_color(work_efficiency),
                    'reports_quality': round(reports_quality),
                    'reports_quality_color': get_color(reports_quality),
                    'compliance': round(compliance),
                    'compliance_color': get_color(compliance),
                    'safety': round(safety),
                    'safety_color': get_color(safety),
                    'attendance': round(attendance),
                    'attendance_color': get_color(attendance),
                    'leadership': round(leadership),
                    'leadership_color': get_color(leadership),
                    'problem_solving': round(problem_solving),
                    'problem_solving_color': get_color(problem_solving),
                    'overall': round(overall)
                })

        # حساب المتوسطات
        avg_workers = sum(criteria_totals['workers_followup']) / len(criteria_totals['workers_followup']) if \
        criteria_totals['workers_followup'] else 0
        avg_efficiency = sum(criteria_totals['work_efficiency']) / len(criteria_totals['work_efficiency']) if \
        criteria_totals['work_efficiency'] else 0
        avg_reports = sum(criteria_totals['reports_quality']) / len(criteria_totals['reports_quality']) if \
        criteria_totals['reports_quality'] else 0
        avg_compliance = sum(criteria_totals['compliance']) / len(criteria_totals['compliance']) if criteria_totals[
            'compliance'] else 0
        avg_safety = sum(criteria_totals['safety']) / len(criteria_totals['safety']) if criteria_totals['safety'] else 0
        avg_attendance = sum(criteria_totals['attendance']) / len(criteria_totals['attendance']) if criteria_totals[
            'attendance'] else 0
        avg_leadership = sum(criteria_totals['leadership']) / len(criteria_totals['leadership']) if criteria_totals[
            'leadership'] else 0
        avg_problem = sum(criteria_totals['problem_solving']) / len(criteria_totals['problem_solving']) if \
        criteria_totals['problem_solving'] else 0

        avg_overall = (avg_workers + avg_efficiency + avg_reports + avg_compliance +
                       avg_safety + avg_attendance + avg_leadership + avg_problem) / 8 if any(
            [avg_workers, avg_efficiency, avg_reports, avg_compliance, avg_safety, avg_attendance, avg_leadership,
             avg_problem]) else 0

        # نقاط القوة والضعف
        strengths = []
        weaknesses = []

        criteria_pairs = [
            ('متابعة العمال', avg_workers),
            ('كفاءة العمل', avg_efficiency),
            ('جودة التقارير', avg_reports),
            ('الالتزام بالسياسات', avg_compliance),
            ('إجراءات السلامة', avg_safety),
            ('الانضباط الوظيفي', avg_attendance),
            ('المهارات القيادية', avg_leadership),
            ('حل المشكلات', avg_problem)
        ]

        for name, value in criteria_pairs:
            if value >= 85:
                strengths.append({'criterion': name, 'percentage': round(value)})
            elif value < 75 and value > 0:
                weaknesses.append({'criterion': name, 'percentage': round(value)})

        # بيانات تطور الأداء (بيانات آمنة لـ JSON)
        months = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو']
        evolution_series = []

        for i, sup in enumerate(supervisors[:5]):  # أقصى 5 مشرفين
            if sup:
                evolution_series.append({
                    'name': sup.full_name or f'مشرف {i + 1}',
                    'data': [82, 85, 84, 88, 87, 89]  # بيانات تجريبية
                })

        return render_template('reports/supervisor_detailed_evaluation.html',
                               supervisors=supervisors_data,
                               avg_workers_followup=round(avg_workers),
                               avg_work_efficiency=round(avg_efficiency),
                               avg_reports_quality=round(avg_reports),
                               avg_compliance=round(avg_compliance),
                               avg_safety=round(avg_safety),
                               avg_attendance=round(avg_attendance),
                               avg_leadership=round(avg_leadership),
                               avg_problem_solving=round(avg_problem),
                               avg_overall=round(avg_overall),
                               strengths=strengths,
                               weaknesses=weaknesses,
                               evolution_months=months,
                               evolution_series=evolution_series)
    except Exception as e:
        app.logger.error(f"Error in report_supervisor_detailed_evaluation: {str(e)}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))


@app.route('/reports/supervisor-kpi-dashboard')
@login_required
def report_supervisor_kpi_dashboard():
    """لوحة مؤشرات أداء المشرفين"""
    try:
        supervisors = Employee.query.filter_by(position='supervisor', is_active=True).all() or []

        # حساب المؤشرات
        total_evaluations = SupervisorEvaluation.query.count() or 0
        excellent_count = SupervisorEvaluation.query.filter(SupervisorEvaluation.overall_score >= 4.5).count() or 0

        leadership_index = 0
        supervision_efficiency = 0
        reports_quality_index = 0
        team_satisfaction = 85  # قيمة افتراضية

        if supervisors:
            # حساب المؤشرات من التقييمات
            all_evals = SupervisorEvaluation.query.all() or []
            if all_evals:
                leadership_index = sum(e.leadership_skills for e in all_evals) / len(all_evals) * 20
                supervision_efficiency = (sum(e.workers_followup for e in all_evals) +
                                          sum(e.work_efficiency for e in all_evals)) / (2 * len(all_evals)) * 20
                reports_quality_index = sum(e.reports_submission for e in all_evals) / len(all_evals) * 20

        # بيانات المعايير
        criteria_labels = ['متابعة العمال', 'كفاءة العمل', 'جودة التقارير', 'الالتزام', 'السلامة', 'الانضباط',
                           'القيادة', 'حل المشكلات']
        criteria_values = [85, 82, 88, 90, 87, 92, 84, 86]  # بيانات تجريبية

        # مستويات المشرفين
        if supervisors:
            excellent = sum(1 for s in supervisors if s.id % 3 == 0)  # محاكاة
            good = sum(1 for s in supervisors if s.id % 3 == 1)
            average = sum(1 for s in supervisors if s.id % 3 == 2)
            poor = len(supervisors) - excellent - good - average
        else:
            excellent = good = average = poor = 0

        levels = {
            'ممتاز': excellent,
            'جيد جداً': good,
            'جيد': average,
            'مقبول': poor
        }

        # ترتيب المشرفين
        supervisors_ranking = []
        for i, sup in enumerate(supervisors[:10], 1):
            if sup:
                overall_score = 95 - i * 3  # محاكاة
                supervisors_ranking.append({
                    'rank': i,
                    'rank_color': 'warning' if i == 1 else 'secondary' if i == 2 else 'bronze' if i == 3 else 'light',
                    'name': sup.full_name or f'مشرف {i}',
                    'company': sup.company.name if sup.company else '-',
                    'overall': overall_score,
                    'leadership': overall_score - 2,
                    'supervision': overall_score - 1,
                    'reports': overall_score - 3,
                    'satisfaction': overall_score - 4,
                    'level': 'ممتاز' if i <= 2 else 'جيد جداً' if i <= 5 else 'جيد',
                    'level_color': 'success' if i <= 2 else 'info' if i <= 5 else 'primary'
                })

        return render_template('reports/supervisor_kpi_dashboard.html',
                               leadership_index=round(leadership_index) if leadership_index else 0,
                               supervision_efficiency=round(supervision_efficiency) if supervision_efficiency else 0,
                               reports_quality_index=round(reports_quality_index) if reports_quality_index else 0,
                               team_satisfaction=team_satisfaction,
                               criteria_labels=criteria_labels,
                               criteria_values=criteria_values,
                               levels_labels=list(levels.keys()),
                               levels_values=list(levels.values()),
                               supervisors_ranking=supervisors_ranking)
    except Exception as e:
        app.logger.error(f"Error in report_supervisor_kpi_dashboard: {str(e)}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))

@app.route('/reports/daily-evaluations')
@login_required
def reports_daily_evaluations():
    date_param = request.args.get('date', date.today().isoformat())
    try:
        report_date = datetime.strptime(date_param, '%Y-%m-%d').date()
    except ValueError:
        report_date = date.today()

    evaluations = CleaningEvaluation.query.filter_by(date=report_date).all()

    # حساب الإحصائيات
    total_evaluations = len(evaluations)
    if total_evaluations > 0:
        total_score = sum(eval.overall_score for eval in evaluations)
        avg_score = total_score / total_evaluations
    else:
        total_score = 0
        avg_score = 0

    return render_template('reports/daily_evaluations.html',
                           evaluations=evaluations,
                           report_date=report_date,
                           today=date.today(),
                           total_evaluations=total_evaluations,
                           total_score=total_score,
                           avg_score=avg_score)


@app.route('/reports/company-attendance')
@login_required
def report_company_attendance():
    """تقرير حضور الموظفين على مستوى الشركات مع عرض يومي ملون"""
    try:
        app.logger.info("=" * 50)
        app.logger.info(f"📊 تقرير حضور الموظفين على مستوى الشركات - المستخدم: {current_user.username}")

        # التحقق من الصلاحيات - المالك فقط يرى جميع الشركات
        if current_user.role != 'owner':
            flash('غير مصرح بالوصول إلى هذا التقرير', 'error')
            return redirect(url_for('reports_index'))

        # الحصول على الشهر والسنة من الرابط أو استخدام الشهر الحالي
        today = date.today()
        selected_year = request.args.get('year', today.year, type=int)
        selected_month = request.args.get('month', today.month, type=int)
        selected_company_id = request.args.get('company_id', type=int)

        # حساب بداية ونهاية الشهر
        start_date = date(selected_year, selected_month, 1)
        if selected_month == 12:
            end_date = date(selected_year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(selected_year, selected_month + 1, 1) - timedelta(days=1)

        # عدد أيام الشهر
        days_in_month = end_date.day

        # قائمة الأيام للعرض
        month_days = list(range(1, days_in_month + 1))

        # أسماء الأشهر
        month_names = {
            1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
            5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
            9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
        }

        # الحصول على جميع الشركات النشطة
        companies_query = Company.query.filter_by(is_active=True).order_by(Company.name)
        if selected_company_id:
            companies = [Company.query.get_or_404(selected_company_id)]
        else:
            companies = companies_query.all()

        # تجهيز بيانات التقرير
        report_data = []
        grand_total_present = 0
        grand_total_absent = 0

        for company in companies:
            # الحصول على موظفي الشركة النشطين
            employees = Employee.query.filter_by(
                company_id=company.id,
                is_active=True
            ).order_by(Employee.full_name).all()

            company_employees = []
            company_present_total = 0
            company_absent_total = 0

            for employee in employees:
                # الحصول على سجلات حضور الموظف لهذا الشهر
                attendance_records = Attendance.query.filter(
                    Attendance.employee_id == employee.id,
                    Attendance.date >= start_date,
                    Attendance.date <= end_date
                ).all()

                # إنشاء مصفوفة للحضور اليومي
                daily_attendance = {}
                for record in attendance_records:
                    day = record.date.day
                    daily_attendance[day] = record.status

                # حساب إحصائيات الموظف
                present_days = len([r for r in attendance_records if r.status == 'present'])
                absent_days = len([r for r in attendance_records if r.status == 'absent'])
                late_days = len([r for r in attendance_records if r.status == 'late'])

                # إجمالي أيام الحضور (present + late)
                total_present = present_days + late_days
                total_absent = absent_days

                company_present_total += total_present
                company_absent_total += total_absent

                # تحديد اسم الوظيفة بالعربية
                if employee.position == 'supervisor':
                    position_ar = 'مشرف'
                elif employee.position == 'monitor':
                    position_ar = 'مراقب'
                elif employee.position == 'worker':
                    position_ar = 'عامل'
                else:
                    position_ar = employee.position

                employee_data = {
                    'id': employee.id,
                    'name': employee.full_name,
                    'position': position_ar,
                    'daily': daily_attendance,
                    'present_days': total_present,
                    'absent_days': total_absent,
                    'late_days': late_days,
                    'attendance_rate': round((total_present / days_in_month) * 100) if days_in_month > 0 else 0
                }
                company_employees.append(employee_data)

            grand_total_present += company_present_total
            grand_total_absent += company_absent_total

            company_data = {
                'id': company.id,
                'name': company.name,
                'employees': company_employees,
                'total_employees': len(company_employees),
                'total_present': company_present_total,
                'total_absent': company_absent_total,
                'attendance_rate': round(
                    (company_present_total / (company_present_total + company_absent_total) * 100)) if (
                                                                                                                   company_present_total + company_absent_total) > 0 else 0
            }
            report_data.append(company_data)

        # قائمة السنوات المتاحة (آخر 5 سنوات)
        current_year = today.year
        years = list(range(current_year - 2, current_year + 1))

        app.logger.info(f"✅ تم إنشاء تقرير حضور لـ {len(report_data)} شركة")
        app.logger.info(f"📅 الشهر: {month_names[selected_month]} {selected_year}")
        app.logger.info(f"👥 إجمالي الحضور: {grand_total_present}, إجمالي الغياب: {grand_total_absent}")
        app.logger.info("=" * 50)

        return render_template('reports/company_attendance.html',
                               report_data=report_data,
                               month_days=month_days,
                               selected_year=selected_year,
                               selected_month=selected_month,
                               selected_company_id=selected_company_id,
                               month_name=month_names[selected_month],
                               years=years,
                               months=month_names,
                               companies=Company.query.filter_by(is_active=True).all(),
                               grand_total_present=grand_total_present,
                               grand_total_absent=grand_total_absent,
                               total_days=days_in_month,
                               today=today)

    except Exception as e:
        app.logger.error(f"❌ Error in report_company_attendance: {str(e)}")
        import traceback
        app.logger.error(f"🔍 تفاصيل الخطأ: {traceback.format_exc()}")
        flash('حدث خطأ في تحميل تقرير الحضور', 'error')
        return redirect(url_for('reports_index'))


@app.route('/reports/salary-report/export/<export_type>')
@login_required
def export_salary_report(export_type):
    """
    تصدير تقرير الرواتب إلى Excel أو PDF باستخدام الدالة المركزية
    export_type: 'excel' أو 'pdf'
    """
    if not check_permission('can_view_salary_reports') or current_user.role != 'owner':
        flash('غير مصرح', 'error')
        return redirect(url_for('reports_index'))

    try:
        # ============================================
        # الحصول على نفس معاملات الفلترة
        # ============================================
        from_date_str = request.args.get('from_date', '')
        to_date_str = request.args.get('to_date', '')
        selected_company_id = request.args.get('company_id', type=int)

        # معالجة التواريخ
        if from_date_str and to_date_str:
            try:
                from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
                to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('صيغة التاريخ غير صحيحة', 'error')
                return redirect(url_for('report_salary_report'))
        else:
            selected_year = request.args.get('year', date.today().year, type=int)
            selected_month = request.args.get('month', date.today().month, type=int)
            from_date = date(selected_year, selected_month, 1)
            if selected_month == 12:
                to_date = date(selected_year + 1, 1, 1) - timedelta(days=1)
            else:
                to_date = date(selected_year, selected_month + 1, 1) - timedelta(days=1)

        # ============================================
        # استخدام الدالة المساعدة لجلب البيانات
        # ============================================
        salary_data = get_salary_data(from_date, to_date, selected_company_id)
        report_data = salary_data['report_data']

        # ============================================
        # تجهيز صفوف البيانات للتصدير
        # ============================================
        rows = []

        for company in report_data:
            for emp in company['employees']:
                rows.append({
                    'company': company['name'],
                    'employee_name': emp['name'],
                    'position': emp['position'],
                    'daily_rate': emp['daily_rate'],
                    'present_days': emp['present_days'],
                    'absent_days': emp.get('absent_days', 0),
                    'overtime_hours': emp.get('overtime_hours', 0),
                    'overtime_pay': emp.get('overtime_pay', 0),
                    'base_pay': emp['base_pay'],
                    'penalties': emp.get('penalties', 0),
                    'loan_deductions': emp.get('loan_deductions', 0),
                    'loan_remaining': emp.get('loan_remaining', 0),
                    'total_deductions': emp.get('total_deductions', 0),
                    'net_salary': emp['net_salary'],
                    'attendance_rate': f"{emp.get('attendance_rate', 0)}%"
                })

            # إضافة صف إجمالي الشركة
            rows.append({
                'company': f"🔹 إجمالي {company['name']}",
                'employee_name': '',
                'position': '',
                'daily_rate': '',
                'present_days': '',
                'absent_days': '',
                'overtime_hours': '',
                'overtime_pay': company['totals']['overtime_pay'],
                'base_pay': company['totals']['base_pay'],
                'penalties': company['totals']['penalties'],
                'loan_deductions': company['totals']['loan_deductions'],
                'loan_remaining': '',
                'total_deductions': company['totals']['penalties'] + company['totals']['loan_deductions'],
                'net_salary': company['totals']['net_salary'],
                'attendance_rate': ''
            })

        # إضافة صف الإجمالي النهائي
        rows.append({
            'company': '💰 الإجمالي النهائي',
            'employee_name': '',
            'position': '',
            'daily_rate': '',
            'present_days': '',
            'absent_days': '',
            'overtime_hours': '',
            'overtime_pay': salary_data['grand_totals']['overtime_pay'],
            'base_pay': salary_data['grand_totals']['base_pay'],
            'penalties': salary_data['grand_totals']['penalties'],
            'loan_deductions': salary_data['grand_totals']['loan_deductions'],
            'loan_remaining': '',
            'total_deductions': salary_data['grand_totals']['penalties'] + salary_data['grand_totals'][
                'loan_deductions'],
            'net_salary': salary_data['grand_totals']['net_salary'],
            'attendance_rate': ''
        })

        # ============================================
        # تعريف أسماء الأعمدة
        # ============================================
        headers = [
            'الشركة',
            'الموظف',
            'الوظيفة',
            'الراتب اليومي',
            'أيام الحضور',
            'أيام الغياب',
            'ساعات إضافية',
            'قيمة الساعات',
            'الراتب الأساسي',
            'الجزاءات',
            'خصم السلف',
            'باقي السلف',
            'إجمالي الخصومات',
            'صافي الراتب',
            'نسبة الحضور'
        ]

        # ============================================
        # اسم التقرير
        # ============================================
        report_name = f"تقرير الرواتب {from_date.strftime('%Y-%m-%d')} إلى {to_date.strftime('%Y-%m-%d')}"
        filename_prefix = f"salary_report_{from_date.strftime('%Y%m%d')}_to_{to_date.strftime('%Y%m%d')}"

        # ============================================
        # استدعاء الدالة المركزية
        # ============================================
        return export_report(
            export_type=export_type,
            report_name=report_name,
            headers=headers,
            rows=rows,
            filename_prefix=filename_prefix,
            orientation='landscape'  # أفقي لاحتواء الأعمدة الكثيرة
        )

    except Exception as e:
        app.logger.error(f"❌ Error in export_salary_report: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        flash(f'حدث خطأ في تصدير التقرير: {str(e)}', 'error')
        return redirect(url_for('report_salary_report', **request.args))

@app.route('/reports/salary-report')
@login_required
def report_salary_report():
    if not check_permission('can_view_salary_reports'):
        flash('غير مصرح بعرض تقارير الرواتب', 'error')
        return redirect(url_for('reports_index'))

    """تقرير الرواتب الشامل للموظفين على مستوى الشركات - مع فلترة حسب التاريخ والسلف"""
    try:
        app.logger.info("=" * 50)
        app.logger.info(f"💰 تقرير الرواتب الشامل - المستخدم: {current_user.username}")

        # التحقق من الصلاحيات - المالك فقط
        if current_user.role != 'owner':
            flash('غير مصرح بالوصول إلى هذا التقرير', 'error')
            return redirect(url_for('reports_index'))

        # الحصول على تواريخ الفلترة من الباراميترات
        from_date_str = request.args.get('from_date', '')
        to_date_str = request.args.get('to_date', '')
        selected_company_id = request.args.get('company_id', type=int)

        # إذا تم تحديد تواريخ، استخدمها
        if from_date_str and to_date_str:
            try:
                from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
                to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('صيغة التاريخ غير صحيحة', 'error')
                from_date = date.today().replace(day=1)
                to_date = date.today()
        else:
            # استخدام الشهر المحدد أو الشهر الحالي
            selected_year = request.args.get('year', date.today().year, type=int)
            selected_month = request.args.get('month', date.today().month, type=int)

            from_date = date(selected_year, selected_month, 1)
            if selected_month == 12:
                to_date = date(selected_year + 1, 1, 1) - timedelta(days=1)
            else:
                to_date = date(selected_year, selected_month + 1, 1) - timedelta(days=1)

        # عدد أيام الفترة
        days_in_period = (to_date - from_date).days + 1

        # أسماء الأشهر
        month_names = {
            1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
            5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
            9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
        }
        months = month_names

        # قائمة السنوات المتاحة
        years = list(range(2020, date.today().year + 2))

        # الحصول على جميع الشركات النشطة
        companies_query = Company.query.filter_by(is_active=True).order_by(Company.name)
        if selected_company_id:
            companies = [Company.query.get_or_404(selected_company_id)]
        else:
            companies = companies_query.all()

        # تجهيز بيانات التقرير
        report_data = []
        grand_totals = {
            'base_pay': 0,
            'overtime_pay': 0,
            'allowances': 0,
            'deductions': 0,
            'insurance': 0,
            'tax': 0,
            'penalties': 0,
            'loan_deductions': 0,  # ✅ إضافة خصم السلف
            'net_salary': 0,
            'employees_count': 0
        }

        for company in companies:
            # الحصول على موظفي الشركة النشطين
            employees = Employee.query.filter_by(
                company_id=company.id,
                is_active=True
            ).order_by(Employee.full_name).all()

            company_employees = []
            company_totals = {
                'base_pay': 0,
                'overtime_pay': 0,
                'allowances': 0,
                'deductions': 0,
                'insurance': 0,
                'tax': 0,
                'penalties': 0,
                'loan_deductions': 0,  # ✅ إضافة خصم السلف
                'net_salary': 0
            }

            for employee in employees:
                # ============================================
                # 1. بيانات الحضور
                # ============================================
                attendance_records = Attendance.query.filter(
                    Attendance.employee_id == employee.id,
                    Attendance.date >= from_date,
                    Attendance.date <= to_date
                ).all()

                present_days = len([r for r in attendance_records if r.status in ['present', 'late']])
                absent_days = len([r for r in attendance_records if r.status == 'absent'])

                # ============================================
                # 2. الساعات الإضافية (من جدول overtime)
                # ============================================
                from models import Overtime
                overtime_records = Overtime.query.filter(
                    Overtime.employee_id == employee.id,
                    Overtime.overtime_date >= from_date,
                    Overtime.overtime_date <= to_date,
                    Overtime.is_transferred == True  # فقط المرحلة
                ).all()

                overtime_hours = sum(r.hours for r in overtime_records)
                overtime_pay = sum(r.cost for r in overtime_records)

                # ============================================
                # 3. السلف والخصومات (من جدول EmployeeLoan و LoanInstallment)
                # ============================================
                from models import EmployeeLoan, LoanInstallment

                # السلف النشطة للموظف
                active_loans = EmployeeLoan.query.filter(
                    EmployeeLoan.employee_id == employee.id,
                    EmployeeLoan.status == 'active'
                ).all()

                total_loan_remaining = sum(l.remaining for l in active_loans)

                # الأقساط المسددة في هذه الفترة (المرحلة إلى كشف الراتب)
                loan_installments = LoanInstallment.query.join(
                    EmployeeLoan, LoanInstallment.loan_id == EmployeeLoan.id
                ).filter(
                    EmployeeLoan.employee_id == employee.id,
                    LoanInstallment.payment_date >= from_date,
                    LoanInstallment.payment_date <= to_date,
                    LoanInstallment.payment_method == 'payroll'
                ).all()

                loan_deductions = sum(i.amount for i in loan_installments)

                # ============================================
                # 4. حساب ساعات العمل الإضافية (من الحضور - بديل)
                # ============================================
                overtime_hours_attendance = 0
                for record in attendance_records:
                    if record.check_in and record.check_out:
                        try:
                            check_in = datetime.combine(record.date, record.check_in)
                            check_out = datetime.combine(record.date, record.check_out)
                            hours_worked = (check_out - check_in).seconds / 3600
                            if hours_worked > 8:
                                overtime_hours_attendance += hours_worked - 8
                        except:
                            pass

                # استخدام الساعات الإضافية من جدول overtime إذا وجدت، وإلا من الحضور
                if overtime_hours == 0 and overtime_hours_attendance > 0:
                    overtime_hours = overtime_hours_attendance
                    overtime_pay = 25 * overtime_hours

                # ============================================
                # 5. الجزاءات
                # ============================================
                from models import Penalty
                penalties_query = Penalty.query.filter(
                    Penalty.employee_id == employee.id,
                    Penalty.penalty_date >= from_date,
                    Penalty.penalty_date <= to_date,
                    Penalty.is_deducted == True
                ).all()
                penalties = sum(p.amount for p in penalties_query)

                # ============================================
                # 6. حساب الراتب
                # ============================================
                daily_rate = round(employee.salary / 30, 2) if employee.salary else 0
                base_pay = daily_rate * present_days

                # البدلات والخصومات الأخرى (قيم افتراضية)
                allowances = 0
                deductions = 0
                insurance = 0
                tax = 0

                # إجمالي الخصومات (الجزاءات + السلف)
                total_deductions = loan_deductions + penalties + deductions + insurance + tax

                # صافي الراتب
                net_salary = base_pay + overtime_pay + allowances - total_deductions

                # تحديد اسم الوظيفة بالعربية
                position_ar = {
                    'supervisor': 'مشرف',
                    'monitor': 'مراقب',
                    'worker': 'عامل'
                }.get(employee.position, employee.position)

                # ============================================
                # 7. تجهيز بيانات الموظف مع جميع الحقول
                # ============================================
                employee_data = {
                    'id': employee.id,
                    'name': employee.full_name,
                    'position': position_ar,
                    'daily_rate': round(daily_rate, 2),
                    'present_days': present_days,
                    'absent_days': absent_days,
                    'overtime_hours': round(overtime_hours, 1),
                    'overtime_pay': round(overtime_pay, 2),
                    'base_pay': round(base_pay, 2),
                    'allowances': round(allowances, 2),
                    'deductions': round(deductions, 2),
                    'insurance': round(insurance, 2),
                    'tax': round(tax, 2),
                    'penalties': round(penalties, 2),
                    'loan_deductions': round(loan_deductions, 2),  # ✅ مهم جداً
                    'loan_remaining': round(total_loan_remaining, 2),  # ✅ مهم جداً
                    'has_loans': len(active_loans) > 0,  # ✅ مهم جداً
                    'active_loans_count': len(active_loans),  # ✅ مهم جداً
                    'total_deductions': round(total_deductions, 2),
                    'net_salary': round(net_salary, 2),
                    'attendance_rate': round((present_days / days_in_period) * 100) if days_in_period > 0 else 0
                }

                company_employees.append(employee_data)

                # إضافة إلى إجماليات الشركة
                company_totals['base_pay'] += base_pay
                company_totals['overtime_pay'] += overtime_pay
                company_totals['allowances'] += allowances
                company_totals['deductions'] += deductions
                company_totals['insurance'] += insurance
                company_totals['tax'] += tax
                company_totals['penalties'] += penalties
                company_totals['loan_deductions'] += loan_deductions  # ✅ مهم جداً
                company_totals['net_salary'] += net_salary

            # ترتيب الموظفين
            company_employees.sort(key=lambda x: x['name'])

            company_data = {
                'id': company.id,
                'name': company.name,
                'employees': company_employees,
                'total_employees': len(company_employees),
                'totals': company_totals
            }
            report_data.append(company_data)

            # إضافة إلى الإجماليات الكلية
            grand_totals['base_pay'] += company_totals['base_pay']
            grand_totals['overtime_pay'] += company_totals['overtime_pay']
            grand_totals['allowances'] += company_totals['allowances']
            grand_totals['deductions'] += company_totals['deductions']
            grand_totals['insurance'] += company_totals['insurance']
            grand_totals['tax'] += company_totals['tax']
            grand_totals['penalties'] += company_totals['penalties']
            grand_totals['loan_deductions'] += company_totals['loan_deductions']  # ✅ مهم جداً
            grand_totals['net_salary'] += company_totals['net_salary']
            grand_totals['employees_count'] += len(company_employees)

        return render_template('reports/salary_report.html',
                               report_data=report_data,
                               from_date=from_date,
                               to_date=to_date,
                               selected_year=from_date.year,
                               selected_month=from_date.month,
                               selected_company_id=selected_company_id,
                               years=years,
                               months=months,
                               companies=Company.query.filter_by(is_active=True).all(),
                               grand_totals=grand_totals,
                               total_days=days_in_period,
                               today=date.today())

    except Exception as e:
        app.logger.error(f"❌ Error in report_salary_report: {str(e)}")
        import traceback
        app.logger.error(f"🔍 تفاصيل الخطأ: {traceback.format_exc()}")
        flash(f'حدث خطأ في تحميل تقرير الرواتب: {str(e)}', 'error')
        return redirect(url_for('reports_index'))


def get_salary_data(from_date, to_date, company_id=None):
    """
    دالة مساعدة لجلب بيانات الرواتب بنفس طريقة report_salary_report
    تعيد قاموساً بنفس هيكل البيانات المستخدم في تقرير الرواتب
    """
    days_in_period = (to_date - from_date).days + 1

    # الحصول على الشركات المطلوبة
    companies_query = Company.query.filter_by(is_active=True).order_by(Company.name)
    if company_id:
        companies_query = companies_query.filter_by(id=company_id)
    companies = companies_query.all()

    # تجهيز بيانات التقرير
    report_data = []
    grand_totals = {
        'base_pay': 0,
        'overtime_pay': 0,
        'allowances': 0,
        'deductions': 0,
        'insurance': 0,
        'tax': 0,
        'penalties': 0,
        'loan_deductions': 0,
        'net_salary': 0,
        'employees_count': 0
    }

    # قاموس لتخزين بيانات الرواتب حسب الشركة والشهر
    salary_by_company_month = {}

    for company in companies:
        # الحصول على موظفي الشركة النشطين
        employees = Employee.query.filter_by(
            company_id=company.id,
            is_active=True
        ).order_by(Employee.full_name).all()

        company_employees = []
        company_totals = {
            'base_pay': 0,
            'overtime_pay': 0,
            'allowances': 0,
            'deductions': 0,
            'insurance': 0,
            'tax': 0,
            'penalties': 0,
            'loan_deductions': 0,
            'net_salary': 0
        }

        for employee in employees:
            # ============================================
            # 1. بيانات الحضور
            # ============================================
            attendance_records = Attendance.query.filter(
                Attendance.employee_id == employee.id,
                Attendance.date >= from_date,
                Attendance.date <= to_date
            ).all()

            present_days = len([r for r in attendance_records if r.status in ['present', 'late']])

            # ============================================
            # 2. الساعات الإضافية
            # ============================================
            from models import Overtime
            overtime_records = Overtime.query.filter(
                Overtime.employee_id == employee.id,
                Overtime.overtime_date >= from_date,
                Overtime.overtime_date <= to_date,
                Overtime.is_transferred == True
            ).all()

            overtime_pay = sum(r.cost for r in overtime_records)

            # ============================================
            # 3. خصم السلف
            # ============================================
            from models import EmployeeLoan, LoanInstallment

            loan_installments = LoanInstallment.query.join(
                EmployeeLoan, LoanInstallment.loan_id == EmployeeLoan.id
            ).filter(
                EmployeeLoan.employee_id == employee.id,
                LoanInstallment.payment_date >= from_date,
                LoanInstallment.payment_date <= to_date,
                LoanInstallment.payment_method == 'payroll'
            ).all()

            loan_deductions = sum(i.amount for i in loan_installments)

            # ============================================
            # 4. الجزاءات
            # ============================================
            from models import Penalty
            penalties_query = Penalty.query.filter(
                Penalty.employee_id == employee.id,
                Penalty.penalty_date >= from_date,
                Penalty.penalty_date <= to_date,
                Penalty.is_deducted == True
            ).all()
            penalties = sum(p.amount for p in penalties_query)

            # ============================================
            # 5. حساب الراتب
            # ============================================
            daily_rate = round(employee.salary / 30, 2) if employee.salary else 0
            base_pay = daily_rate * present_days

            # صافي الراتب
            net_salary = base_pay + overtime_pay - loan_deductions - penalties

            # تحديد اسم الوظيفة بالعربية
            position_ar = {
                'supervisor': 'مشرف',
                'monitor': 'مراقب',
                'worker': 'عامل'
            }.get(employee.position, employee.position)

            employee_data = {
                'id': employee.id,
                'name': employee.full_name,
                'position': position_ar,
                'daily_rate': round(daily_rate, 2),
                'present_days': present_days,
                'overtime_pay': round(overtime_pay, 2),
                'base_pay': round(base_pay, 2),
                'penalties': round(penalties, 2),
                'loan_deductions': round(loan_deductions, 2),
                'net_salary': round(max(0, net_salary), 2),  # التأكد من أنها موجبة
                'attendance_rate': round((present_days / days_in_period) * 100) if days_in_period > 0 else 0
            }

            company_employees.append(employee_data)

            # تحديث إجماليات الشركة
            company_totals['base_pay'] += base_pay
            company_totals['overtime_pay'] += overtime_pay
            company_totals['penalties'] += penalties
            company_totals['loan_deductions'] += loan_deductions
            company_totals['net_salary'] += net_salary

        company_data = {
            'id': company.id,
            'name': company.name,
            'employees': company_employees,
            'total_employees': len(company_employees),
            'totals': company_totals
        }
        report_data.append(company_data)

        # تحديث الإجماليات الكلية
        grand_totals['base_pay'] += company_totals['base_pay']
        grand_totals['overtime_pay'] += company_totals['overtime_pay']
        grand_totals['penalties'] += company_totals['penalties']
        grand_totals['loan_deductions'] += company_totals['loan_deductions']
        grand_totals['net_salary'] += company_totals['net_salary']
        grand_totals['employees_count'] += len(company_employees)

        # تخزين بيانات الشركة حسب الشهر (للاستخدام في التحليل الشهري)
        for employee_data in company_employees:
            # استخراج الشهر والسنة من التاريخ (تقريباً)
            # هذا تبسيط، في الواقع قد تحتاج لتخزين بيانات كل شهر بشكل منفصل
            key = f"{company.id}_{from_date.year}_{from_date.month}"
            if key not in salary_by_company_month:
                salary_by_company_month[key] = {
                    'salaries': 0,
                    'overtime': 0,
                    'penalties': 0,
                    'loan_deductions': 0,
                    'employee_count': 0
                }
            salary_by_company_month[key]['salaries'] += employee_data['net_salary']
            salary_by_company_month[key]['overtime'] += employee_data['overtime_pay']
            salary_by_company_month[key]['penalties'] += employee_data['penalties']
            salary_by_company_month[key]['loan_deductions'] += employee_data['loan_deductions']
            salary_by_company_month[key]['employee_count'] += 1

    return {
        'report_data': report_data,
        'grand_totals': grand_totals,
        'salary_by_company_month': salary_by_company_month
    }

@app.route('/create-payroll-table')
@login_required
def create_payroll_table():
    """إنشاء جدول الرواتب الجديد"""
    if current_user.role != 'owner':
        return "غير مصرح", 403

    try:
        from sqlalchemy import inspect, text

        # التحقق من وجود الجدول
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        if 'payrolls' not in tables:
            # إنشاء جدول payrolls
            db.create_all()

            # التحقق مرة أخرى
            inspector = inspect(db.engine)
            if 'payrolls' in inspector.get_table_names():
                flash('✅ تم إنشاء جدول الرواتب بنجاح', 'success')
            else:
                # إذا لم يتم الإنشاء تلقائياً، استخدم SQL مباشر
                with db.engine.connect() as conn:
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS payrolls (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            employee_id INTEGER NOT NULL,
                            year INTEGER NOT NULL,
                            month INTEGER NOT NULL,
                            base_salary FLOAT DEFAULT 0,
                            daily_rate FLOAT DEFAULT 0,
                            working_days INTEGER DEFAULT 0,
                            present_days INTEGER DEFAULT 0,
                            absent_days INTEGER DEFAULT 0,
                            late_days INTEGER DEFAULT 0,
                            overtime_hours FLOAT DEFAULT 0,
                            base_pay FLOAT DEFAULT 0,
                            overtime_rate FLOAT DEFAULT 25,
                            overtime_pay FLOAT DEFAULT 0,
                            transportation_allowance FLOAT DEFAULT 0,
                            housing_allowance FLOAT DEFAULT 0,
                            food_allowance FLOAT DEFAULT 0,
                            other_allowances FLOAT DEFAULT 0,
                            deductions FLOAT DEFAULT 0,
                            insurance_deduction FLOAT DEFAULT 0,
                            tax_deduction FLOAT DEFAULT 0,
                            loan_deduction FLOAT DEFAULT 0,
                            penalty_deduction FLOAT DEFAULT 0,
                            total_allowances FLOAT DEFAULT 0,
                            total_deductions FLOAT DEFAULT 0,
                            net_salary FLOAT DEFAULT 0,
                            status VARCHAR(20) DEFAULT 'pending',
                            payment_date DATE,
                            payment_method VARCHAR(50),
                            payment_reference VARCHAR(100),
                            paid_by INTEGER,
                            notes TEXT,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY(employee_id) REFERENCES employees(id),
                            FOREIGN KEY(paid_by) REFERENCES clean_users(id)
                        )
                    """))
                    conn.commit()
                flash('✅ تم إنشاء جدول الرواتب باستخدام SQL المباشر', 'success')
        else:
            flash('ℹ️ جدول الرواتب موجود مسبقاً', 'info')

        return redirect(url_for('reports_index'))

    except Exception as e:
        flash(f'❌ خطأ: {str(e)}', 'error')
        import traceback
        app.logger.error(traceback.format_exc())
        return redirect(url_for('reports_index'))


@app.route('/generate-sample-payrolls')
@login_required
def generate_sample_payrolls():
    """إنشاء كشوف مرتبات تجريبية للشهر الحالي"""
    if current_user.role != 'owner':
        return "غير مصرح", 403

    try:
        today = date.today()
        employees = Employee.query.filter_by(is_active=True).all()
        created_count = 0

        for employee in employees:
            # التحقق من عدم وجود كشف مرتبات لهذا الشهر
            existing = Payroll.query.filter_by(
                employee_id=employee.id,
                year=today.year,
                month=today.month
            ).first()

            if not existing and employee.salary and employee.salary > 0:
                # حساب أيام الشهر
                if today.month == 12:
                    end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)

                working_days = end_date.day
                start_date = date(today.year, today.month, 1)

                # حساب أيام الحضور
                attendance_records = Attendance.query.filter(
                    Attendance.employee_id == employee.id,
                    Attendance.date >= start_date,
                    Attendance.date <= end_date
                ).all()

                present_days = len([r for r in attendance_records if r.status in ['present', 'late']])

                # حساب ساعات إضافية تجريبية
                overtime_hours = 5  # قيمة تجريبية

                # إنشاء كشف مرتبات
                payroll = Payroll(
                    employee_id=employee.id,
                    year=today.year,
                    month=today.month,
                    base_salary=employee.salary,
                    daily_rate=round(employee.salary / 30, 2),
                    working_days=working_days,
                    present_days=present_days,
                    absent_days=working_days - present_days,
                    overtime_hours=overtime_hours,
                    overtime_rate=25,
                    status='pending'
                )
                payroll.calculate_payroll()
                db.session.add(payroll)
                created_count += 1

        db.session.commit()
        flash(f'✅ تم إنشاء {created_count} كشف مرتبات تجريبي', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'❌ خطأ: {str(e)}', 'error')
        import traceback
        app.logger.error(traceback.format_exc())

    return redirect(url_for('reports_index'))


@app.route('/fix-employee-salary')
@login_required
def fix_employee_salary():
    """إصلاح مشكلة daily_rate في نموذج Employee"""
    if current_user.role != 'owner':
        return "غير مصرح", 403

    try:
        from sqlalchemy import inspect, text

        # التحقق من وجود العمود daily_rate في جدول employees
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('employees')]

        added_columns = []

        if 'daily_rate' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE employees ADD COLUMN daily_rate FLOAT DEFAULT 0"))
                conn.commit()
            added_columns.append('daily_rate')
            print("✅ تم إضافة عمود daily_rate")

        if 'overtime_rate' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE employees ADD COLUMN overtime_rate FLOAT DEFAULT 0"))
                conn.commit()
            added_columns.append('overtime_rate')
            print("✅ تم إضافة عمود overtime_rate")

        if 'allowances' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE employees ADD COLUMN allowances FLOAT DEFAULT 0"))
                conn.commit()
            added_columns.append('allowances')
            print("✅ تم إضافة عمود allowances")

        if 'deductions' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE employees ADD COLUMN deductions FLOAT DEFAULT 0"))
                conn.commit()
            added_columns.append('deductions')
            print("✅ تم إضافة عمود deductions")

        if 'insurance_deduction' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE employees ADD COLUMN insurance_deduction FLOAT DEFAULT 0"))
                conn.commit()
            added_columns.append('insurance_deduction')
            print("✅ تم إضافة عمود insurance_deduction")

        if 'tax_deduction' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE employees ADD COLUMN tax_deduction FLOAT DEFAULT 0"))
                conn.commit()
            added_columns.append('tax_deduction')
            print("✅ تم إضافة عمود tax_deduction")

        # تحديث الأجور اليومية للموظفين الحاليين
        employees = Employee.query.all()
        updated_count = 0
        for emp in employees:
            if emp.salary and emp.salary > 0:
                emp.daily_rate = round(emp.salary / 30, 2)
                updated_count += 1

        db.session.commit()

        if added_columns:
            flash(f'✅ تم إضافة الأعمدة: {", ".join(added_columns)}', 'success')
        flash(f'✅ تم تحديث الأجور اليومية لـ {updated_count} موظف', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'❌ خطأ: {str(e)}', 'error')
        import traceback
        app.logger.error(traceback.format_exc())

    return redirect(url_for('reports_index'))

def create_monthly_payroll(employee, year, month, overtime_hours=0):
    """إنشاء كشف مرتبات جديد لموظف لشهر محدد"""

    # حساب أيام الشهر
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)

    working_days = end_date.day

    # حساب أيام الحضور
    start_date = date(year, month, 1)
    attendance_records = Attendance.query.filter(
        Attendance.employee_id == employee.id,
        Attendance.date >= start_date,
        Attendance.date <= end_date
    ).all()

    present_days = len([r for r in attendance_records if r.status in ['present', 'late']])
    absent_days = len([r for r in attendance_records if r.status == 'absent'])

    # حساب الأجر اليومي
    daily_rate = round(employee.salary / 30, 2) if employee.salary else 0

    # إنشاء كشف المرتبات
    payroll = Payroll(
        employee_id=employee.id,
        year=year,
        month=month,
        base_salary=employee.salary,
        daily_rate=daily_rate,
        working_days=working_days,
        present_days=present_days,
        absent_days=absent_days,
        overtime_hours=overtime_hours,
        overtime_rate=25.0,  # يمكن جعله من الإعدادات
        status='pending'
    )

    # حساب الراتب
    payroll.calculate_payroll()

    return payroll

@app.route('/attendance/add-penalty', methods=['POST'])
@login_required
def add_penalty():
    """إضافة جزاء لموظف من صفحة الحضور"""
    try:
        # التحقق من الصلاحيات
        if current_user.role not in ['owner', 'supervisor', 'monitor']:
            return jsonify({
                'success': False,
                'message': 'غير مصرح بهذا الإجراء'
            }), 403

        # الحصول على البيانات من النموذج
        employee_id = request.form.get('employee_id')
        penalty_date = request.form.get('penalty_date')
        amount = request.form.get('amount')
        reason = request.form.get('reason')
        description = request.form.get('description', '')

        # التحقق من البيانات المطلوبة
        if not all([employee_id, penalty_date, amount, reason]):
            return jsonify({
                'success': False,
                'message': 'جميع الحقول المطلوبة يجب ملؤها'
            }), 400

        # تحويل التاريخ
        try:
            penalty_date_obj = datetime.strptime(penalty_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'صيغة التاريخ غير صحيحة'
            }), 400

        # التحقق من وجود الموظف
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({
                'success': False,
                'message': 'الموظف غير موجود'
            }), 404

        # التحقق من الصلاحية للموظف
        if not can_manage_attendance(current_user, int(employee_id)):
            return jsonify({
                'success': False,
                'message': 'غير مصرح بإضافة جزاء لهذا الموظف'
            }), 403

        # إنشاء الجزاء
        penalty = Penalty(
            employee_id=int(employee_id),
            penalty_date=penalty_date_obj,
            year=penalty_date_obj.year,
            month=penalty_date_obj.month,
            amount=float(amount),
            reason=reason,
            description=description,
            recorded_by=current_user.id,
            is_deducted=False
        )

        db.session.add(penalty)
        db.session.commit()

        # ✅ تحديث كشف الراتب لهذا الشهر إذا كان موجوداً
        payroll = Payroll.query.filter_by(
            employee_id=int(employee_id),
            year=penalty_date_obj.year,
            month=penalty_date_obj.month
        ).first()

        if payroll:
            # إضافة الجزاء إلى كشف الراتب
            payroll.penalty_deduction = (payroll.penalty_deduction or 0) + float(amount)
            payroll.calculate_payroll()
            db.session.commit()

        return jsonify({
            'success': True,
            'message': 'تم إضافة الجزاء بنجاح',
            'penalty_id': penalty.id,
            'amount': amount
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in add_penalty: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'حدث خطأ: {str(e)}'
        }), 500

@app.route('/penalties')
@login_required
def penalties_list():
    """عرض قائمة الجزاءات"""
    try:
        # التحقق من الصلاحيات
        if current_user.role != 'owner':
            flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
            return redirect(url_for('dashboard'))

        # ✅ تعريف متغير today
        today = date.today()

        # الحصول على معاملات الفلترة
        employee_id = request.args.get('employee_id', type=int)
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)
        status = request.args.get('status', '')

        # استعلام الجزاءات
        query = Penalty.query

        if employee_id:
            query = query.filter_by(employee_id=employee_id)
        if month:
            query = query.filter_by(month=month)
        if year:
            query = query.filter_by(year=year)
        if status == 'deducted':
            query = query.filter_by(is_deducted=True)
        elif status == 'pending':
            query = query.filter_by(is_deducted=False)

        penalties = query.order_by(Penalty.penalty_date.desc()).all()

        # إحصائيات
        total_amount = sum(p.amount for p in penalties)
        total_count = len(penalties)

        # إحصائيات الترحيل
        transferred_amount = sum(p.amount for p in penalties if p.is_deducted)
        transferred_count = sum(1 for p in penalties if p.is_deducted)
        pending_amount = sum(p.amount for p in penalties if not p.is_deducted)
        pending_count = sum(1 for p in penalties if not p.is_deducted)

        # قائمة الموظفين للفلترة
        employees = Employee.query.filter_by(is_active=True).all()

        # قائمة السنوات المتاحة
        current_year = date.today().year
        years = list(range(current_year - 2, current_year + 1))

        # ✅ المسار الصحيح: penalties/penalties_list (بدون .html)
        return render_template('penalties/penalties_list.html',
                               penalties=penalties,
                               total_amount=total_amount,
                               total_count=total_count,
                               transferred_amount=transferred_amount,
                               transferred_count=transferred_count,
                               pending_amount=pending_amount,
                               pending_count=pending_count,
                               employees=employees,
                               years=years,
                               selected_employee=employee_id,
                               selected_month=month,
                               selected_year=year,
                               selected_status=status,
                               today=today)

    except Exception as e:
        app.logger.error(f"Error in penalties_list: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        flash('حدث خطأ في تحميل قائمة الجزاءات', 'error')
        return redirect(url_for('dashboard'))

@app.route('/penalties/bulk-transfer', methods=['POST'])
@login_required
def bulk_transfer_penalties():
    """ترحيل مجموعة من الجزاءات إلى كشف الرواتب"""
    try:
        if current_user.role != 'owner':
            return jsonify({
                'success': False,
                'message': 'غير مصرح بهذا الإجراء'
            }), 403

        data = request.get_json()
        penalty_ids = data.get('penalty_ids', [])
        transfer_all = data.get('transfer_all', False)

        if not penalty_ids and not transfer_all:
            return jsonify({
                'success': False,
                'message': 'لم يتم تحديد أي جزاءات للترحيل'
            }), 400

        # الحصول على الجزاءات المطلوبة
        if transfer_all:
            penalties = Penalty.query.filter_by(is_deducted=False).all()
        else:
            penalties = Penalty.query.filter(Penalty.id.in_(penalty_ids), Penalty.is_deducted == False).all()

        if not penalties:
            return jsonify({
                'success': False,
                'message': 'لا توجد جزاءات غير مرحّلة'
            }), 400

        transferred_count = 0
        errors = []

        for penalty in penalties:
            try:
                # البحث عن كشف الراتب لنفس الشهر والسنة
                payroll = Payroll.query.filter_by(
                    employee_id=penalty.employee_id,
                    year=penalty.year,
                    month=penalty.month
                ).first()

                if payroll:
                    # ✅ التأكد من وجود قيمة قبل الجمع
                    current_penalty = payroll.penalty_deduction or 0
                    payroll.penalty_deduction = current_penalty + penalty.amount
                    payroll.calculate_payroll()
                else:
                    # إنشاء كشف راتب جديد إذا لم يكن موجوداً
                    employee = Employee.query.get(penalty.employee_id)
                    if employee:
                        # حساب أيام الشهر
                        if penalty.month == 12:
                            end_date = date(penalty.year + 1, 1, 1) - timedelta(days=1)
                        else:
                            end_date = date(penalty.year, penalty.month + 1, 1) - timedelta(days=1)

                        start_date = date(penalty.year, penalty.month, 1)

                        # حساب أيام الحضور
                        attendance_records = Attendance.query.filter(
                            Attendance.employee_id == employee.id,
                            Attendance.date >= start_date,
                            Attendance.date <= end_date
                        ).all()

                        present_days = len([r for r in attendance_records if r.status in ['present', 'late']])

                        # إنشاء كشف راتب جديد
                        payroll = Payroll(
                            employee_id=employee.id,
                            year=penalty.year,
                            month=penalty.month,
                            base_salary=employee.salary or 0,
                            daily_rate=round((employee.salary or 0) / 30, 2),
                            working_days=end_date.day,
                            present_days=present_days,
                            absent_days=end_date.day - present_days,
                            overtime_hours=0,
                            overtime_rate=25,
                            penalty_deduction=penalty.amount,
                            deductions=0,
                            insurance_deduction=0,
                            tax_deduction=0,
                            transportation_allowance=0,
                            housing_allowance=0,
                            food_allowance=0,
                            other_allowances=0,
                            status='pending'
                        )
                        payroll.calculate_payroll()
                        db.session.add(payroll)

                # تحديث حالة الجزاء
                penalty.is_deducted = True
                transferred_count += 1

            except Exception as e:
                errors.append(f"الجزاء {penalty.id}: {str(e)}")

        db.session.commit()

        message = f'✅ تم ترحيل {transferred_count} جزاء بنجاح'
        if errors:
            message += f'\n❌ أخطاء: {len(errors)}'

        return jsonify({
            'success': True,
            'message': message,
            'transferred_count': transferred_count,
            'errors': errors[:5]  # إرجاع أول 5 أخطاء فقط
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in bulk_transfer_penalties: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'حدث خطأ: {str(e)}'
        }), 500

@app.route('/penalties/transfer/<int:penalty_id>', methods=['POST'])
@login_required
def transfer_single_penalty(penalty_id):
    """ترحيل جزاء واحد إلى كشف الرواتب"""
    try:
        if current_user.role != 'owner':
            return jsonify({
                'success': False,
                'message': 'غير مصرح بهذا الإجراء'
            }), 403

        penalty = Penalty.query.get_or_404(penalty_id)

        if penalty.is_deducted:
            return jsonify({
                'success': False,
                'message': 'هذا الجزاء تم ترحيله مسبقاً'
            }), 400

        # البحث عن كشف الراتب
        payroll = Payroll.query.filter_by(
            employee_id=penalty.employee_id,
            year=penalty.year,
            month=penalty.month
        ).first()

        if payroll:
            # ✅ التأكد من وجود قيمة قبل الجمع
            current_penalty = payroll.penalty_deduction or 0
            payroll.penalty_deduction = current_penalty + penalty.amount
            payroll.calculate_payroll()
        else:
            # إنشاء كشف راتب جديد
            employee = Employee.query.get(penalty.employee_id)
            if not employee:
                return jsonify({
                    'success': False,
                    'message': 'الموظف غير موجود'
                }), 404

            # حساب أيام الشهر
            if penalty.month == 12:
                end_date = date(penalty.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(penalty.year, penalty.month + 1, 1) - timedelta(days=1)

            start_date = date(penalty.year, penalty.month, 1)

            # حساب أيام الحضور
            attendance_records = Attendance.query.filter(
                Attendance.employee_id == employee.id,
                Attendance.date >= start_date,
                Attendance.date <= end_date
            ).all()

            present_days = len([r for r in attendance_records if r.status in ['present', 'late']])

            # إنشاء كشف راتب جديد
            payroll = Payroll(
                employee_id=employee.id,
                year=penalty.year,
                month=penalty.month,
                base_salary=employee.salary or 0,
                daily_rate=round((employee.salary or 0) / 30, 2),
                working_days=end_date.day,
                present_days=present_days,
                absent_days=end_date.day - present_days,
                overtime_hours=0,
                overtime_rate=25,
                penalty_deduction=penalty.amount,
                deductions=0,
                insurance_deduction=0,
                tax_deduction=0,
                transportation_allowance=0,
                housing_allowance=0,
                food_allowance=0,
                other_allowances=0,
                status='pending'
            )
            payroll.calculate_payroll()
            db.session.add(payroll)

        penalty.is_deducted = True
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '✅ تم ترحيل الجزاء بنجاح'
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in transfer_single_penalty: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'حدث خطأ: {str(e)}'
        }), 500


@app.route('/financial/company-invoices')
@login_required
def company_invoices_list():
    if not check_permission('can_view_invoices'):
        flash('غير مصرح بعرض الفواتير', 'error')
        return redirect(url_for('dashboard'))

    """عرض قائمة فواتير الشركات"""
    if current_user.role != 'owner':
        flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))

    try:
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        company_id = request.args.get('company_id', type=int)
        status = request.args.get('status', '')

        query = CompanyInvoice.query

        if year:
            query = query.filter_by(year=year)
        if month:
            query = query.filter_by(month=month)
        if company_id:
            query = query.filter_by(company_id=company_id)
        if status:
            query = query.filter_by(status=status)

        invoices = query.order_by(CompanyInvoice.year.desc(), CompanyInvoice.month.desc()).all()

        # إحصائيات
        total_invoiced = sum(i.total_amount for i in invoices)
        total_collected = sum(i.paid_amount for i in invoices)
        total_pending = total_invoiced - total_collected

        companies = Company.query.filter_by(is_active=True).all()
        current_year = date.today().year
        years = list(range(current_year - 3, current_year + 2))

        return render_template('financial/company_invoices.html',
                               invoices=invoices,
                               total_invoiced=total_invoiced,
                               total_collected=total_collected,
                               total_pending=total_pending,
                               companies=companies,
                               years=years,
                               selected_year=year,
                               selected_month=month,
                               selected_company=company_id,
                               selected_status=status)

    except Exception as e:
        app.logger.error(f"Error in company_invoices_list: {str(e)}")
        flash('حدث خطأ في تحميل الفواتير', 'error')
        return redirect(url_for('dashboard'))

@app.route('/financial/add-invoice', methods=['POST'])
@login_required
def add_invoice():
    """إضافة فاتورة جديدة لشركة - مع تحديث الإغلاق الشهري"""
    if current_user.role != 'owner':
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403

    try:
        company_id = request.form.get('company_id')
        year = int(request.form.get('year'))
        month = int(request.form.get('month'))

        # التحقق من عدم وجود فاتورة لنفس الشهر
        existing = CompanyInvoice.query.filter_by(
            company_id=company_id,
            year=year,
            month=month
        ).first()

        if existing:
            return jsonify({
                'success': False,
                'message': 'يوجد فاتورة لهذا الشهر مسبقاً'
            }), 400

        invoice = CompanyInvoice(
            company_id=company_id,
            year=year,
            month=month,
            contract_amount=float(request.form.get('contract_amount', 0)),
            additional_services=float(request.form.get('additional_services', 0)),
            extra_work=float(request.form.get('extra_work', 0)),
            materials_amount=float(request.form.get('materials_amount', 0)),
            equipment_rent=float(request.form.get('equipment_rent', 0)),
            discount=float(request.form.get('discount', 0)),
            penalty_deduction=float(request.form.get('penalty_deduction', 0)),
            late_payment_penalty=float(request.form.get('late_payment_penalty', 0)),
            paid_amount=float(request.form.get('paid_amount', 0)),
            payment_date=datetime.strptime(request.form.get('payment_date'), '%Y-%m-%d').date() if request.form.get('payment_date') else None,
            payment_method=request.form.get('payment_method'),
            payment_reference=request.form.get('payment_reference'),
            notes=request.form.get('notes')
        )

        invoice.calculate_totals()
        db.session.add(invoice)
        db.session.commit()

        # ✅ تحديث الإغلاق الشهري في الخلفية
        trigger_monthly_closing_update(year, month)

        return jsonify({
            'success': True,
            'message': 'تم إضافة الفاتورة بنجاح',
            'invoice_id': invoice.id
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in add_invoice: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/financial/other-income', methods=['GET', 'POST'])
@login_required
def other_income():
    """إدارة الإيرادات الأخرى - مع تحديث الإغلاق الشهري"""
    if not check_permission('can_view_financial'):
        flash('غير مصرح بعرض الإيرادات', 'error')
        return redirect(url_for('dashboard'))

    if current_user.role != 'owner':
        flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))

    today = date.today()

    if request.method == 'POST':
        try:
            year = int(request.form.get('year'))
            month = int(request.form.get('month'))

            income = OtherIncome(
                company_id=request.form.get('company_id') or None,
                income_date=datetime.strptime(request.form.get('income_date'), '%Y-%m-%d').date(),
                year=year,
                month=month,
                income_type=request.form.get('income_type'),
                income_type_ar=request.form.get('income_type_ar'),
                amount=float(request.form.get('amount')),
                description=request.form.get('description'),
                reference=request.form.get('reference'),
                is_recurring=request.form.get('is_recurring') == 'on',
                recurring_period=request.form.get('recurring_period')
            )

            db.session.add(income)
            db.session.commit()

            # ✅ تحديث الإغلاق الشهري في الخلفية
            trigger_monthly_closing_update(year, month)

            flash('تم إضافة الإيراد بنجاح', 'success')
            return redirect(url_for('other_income'))

        except Exception as e:
            db.session.rollback()
            flash(f'خطأ: {str(e)}', 'error')

    # GET request - عرض الإيرادات
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    income_type = request.args.get('type', '')

    query = OtherIncome.query

    if year:
        query = query.filter_by(year=year)
    if month:
        query = query.filter_by(month=month)
    if income_type:
        query = query.filter_by(income_type=income_type)

    incomes = query.order_by(OtherIncome.income_date.desc()).all()

    total_amount = sum(i.amount for i in incomes)

    companies = Company.query.filter_by(is_active=True).all()
    current_year = date.today().year
    years = list(range(current_year - 3, current_year + 2))

    income_types = [
        {'value': 'service', 'label': 'خدمات إضافية'},
        {'value': 'project', 'label': 'مشاريع خاصة'},
        {'value': 'material', 'label': 'بيع مواد'},
        {'value': 'equipment', 'label': 'تأجير معدات'},
        {'value': 'other', 'label': 'أخرى'}
    ]

    return render_template('financial/other_income.html',
                           incomes=incomes,
                           total_amount=total_amount,
                           companies=companies,
                           years=years,
                           income_types=income_types,
                           selected_year=year,
                           selected_month=month,
                           selected_type=income_type,
                           today=today)  # ✅ أضف today هنا


# ============================================
# دالة معالجة الإغلاق الشهري المحسنة
# ============================================
def process_monthly_closing(year, month):
    """
    معالجة وحفظ بيانات الإغلاق الشهري مسبقاً
    تقوم بحساب جميع المؤشرات المالية للشهر وتخزينها في جدول MonthlyFinancialSummary
    """
    try:
        app.logger.info(f"🔄 بدء معالجة الإغلاق الشهري لـ {month}/{year}")

        from models import Payroll, CompanyInvoice, OtherIncome, MonthlyFinancialSummary, Company, Employee
        from sqlalchemy import func

        # 1. جلب جميع الشركات النشطة
        companies = Company.query.filter_by(is_active=True).all()

        # 2. معالجة الرواتب للشهر
        payrolls = Payroll.query.filter_by(year=year, month=month).all()

        # 3. تجميع الرواتب حسب الشركة
        company_salaries = {}
        for payroll in payrolls:
            if payroll.employee and payroll.employee.company_id:
                company_id = payroll.employee.company_id
                if company_id not in company_salaries:
                    company_salaries[company_id] = {
                        'total_base_salaries': 0,
                        'total_overtime': 0,
                        'total_penalties': 0,
                        'total_loan_deductions': 0,
                        'net_salaries': 0,
                        'employee_count': 0
                    }

                company_salaries[company_id]['total_base_salaries'] += payroll.base_salary or 0
                company_salaries[company_id]['total_overtime'] += payroll.overtime_pay or 0
                company_salaries[company_id]['total_penalties'] += payroll.penalty_deduction or 0
                company_salaries[company_id]['total_loan_deductions'] += payroll.loan_deduction or 0
                company_salaries[company_id]['net_salaries'] += payroll.net_salary or 0
                company_salaries[company_id]['employee_count'] += 1

        # 4. معالجة فواتير الشركات
        invoices = CompanyInvoice.query.filter_by(year=year, month=month).all()
        company_invoices = {}
        for inv in invoices:
            if inv.company_id not in company_invoices:
                company_invoices[inv.company_id] = {
                    'total_invoiced': 0,
                    'total_collected': 0
                }
            company_invoices[inv.company_id]['total_invoiced'] += inv.total_amount or 0
            company_invoices[inv.company_id]['total_collected'] += inv.paid_amount or 0

        # 5. معالجة الإيرادات الأخرى
        other_incomes = OtherIncome.query.filter_by(year=year, month=month).all()
        company_other_income = {}
        general_income = 0
        for inc in other_incomes:
            if inc.company_id:
                if inc.company_id not in company_other_income:
                    company_other_income[inc.company_id] = 0
                company_other_income[inc.company_id] += inc.amount or 0
            else:
                general_income += inc.amount or 0

        # 6. إنشاء أو تحديث الملخص الشهري لكل شركة
        summaries_created = 0
        for company in companies:
            # بيانات الشركة
            salaries = company_salaries.get(company.id, {})
            invoices_data = company_invoices.get(company.id, {})
            other_income = company_other_income.get(company.id, 0)

            # البحث عن الملخص الموجود
            summary = MonthlyFinancialSummary.query.filter_by(
                year=year,
                month=month,
                company_id=company.id
            ).first()

            if not summary:
                summary = MonthlyFinancialSummary(
                    year=year,
                    month=month,
                    company_id=company.id
                )
                db.session.add(summary)

            # تحديث البيانات
            summary.total_invoiced = invoices_data.get('total_invoiced', 0)
            summary.total_collected = invoices_data.get('total_collected', 0)
            summary.other_income = other_income
            summary.total_base_salaries = salaries.get('total_base_salaries', 0)
            summary.total_overtime = salaries.get('total_overtime', 0)
            summary.total_penalties = salaries.get('total_penalties', 0)
            summary.total_loan_deductions = salaries.get('total_loan_deductions', 0)
            summary.net_salaries = salaries.get('net_salaries', 0)
            summary.employee_count = salaries.get('employee_count', 0)

            # حساب المؤشرات
            summary.calculate()
            summaries_created += 1

        # 7. إنشاء ملخص للإيرادات العامة (بدون شركة)
        if general_income > 0:
            general_summary = MonthlyFinancialSummary.query.filter_by(
                year=year,
                month=month,
                company_id=None
            ).first()

            if not general_summary:
                general_summary = MonthlyFinancialSummary(
                    year=year,
                    month=month,
                    company_id=None
                )
                db.session.add(general_summary)

            general_summary.other_income = general_income
            general_summary.total_invoiced = 0
            general_summary.total_collected = 0
            general_summary.net_salaries = 0
            general_summary.employee_count = 0
            general_summary.calculate()

        db.session.commit()

        app.logger.info(f"✅ تمت معالجة {summaries_created} شركة للإغلاق الشهري {month}/{year}")
        return True, f"تمت معالجة {summaries_created} شركة بنجاح"

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"❌ خطأ في معالجة الإغلاق الشهري: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        return False, str(e)


# ============================================
# دالة تشغيل تحديث الإغلاق الشهري في الخلفية
# ============================================
def trigger_monthly_closing_update(year, month):
    """
    تشغيل تحديث الإغلاق الشهري في خلفية منفصلة
    لمنع تأثير العملية على سرعة استجابة المستخدم
    """
    from threading import Thread

    def run_update():
        with app.app_context():
            try:
                app.logger.info(f"🔄 بدء تحديث الإغلاق الشهري في الخلفية لـ {month}/{year}")
                process_monthly_closing(year, month)
            except Exception as e:
                app.logger.error(f"❌ خطأ في تحديث الخلفية: {str(e)}")

    thread = Thread(target=run_update)
    thread.daemon = True
    thread.start()

    app.logger.info(f"📌 تم بدء تحديث الخلفية للإغلاق الشهري {month}/{year}")


@app.route('/financial/monthly-closing')
@login_required
def monthly_closing():
    """تقرير الإغلاق الشهري الشامل - مع دعم الفترة من/إلى وفلترة الشركة ورسم بياني"""
    if not check_permission('can_view_financial'):
        flash('غير مصرح بعرض الإغلاق الشهري', 'error')
        return redirect(url_for('dashboard'))

    try:
        today = date.today()

        # ============================================
        # 1. استقبال معاملات الفلترة
        # ============================================
        from_date_str = request.args.get('from_date', '')
        to_date_str = request.args.get('to_date', '')
        company_id = request.args.get('company_id', type=int)

        # معالجة التواريخ
        if from_date_str and to_date_str:
            try:
                from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
                to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
                selected_year = from_date.year
                selected_month = from_date.month
            except ValueError:
                flash('صيغة التاريخ غير صحيحة', 'error')
                from_date = date(today.year, today.month, 1)
                to_date = today
                selected_year = today.year
                selected_month = today.month
        else:
            selected_year = request.args.get('year', today.year, type=int)
            selected_month = request.args.get('month', today.month, type=int)
            from_date = date(selected_year, selected_month, 1)
            if selected_month == 12:
                to_date = date(selected_year + 1, 1, 1) - timedelta(days=1)
            else:
                to_date = date(selected_year, selected_month + 1, 1) - timedelta(days=1)

        days_in_period = (to_date - from_date).days + 1

        month_names = {
            1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
            5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
            9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
        }

        years = list(range(today.year - 3, today.year + 2))
        companies_filter = Company.query.filter_by(is_active=True).order_by(Company.name).all()

        # ============================================
        # 2. جلب بيانات الرواتب باستخدام الدالة المساعدة
        # ============================================
        salary_data_result = get_salary_data(from_date, to_date, company_id)
        salary_report_data = salary_data_result['report_data']
        salary_grand_totals = salary_data_result['grand_totals']
        salary_by_company_month = salary_data_result['salary_by_company_month']

        # استخراج الإحصائيات الكلية من بيانات الرواتب
        total_salaries = salary_grand_totals['net_salary']
        total_overtime = salary_grand_totals['overtime_pay']
        total_penalties = salary_grand_totals['penalties']
        total_loan_deductions = salary_grand_totals['loan_deductions']
        employee_count = salary_grand_totals['employees_count']

        # ============================================
        # 3. جلب جميع الشركات
        # ============================================
        companies_query = Company.query.filter_by(is_active=True).order_by(Company.name)
        if company_id:
            companies_query = companies_query.filter_by(id=company_id)
        companies = companies_query.all()

        # ============================================
        # 4. قائمة الأشهر في الفترة المحددة
        # ============================================
        months_in_period = []
        current_date = from_date.replace(day=1)
        while current_date <= to_date:
            months_in_period.append((current_date.year, current_date.month))
            if current_date.month == 12:
                current_date = date(current_date.year + 1, 1, 1)
            else:
                current_date = date(current_date.year, current_date.month + 1, 1)

        # ============================================
        # 5. جلب بيانات الفواتير
        # ============================================
        invoices_query = CompanyInvoice.query
        if company_id:
            invoices_query = invoices_query.filter_by(company_id=company_id)

        all_invoices = invoices_query.all()
        filtered_invoices = []
        for inv in all_invoices:
            inv_date = date(inv.year, inv.month, 1)
            if from_date <= inv_date <= to_date:
                filtered_invoices.append(inv)

        # ============================================
        # 6. جلب الإيرادات الأخرى
        # ============================================
        other_incomes_query = OtherIncome.query.filter(
            OtherIncome.income_date >= from_date,
            OtherIncome.income_date <= to_date
        )
        if company_id:
            other_incomes_query = other_incomes_query.filter_by(company_id=company_id)

        other_incomes = other_incomes_query.all()

        # ============================================
        # 7. تجميع إحصائيات كل شركة
        # ============================================
        company_stats = []

        # متغيرات للإحصائيات الكلية
        total_invoiced = 0
        total_collected = 0
        other_income_total = 0
        general_income_total = 0
        general_incomes = []

        for company in companies:
            for year, month in months_in_period:
                # ============================================
                # أ. جلب الرواتب من البيانات المخزنة
                # ============================================
                key = f"{company.id}_{year}_{month}"
                if key in salary_by_company_month:
                    month_salaries = salary_by_company_month[key]['salaries']
                    month_overtime = salary_by_company_month[key]['overtime']
                    month_penalties = salary_by_company_month[key]['penalties']
                    month_loans = salary_by_company_month[key]['loan_deductions']
                    month_employee_count = salary_by_company_month[key]['employee_count']
                else:
                    month_salaries = 0
                    month_overtime = 0
                    month_penalties = 0
                    month_loans = 0
                    month_employee_count = 0

                # ============================================
                # ب. جلب فواتير الشركة لهذا الشهر
                # ============================================
                month_invoices = [inv for inv in filtered_invoices
                                  if inv.company_id == company.id and inv.year == year and inv.month == month]

                month_invoiced = sum(i.total_amount or 0 for i in month_invoices)
                month_collected = sum(i.paid_amount or 0 for i in month_invoices)

                # ============================================
                # ج. جلب الإيرادات الأخرى لهذا الشهر
                # ============================================
                month_other = [inc for inc in other_incomes
                               if inc.company_id == company.id
                               and inc.income_date.year == year
                               and inc.income_date.month == month]

                month_other_income = sum(o.amount or 0 for o in month_other)

                # ============================================
                # د. حساب الإيرادات والمصروفات والربح
                # ============================================
                month_revenue = month_collected + month_other_income
                month_expenses = month_salaries
                month_profit = month_revenue - month_expenses
                month_profit_margin = (month_profit / month_revenue * 100) if month_revenue > 0 else 0

                # اسم الشهر
                month_name = month_names.get(month, f'شهر {month}')

                # إضافة فقط إذا كان هناك أي بيانات
                if month_revenue != 0 or month_expenses != 0 or month_invoiced != 0 or month_employee_count > 0:
                    company_stats.append({
                        'name': company.name,
                        'year': year,
                        'month': month,
                        'month_name': f'{month_name} {year}',
                        'invoiced': month_invoiced,
                        'collected': month_collected,
                        'other_income': month_other_income,
                        'total_revenue': month_revenue,
                        'salaries': month_salaries,
                        'overtime': month_overtime,
                        'penalties': month_penalties,
                        'loan_deductions': month_loans,
                        'profit': month_profit,
                        'profit_margin': month_profit_margin,
                        'employee_count': month_employee_count,
                        'is_general': False
                    })

                    # تحديث الإحصائيات الكلية
                    total_invoiced += month_invoiced
                    total_collected += month_collected
                    other_income_total += month_other_income

        # ============================================
        # 8. جلب الإيرادات العامة (بدون شركة)
        # ============================================
        general_incomes_query = OtherIncome.query.filter(
            OtherIncome.company_id == None,
            OtherIncome.income_date >= from_date,
            OtherIncome.income_date <= to_date
        ).all()

        for inc in general_incomes_query:
            general_incomes.append({
                'date': inc.income_date.strftime('%Y-%m-%d'),
                'type': inc.income_type_ar or inc.income_type,
                'description': inc.description or '-',
                'amount': inc.amount or 0
            })
            general_income_total += inc.amount or 0
            other_income_total += inc.amount or 0

        # إضافة الإيرادات العامة إلى company_stats
        if general_income_total > 0 and not company_id:
            # تجميع الإيرادات العامة حسب الشهر
            general_by_month = {}
            for inc in general_incomes:
                inc_date = datetime.strptime(inc['date'], '%Y-%m-%d').date()
                month_key = f"{inc_date.year}-{inc_date.month:02d}"
                if month_key not in general_by_month:
                    general_by_month[month_key] = 0
                general_by_month[month_key] += inc['amount']

            for month_key, amount in general_by_month.items():
                year = int(month_key[:4])
                month = int(month_key[5:7])
                month_name = month_names.get(month, f'شهر {month}')

                company_stats.append({
                    'name': '📌 إيرادات عامة',
                    'year': year,
                    'month': month,
                    'month_name': f'{month_name} {year}',
                    'invoiced': 0,
                    'collected': 0,
                    'other_income': amount,
                    'total_revenue': amount,
                    'salaries': 0,
                    'overtime': 0,
                    'penalties': 0,
                    'loan_deductions': 0,
                    'profit': amount,
                    'profit_margin': 100,
                    'employee_count': 0,
                    'is_general': True
                })

        # ترتيب النتائج حسب السنة والشهر
        company_stats.sort(key=lambda x: (x['year'], x['month']))

        # ============================================
        # 9. حساب المؤشرات الكلية
        # ============================================
        total_revenue = total_collected + other_income_total
        total_expenses = total_salaries
        net_profit = total_revenue - total_expenses
        profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
        collection_rate = (total_collected / total_invoiced * 100) if total_invoiced > 0 else 0
        avg_salary = total_salaries / employee_count if employee_count > 0 else 0

        # ============================================
        # 10. بيانات المقارنة مع الفترة السابقة
        # ============================================
        period_length = (to_date - from_date).days + 1
        prev_from_date = from_date - timedelta(days=period_length)
        prev_to_date = from_date - timedelta(days=1)

        # جلب بيانات الفترة السابقة باستخدام الدالة المساعدة
        prev_salary_data = get_salary_data(prev_from_date, prev_to_date, company_id)
        prev_salaries = prev_salary_data['grand_totals']['net_salary']

        prev_invoices = CompanyInvoice.query.filter(
            CompanyInvoice.payment_date >= prev_from_date,
            CompanyInvoice.payment_date <= prev_to_date
        ).all()

        prev_other = OtherIncome.query.filter(
            OtherIncome.income_date >= prev_from_date,
            OtherIncome.income_date <= prev_to_date
        ).all()

        prev_revenue = sum(i.paid_amount or 0 for i in prev_invoices) + sum(o.amount or 0 for o in prev_other)
        prev_profit = prev_revenue - prev_salaries

        revenue_change = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
        profit_change = ((net_profit - prev_profit) / prev_profit * 100) if prev_profit > 0 else 0

        # ============================================
        # 11. بيانات آخر 12 شهر للرسم البياني
        # ============================================
        monthly_data = []
        base_date = from_date
        for i in range(11, -1, -1):
            month_date = base_date - timedelta(days=30 * i)
            m = month_date.month
            y = month_date.year

            # تحديد بداية ونهاية الشهر
            month_start = date(y, m, 1)
            if m == 12:
                month_end = date(y + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(y, m + 1, 1) - timedelta(days=1)

            m_invoices = CompanyInvoice.query.filter(
                CompanyInvoice.payment_date >= month_start,
                CompanyInvoice.payment_date <= month_end
            ).all()

            m_other = OtherIncome.query.filter(
                OtherIncome.income_date >= month_start,
                OtherIncome.income_date <= month_end
            ).all()

            # جلب رواتب هذا الشهر باستخدام الدالة المساعدة
            m_salary_data = get_salary_data(month_start, month_end, company_id)
            m_salaries = m_salary_data['grand_totals']['net_salary']

            m_revenue = sum(i.paid_amount or 0 for i in m_invoices) + sum(o.amount or 0 for o in m_other)
            m_profit = m_revenue - m_salaries

            monthly_data.append({
                'month': month_names.get(m, f'شهر {m}'),
                'revenue': m_revenue,
                'salaries': m_salaries,
                'profit': m_profit
            })

        # ============================================
        # 12. بيانات الرسم البياني للشركات
        # ============================================
        company_names_for_chart = []
        company_revenues_for_chart = []
        company_profits_for_chart = []

        for stat in company_stats:
            if not stat.get('is_general', False) and stat['name'] not in company_names_for_chart:
                company_names_for_chart.append(stat['name'])
                company_revenues_for_chart.append(stat['total_revenue'])
                company_profits_for_chart.append(stat['profit'])

        chart_data = {
            'companies': company_names_for_chart,
            'revenues': company_revenues_for_chart,
            'profits': company_profits_for_chart
        }

        # ============================================
        # 13. التأكد من أن monthly_data ليس فارغاً
        # ============================================
        if not monthly_data:
            monthly_data = [{'month': month_names.get(selected_month, ''), 'revenue': 0, 'salaries': 0, 'profit': 0}]

        # ============================================
        # 14. تجهيز البيانات للقالب
        # ============================================
        context = {
            'selected_year': selected_year,
            'selected_month': selected_month,
            'month_name': month_names.get(selected_month, ''),
            'from_date': from_date,
            'to_date': to_date,
            'from_date_str': from_date.strftime('%Y-%m-%d'),
            'to_date_str': to_date.strftime('%Y-%m-%d'),
            'years': years,
            'months': month_names,
            'companies_filter': companies_filter,
            'selected_company_id': company_id,
            'days_in_period': days_in_period,

            'total_revenue': total_revenue,
            'net_profit': net_profit,
            'total_expenses': total_expenses,
            'profit_margin': profit_margin,
            'revenue_change': revenue_change,
            'profit_change': profit_change,
            'collection_rate': collection_rate,
            'total_invoiced': total_invoiced,
            'total_collected': total_collected,
            'other_income_total': other_income_total,

            'total_salaries': total_salaries,
            'total_overtime': total_overtime,
            'total_penalties': total_penalties,
            'total_loan_deductions': total_loan_deductions,
            'employee_count': employee_count,
            'avg_salary': avg_salary,

            'company_stats': company_stats,
            'general_income_total': general_income_total,
            'general_income_count': len(general_incomes),
            'general_incomes': general_incomes,

            'chart_data': chart_data,
            'monthly_data': monthly_data,

            'invoices': filtered_invoices,
            'other_incomes': other_incomes,
            'payrolls': [],

            'prev_revenue': prev_revenue,
            'prev_profit': prev_profit
        }

        return render_template('financial/monthly_closing.html', **context)

    except Exception as e:
        app.logger.error(f"❌ Error in monthly_closing: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        flash(f'حدث خطأ في تحميل التقرير: {str(e)}', 'error')
        return redirect(url_for('reports_index'))

@app.route('/debug/check-transfer', methods=['GET'])
@login_required
def debug_check_transfer():
    """فحص حالة الترحيل"""
    try:
        from models import Overtime, Payroll

        # عدد الساعات الإضافية غير المرحّلة
        pending_overtime = Overtime.query.filter_by(is_transferred=False).count()

        # عدد كشوف الرواتب
        payroll_count = Payroll.query.count()

        return jsonify({
            'pending_overtime': pending_overtime,
            'payroll_count': payroll_count,
            'transfer_endpoint': '/overtime/transfer-to-payroll',
            'method': 'POST'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ✅ هذه الدالة يجب أن تكون خارج monthly_closing
def update_monthly_summary(year, month):
    """تحديث الملخص الشهري"""
    try:
        # جلب البيانات
        payrolls = Payroll.query.filter_by(year=year, month=month).all()
        invoices = CompanyInvoice.query.filter_by(year=year, month=month).all()
        other_incomes = OtherIncome.query.filter_by(year=year, month=month).all()

        total_salaries = sum(p.base_salary or 0 for p in payrolls)
        total_penalties = sum(p.penalty_deduction or 0 for p in payrolls)
        net_salaries = sum(p.net_salary or 0 for p in payrolls)
        employee_count = len(payrolls)

        total_invoiced = sum(i.total_amount or 0 for i in invoices)
        total_collected = sum(i.paid_amount or 0 for i in invoices)
        other_income_total = sum(i.amount or 0 for i in other_incomes)

        # البحث عن الملخص الموجود أو إنشاء جديد
        summary = MonthlyFinancialSummary.query.filter_by(
            year=year,
            month=month
        ).first()

        if not summary:
            summary = MonthlyFinancialSummary(
                year=year,
                month=month
            )
            db.session.add(summary)

        # تحديث البيانات
        summary.total_invoiced = total_invoiced
        summary.total_collected = total_collected
        summary.other_income = other_income_total
        summary.total_salaries = total_salaries
        summary.total_penalties = total_penalties
        summary.operating_expenses = 0  # يمكن تحديثها لاحقاً
        summary.employee_count = employee_count

        # حساب المؤشرات
        summary.calculate()

        db.session.commit()
        return True

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating monthly summary: {str(e)}")
        return False


# ✅ [جديد] دالة عامة لتصدير أي تقرير إلى Excel
# ✅ [جديد] دالة عامة لتصدير أي تقرير إلى Excel
@app.route('/export-to-excel', methods=['POST'])
@login_required
def export_to_excel():
    """تصدير البيانات إلى ملف Excel"""
    try:
        # الحصول على البيانات من الطلب
        data = request.get_json()

        if not data or 'rows' not in data or 'columns' not in data:
            return jsonify({
                'success': False,
                'message': 'بيانات غير صالحة للتصدير'
            }), 400

        rows = data['rows']
        columns = data['columns']
        report_name = data.get('report_name', 'تقرير')

        # إنشاء DataFrame من البيانات
        df = pd.DataFrame(rows)

        # إعادة تسمية الأعمدة (إذا كانت الأسماء مختلفة)
        if 'column_names' in data:
            df.columns = data['column_names']
        else:
            # استخدام أسماء الأعمدة المرسلة
            df.columns = [col.get('label', col.get('field', f'عمود {i + 1}')) for i, col in enumerate(columns)]

        # إنشاء ملف Excel في الذاكرة
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=report_name, index=False)

            # تنسيق الخلايا (اختياري)
            workbook = writer.book
            worksheet = writer.sheets[report_name]

            # ضبط عرض الأعمدة تلقائياً
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        # تجهيز الملف للتحميل
        output.seek(0)
        filename = f"{report_name}_{date.today().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        app.logger.error(f"Error in export_to_excel: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'حدث خطأ أثناء التصدير: {str(e)}'
        }), 500


# ✅ [جديد] دالة تصدير مخصصة لتقرير الحضور
@app.route('/attendance/report/export')
@login_required
def export_attendance_report():
    """تصدير تقرير الحضور إلى Excel"""
    if not check_permission('can_view_attendance_reports'):
        flash('غير مصرح', 'error')
        return redirect(url_for('attendance_index'))

    try:
        # الحصول على تواريخ الفلترة
        from_date_str = request.args.get('from_date', '')
        to_date_str = request.args.get('to_date', '')

        if not from_date_str or not to_date_str:
            flash('يجب تحديد فترة للتصدير', 'error')
            return redirect(url_for('attendance_report'))

        from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()

        # الحصول على البيانات
        attendance_records = Attendance.query \
            .join(Employee) \
            .filter(
            Attendance.date >= from_date,
            Attendance.date <= to_date
        ) \
            .order_by(Attendance.date.desc()) \
            .all()

        # تجهيز البيانات للتصدير
        data = []
        for record in attendance_records:
            data.append({
                'التاريخ': record.date.strftime('%Y-%m-%d'),
                'الموظف': record.employee.full_name if record.employee else '-',
                'الحالة': {
                    'present': 'حاضر',
                    'absent': 'غائب',
                    'late': 'متأخر'
                }.get(record.status, record.status),
                'الوردية': 'صباحية' if record.shift_type == 'morning' else 'مسائية',
                'وقت الحضور': record.check_in.strftime('%H:%M') if record.check_in else '-',
                'وقت الانصراف': record.check_out.strftime('%H:%M') if record.check_out else '-',
                'ملاحظات': record.notes or ''
            })

        # إنشاء DataFrame
        df = pd.DataFrame(data)

        # إنشاء ملف Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='تقرير الحضور', index=False)

        output.seek(0)
        filename = f"تقرير_الحضور_{from_date_str}_الى_{to_date_str}.xlsx"

        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        app.logger.error(f"Error in export_attendance_report: {str(e)}")
        flash(f'حدث خطأ أثناء التصدير: {str(e)}', 'error')
        return redirect(url_for('attendance_report'))


# ============================================
# دوال الترحيل الذكي - أضفها هنا
# ============================================

@app.route('/attendance/transfer-enhanced')
@login_required
def transfer_attendance_smart():
    """صفحة الترحيل الذكي المحسنة"""
    if current_user.role != 'owner':
        flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))

    # جلب البيانات للفلترة
    companies = Company.query.filter_by(is_active=True).all()
    areas = Area.query.filter_by(is_active=True).all()
    locations = Location.query.filter_by(is_active=True).all()

    return render_template('attendance/transfer.html',
                           companies=companies,
                           areas=areas,
                           locations=locations,
                           today=date.today())


@app.route('/api/areas/all')
@login_required
def get_all_areas():
    """الحصول على جميع المناطق مع أسماء الشركات"""
    try:
        areas = Area.query.filter_by(is_active=True).all()
        areas_data = [{
            'id': area.id,
            'name': area.name,
            'company_name': area.company.name if area.company else 'بدون شركة'
        } for area in areas]

        return jsonify({
            'success': True,
            'data': areas_data
        })
    except Exception as e:
        app.logger.error(f"Error in get_all_areas: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/locations/all')
@login_required
def get_all_locations():
    """الحصول على جميع المواقع مع أسماء المناطق"""
    try:
        locations = Location.query.filter_by(is_active=True).all()
        locations_data = [{
            'id': loc.id,
            'name': loc.name,
            'area_name': loc.area.name if loc.area else 'بدون منطقة'
        } for loc in locations]

        return jsonify({
            'success': True,
            'data': locations_data
        })
    except Exception as e:
        app.logger.error(f"Error in get_all_locations: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/attendance/source-data')
@login_required
def get_source_data():
    """الحصول على إحصائيات بيانات المصدر"""
    try:
        start_date_str = request.args.get('start')
        end_date_str = request.args.get('end')
        filter_type = request.args.get('filter', 'all')
        filter_id = request.args.get('filter_id')

        if not start_date_str or not end_date_str:
            return jsonify({'success': False, 'message': 'التواريخ مطلوبة'}), 400

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        # بناء استعلام الموظفين
        employees_query = Employee.query.filter_by(is_active=True)

        if filter_type == 'company' and filter_id:
            employees_query = employees_query.filter_by(company_id=int(filter_id))
        elif filter_type == 'area' and filter_id:
            area = Area.query.get(int(filter_id))
            if area:
                location_ids = [loc.id for loc in area.locations]
                place_ids = Place.query.filter(Place.location_id.in_(location_ids)).all()
                worker_ids = [p.worker_id for p in place_ids if p.worker_id]
                if worker_ids:
                    employees_query = employees_query.filter(Employee.id.in_(worker_ids))
                else:
                    employees_query = employees_query.filter(Employee.id == -1)  # لا نتائج
        elif filter_type == 'location' and filter_id:
            place_ids = Place.query.filter_by(location_id=int(filter_id)).all()
            worker_ids = [p.worker_id for p in place_ids if p.worker_id]
            if worker_ids:
                employees_query = employees_query.filter(Employee.id.in_(worker_ids))
            else:
                employees_query = employees_query.filter(Employee.id == -1)  # لا نتائج

        employees = employees_query.all()
        employee_ids = [e.id for e in employees]

        # جلب سجلات الحضور
        attendance_records = 0
        if employee_ids:
            attendance_records = Attendance.query.filter(
                Attendance.employee_id.in_(employee_ids),
                Attendance.date >= start_date,
                Attendance.date <= end_date
            ).count()

        total_days = (end_date - start_date).days + 1

        return jsonify({
            'success': True,
            'total_records': attendance_records,
            'employee_count': len(employees),
            'total_days': total_days
        })

    except Exception as e:
        app.logger.error(f"Error in get_source_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/attendance/transfer-preview', methods=['POST'])
@login_required
def transfer_preview():
    """معاينة الترحيل قبل التنفيذ"""
    try:
        data = request.get_json()

        source_start = datetime.strptime(data['source_start'], '%Y-%m-%d').date()
        source_end = datetime.strptime(data['source_end'], '%Y-%m-%d').date()
        target_start = datetime.strptime(data['target_start'], '%Y-%m-%d').date()
        target_end = datetime.strptime(data['target_end'], '%Y-%m-%d').date()

        filter_type = data.get('filter_type', 'all')
        filter_id = data.get('filter_id')
        copy_mode = data.get('copy_mode', True)
        fill_absences = data.get('fill_absences', True)
        exclude_management = data.get('exclude_management', True)

        # حساب عدد أيام الفترة المصدر والهدف
        source_days = (source_end - source_start).days + 1
        target_days = (target_end - target_start).days + 1

        # بناء استعلام الموظفين حسب الفلترة
        employees_query = Employee.query.filter_by(is_active=True)

        if filter_type == 'company' and filter_id:
            employees_query = employees_query.filter_by(company_id=int(filter_id))
        elif filter_type == 'area' and filter_id:
            area = Area.query.get(int(filter_id))
            if area:
                location_ids = [loc.id for loc in area.locations]
                place_ids = Place.query.filter(Place.location_id.in_(location_ids)).all()
                worker_ids = [p.worker_id for p in place_ids if p.worker_id]
                if worker_ids:
                    employees_query = employees_query.filter(Employee.id.in_(worker_ids))
                else:
                    employees_query = employees_query.filter(Employee.id == -1)
        elif filter_type == 'location' and filter_id:
            place_ids = Place.query.filter_by(location_id=int(filter_id)).all()
            worker_ids = [p.worker_id for p in place_ids if p.worker_id]
            if worker_ids:
                employees_query = employees_query.filter(Employee.id.in_(worker_ids))
            else:
                employees_query = employees_query.filter(Employee.id == -1)

        employees = employees_query.all()
        employee_ids = [e.id for e in employees]

        # جلب سجلات المصدر
        source_records = []
        if employee_ids:
            source_records = Attendance.query.filter(
                Attendance.employee_id.in_(employee_ids),
                Attendance.date >= source_start,
                Attendance.date <= source_end
            ).all()

        # تجميع سجلات المصدر حسب الموظف والتاريخ
        source_map = {}
        for record in source_records:
            key = f"{record.employee_id}_{record.date}"
            source_map[key] = record

        # جلب سجلات الهدف الموجودة مسبقاً
        target_records = []
        if employee_ids:
            target_records = Attendance.query.filter(
                Attendance.employee_id.in_(employee_ids),
                Attendance.date >= target_start,
                Attendance.date <= target_end
            ).all()

        target_map = {}
        for record in target_records:
            key = f"{record.employee_id}_{record.date}"
            target_map[key] = record

        # حساب إحصائيات المعاينة
        existing_count = len(target_records)
        new_count = 0
        absence_count = 0
        preview_records = []

        # إنشاء سجلات المعاينة
        for employee in employees:
            # استثناء الإداريين إذا كان الخيار مفعل
            if exclude_management and employee.position in ['owner', 'supervisor', 'monitor']:
                continue

            for day_offset in range(target_days):
                current_date = target_start + timedelta(days=day_offset)
                key = f"{employee.id}_{current_date}"

                # البحث عن سجل في المصدر (بنفس إزاحة اليوم)
                source_date = source_start + timedelta(days=day_offset % source_days)
                source_key = f"{employee.id}_{source_date}"
                source_record = source_map.get(source_key)

                if key in target_map:
                    # سجل موجود مسبقاً
                    action = 'موجود'
                    status = target_map[key].status
                elif source_record and copy_mode:
                    # نسخ من المصدر
                    action = 'نسخ'
                    status = source_record.status
                    new_count += 1
                elif fill_absences:
                    # تعبئة غياب تلقائي
                    action = 'غياب تلقائي'
                    status = 'absent'
                    absence_count += 1
                else:
                    # لا شيء
                    continue

                # تحديد لون الصف
                row_class = ''
                if action == 'موجود':
                    row_class = 'table-info'
                elif action == 'نسخ':
                    row_class = 'table-success'
                elif action == 'غياب تلقائي':
                    row_class = 'table-warning'

                preview_records.append({
                    'employee_id': employee.id,
                    'employee_name': employee.full_name,
                    'position': {
                        'supervisor': 'مشرف',
                        'monitor': 'مراقب',
                        'worker': 'عامل'
                    }.get(employee.position, employee.position),
                    'company': employee.company.name if employee.company else '-',
                    'date': current_date.strftime('%Y-%m-%d'),
                    'action': action,
                    'status': status,
                    'status_ar': 'حاضر' if status == 'present' else 'غائب' if status == 'absent' else 'متأخر',
                    'row_class': row_class
                })

        return jsonify({
            'success': True,
            'stats': {
                'total': len(preview_records),
                'existing': existing_count,
                'new': new_count,
                'absences': absence_count,
                'employees': len(employees),
                'days': target_days
            },
            'records': preview_records[:100]  # حد أقصى 100 سجل للمعاينة
        })

    except Exception as e:
        app.logger.error(f"Error in transfer_preview: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/attendance/transfer-execute', methods=['POST'])
@login_required
def transfer_execute():
    """تنفيذ الترحيل الذكي"""
    try:
        data = request.get_json()

        source_start = datetime.strptime(data['source_start'], '%Y-%m-%d').date()
        source_end = datetime.strptime(data['source_end'], '%Y-%m-%d').date()
        target_start = datetime.strptime(data['target_start'], '%Y-%m-%d').date()
        target_end = datetime.strptime(data['target_end'], '%Y-%m-%d').date()

        filter_type = data.get('filter_type', 'all')
        filter_id = data.get('filter_id')
        copy_mode = data.get('copy_mode', True)
        fill_absences = data.get('fill_absences', True)
        exclude_management = data.get('exclude_management', True)

        source_days = (source_end - source_start).days + 1
        target_days = (target_end - target_start).days + 1

        # بناء استعلام الموظفين حسب الفلترة
        employees_query = Employee.query.filter_by(is_active=True)

        if filter_type == 'company' and filter_id:
            employees_query = employees_query.filter_by(company_id=int(filter_id))
        elif filter_type == 'area' and filter_id:
            area = Area.query.get(int(filter_id))
            if area:
                location_ids = [loc.id for loc in area.locations]
                place_ids = Place.query.filter(Place.location_id.in_(location_ids)).all()
                worker_ids = [p.worker_id for p in place_ids if p.worker_id]
                if worker_ids:
                    employees_query = employees_query.filter(Employee.id.in_(worker_ids))
                else:
                    employees_query = employees_query.filter(Employee.id == -1)
        elif filter_type == 'location' and filter_id:
            place_ids = Place.query.filter_by(location_id=int(filter_id)).all()
            worker_ids = [p.worker_id for p in place_ids if p.worker_id]
            if worker_ids:
                employees_query = employees_query.filter(Employee.id.in_(worker_ids))
            else:
                employees_query = employees_query.filter(Employee.id == -1)

        employees = employees_query.all()
        employee_ids = [e.id for e in employees]

        # جلب سجلات المصدر
        source_records = []
        if employee_ids:
            source_records = Attendance.query.filter(
                Attendance.employee_id.in_(employee_ids),
                Attendance.date >= source_start,
                Attendance.date <= source_end
            ).all()

        # تجميع سجلات المصدر
        source_map = {}
        for record in source_records:
            key = f"{record.employee_id}_{record.date}"
            source_map[key] = record

        # حذف السجلات الموجودة في الهدف إذا كان وضع النسخ غير مفعل (نقل)
        if not copy_mode and employee_ids:
            Attendance.query.filter(
                Attendance.employee_id.in_(employee_ids),
                Attendance.date >= target_start,
                Attendance.date <= target_end
            ).delete(synchronize_session=False)
            db.session.flush()

        # إنشاء سجلات جديدة
        created_count = 0
        skipped_count = 0
        absence_count = 0

        for employee in employees:
            if exclude_management and employee.position in ['owner', 'supervisor', 'monitor']:
                continue

            for day_offset in range(target_days):
                current_date = target_start + timedelta(days=day_offset)

                # التحقق من وجود سجل مسبق
                existing = Attendance.query.filter_by(
                    employee_id=employee.id,
                    date=current_date
                ).first()

                if existing and copy_mode:
                    skipped_count += 1
                    continue

                # البحث عن سجل في المصدر
                source_date = source_start + timedelta(days=day_offset % source_days)
                source_key = f"{employee.id}_{source_date}"
                source_record = source_map.get(source_key)

                if source_record and copy_mode:
                    # نسخ من المصدر
                    new_record = Attendance(
                        employee_id=employee.id,
                        date=current_date,
                        status=source_record.status,
                        shift_type=source_record.shift_type,
                        check_in=source_record.check_in,
                        check_out=source_record.check_out,
                        notes=f"منقول من {source_record.date.strftime('%Y-%m-%d')}"
                    )
                    db.session.add(new_record)
                    created_count += 1
                elif fill_absences and not existing:
                    # تعبئة غياب تلقائي
                    new_record = Attendance(
                        employee_id=employee.id,
                        date=current_date,
                        status='absent',
                        shift_type='morning',
                        notes='غياب تلقائي (تعبئة ذكية)'
                    )
                    db.session.add(new_record)
                    absence_count += 1

        db.session.commit()

        message = f'✅ تم الترحيل بنجاح!\n'
        message += f'📝 سجلات جديدة: {created_count}\n'
        message += f'⚠️ غيابات تلقائية: {absence_count}\n'
        if skipped_count > 0:
            message += f'⏭️ سجلات مكررة: {skipped_count}'

        return jsonify({
            'success': True,
            'message': message,
            'created': created_count,
            'absences': absence_count,
            'skipped': skipped_count
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in transfer_execute: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/attendance/force-transfer-payroll', methods=['POST'])
@login_required
def force_transfer_payroll():
    """ترحيل بيانات الحضور مع استبدال كشف الراتب الموجود"""
    try:
        data = request.get_json()

        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        fill_absences = data.get('fill_absences', True)
        exclude_management = data.get('exclude_management', True)

        month = start_date.month
        year = start_date.year

        # حذف كشوف الرواتب الموجودة لهذا الشهر
        Payroll.query.filter_by(year=year, month=month).delete()

        total_salary = 0
        employee_count = 0
        payrolls_created = []

        for emp_data in data['employees']:
            if exclude_management and emp_data['role'] in ['owner', 'supervisor', 'monitor']:
                continue

            attendance_days = emp_data['attendance_days']
            total_days = emp_data['total_days']

            if fill_absences:
                absence_days = emp_data['absence_days']
            else:
                absence_days = emp_data.get('absence_days', 0)

            salary_per_day = emp_data['base_salary'] / 30 if emp_data['base_salary'] > 0 else 0
            earned_salary = attendance_days * salary_per_day
            deductions = emp_data.get('penalties', 0)
            net_salary = earned_salary - deductions

            payroll = Payroll(
                employee_id=emp_data['id'],
                year=year,
                month=month,
                base_salary=emp_data['base_salary'],
                daily_rate=salary_per_day,
                working_days=total_days,
                present_days=attendance_days,
                absent_days=absence_days,
                late_days=0,
                overtime_hours=0,
                base_pay=earned_salary,
                overtime_pay=0,
                penalty_deduction=deductions,
                total_allowances=0,
                total_deductions=deductions,
                net_salary=net_salary,
                status='pending'
            )

            db.session.add(payroll)
            db.session.flush()

            total_salary += net_salary
            employee_count += 1
            payrolls_created.append({
                'id': payroll.id,
                'employee_id': emp_data['id'],
                'net_salary': net_salary
            })

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'✅ تم استبدال كشف الراتب لـ {employee_count} موظف بنجاح',
            'payroll_id': payrolls_created[0]['id'] if payrolls_created else None,
            'employee_count': employee_count,
            'total_salary': total_salary,
            'payrolls': payrolls_created
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in force_transfer_payroll: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/attendance/period-data')
@login_required
def get_source_data_smart():
    """جلب بيانات الفترة المحددة"""
    try:
        start_date_str = request.args.get('start')
        end_date_str = request.args.get('end')

        if not start_date_str or not end_date_str:
            return jsonify({'success': False, 'message': 'التواريخ مطلوبة'})

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        # جلب جميع الموظفين النشطين
        employees = Employee.query.filter_by(is_active=True).all()

        total_employees = len(employees)
        with_attendance = 0
        without_attendance = 0
        total_attendance_days = 0

        employees_data = []

        for emp in employees:
            # جلب سجلات حضور الموظف في الفترة
            attendance_records = Attendance.query.filter(
                Attendance.employee_id == emp.id,
                Attendance.date.between(start_date, end_date)
            ).all()

            attendance_days = len([r for r in attendance_records if r.status in ['present', 'late']])
            absence_days = len([r for r in attendance_records if r.status == 'absent'])

            if attendance_days > 0:
                with_attendance += 1
            else:
                without_attendance += 1

            total_attendance_days += attendance_days

            # جلب الجزاءات في الفترة
            penalties = Penalty.query.filter(
                Penalty.employee_id == emp.id,
                Penalty.penalty_date.between(start_date, end_date)
            ).all()

            total_penalties = sum(p.amount for p in penalties)

            employees_data.append({
                'id': emp.id,
                'name': emp.full_name,
                'position': emp.position,
                'role': emp.role,
                'company': emp.company.name if emp.company else '-',
                'base_salary': float(emp.base_salary or 0),
                'attendance_days': attendance_days,
                'absence_days': absence_days,
                'penalties': float(total_penalties),
                'has_attendance': attendance_days > 0
            })

        return jsonify({
            'success': True,
            'total_employees': total_employees,
            'with_attendance': with_attendance,
            'without_attendance': without_attendance,
            'total_attendance_days': total_attendance_days,
            'employees': employees_data
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/attendance/transfer-to-payroll', methods=['POST'])
@login_required
def transfer_to_payroll():
    """ترحيل بيانات الحضور إلى كشف الراتب"""
    try:
        data = request.get_json()

        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        fill_absences = data.get('fill_absences', True)
        exclude_management = data.get('exclude_management', True)

        # إنشاء كشف راتب جديد
        payroll = Payroll(
            month=start_date.month,
            year=start_date.year,
            start_date=start_date,
            end_date=end_date,
            created_by=current_user.id,
            status='draft'
        )
        db.session.add(payroll)
        db.session.flush()

        total_salary = 0
        employee_count = 0

        for emp_data in data['employees']:
            # استثناء الإداريين إذا كان الخيار مفعل
            if exclude_management and emp_data['role'] in ['owner', 'supervisor', 'monitor']:
                continue

            # حساب الراتب
            salary_per_day = emp_data['base_salary'] / 30
            earned_salary = emp_data['attendance_days'] * salary_per_day

            # إنشاء سجل راتب للموظف
            payroll_item = PayrollItem(
                payroll_id=payroll.id,
                employee_id=emp_data['id'],
                base_salary=emp_data['base_salary'],
                attendance_days=emp_data['attendance_days'],
                absence_days=emp_data['absence_days'],
                penalties=emp_data['penalties'],
                earned_salary=earned_salary,
                net_salary=earned_salary - emp_data['penalties']
            )
            db.session.add(payroll_item)

            total_salary += payroll_item.net_salary
            employee_count += 1

        payroll.total_salary = total_salary
        payroll.employee_count = employee_count

        db.session.commit()

        return jsonify({
            'success': True,
            'payroll_id': payroll.id,
            'employee_count': employee_count,
            'total_salary': total_salary
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/attendance/transfer-preview', methods=['POST'])
@login_required
def transfer_preview_smart():
    """معاينة الترحيل قبل التنفيذ"""
    try:
        data = request.get_json()

        source_start = datetime.strptime(data['source_start'], '%Y-%m-%d').date()
        source_end = datetime.strptime(data['source_end'], '%Y-%m-%d').date()
        target_start = datetime.strptime(data['target_start'], '%Y-%m-%d').date()
        target_end = datetime.strptime(data['target_end'], '%Y-%m-%d').date()

        filter_type = data.get('filter_type', 'all')
        filter_id = data.get('filter_id')
        copy_mode = data.get('copy_mode', True)
        fill_absences = data.get('fill_absences', True)
        exclude_management = data.get('exclude_management', True)

        # حساب عدد أيام الفترة المصدر والهدف
        source_days = (source_end - source_start).days + 1
        target_days = (target_end - target_start).days + 1

        # بناء استعلام الموظفين حسب الفلترة
        employees_query = Employee.query.filter_by(is_active=True)

        if filter_type == 'company' and filter_id:
            employees_query = employees_query.filter_by(company_id=int(filter_id))
        elif filter_type == 'area' and filter_id:
            # جلب الموظفين في منطقة محددة
            area = Area.query.get(int(filter_id))
            if area:
                # جلب الموظفين في هذه المنطقة (من خلال الأماكن)
                location_ids = [loc.id for loc in area.locations]
                place_ids = Place.query.filter(Place.location_id.in_(location_ids)).all()
                worker_ids = [p.worker_id for p in place_ids if p.worker_id]
                employees_query = employees_query.filter(Employee.id.in_(worker_ids))
        elif filter_type == 'location' and filter_id:
            # جلب الموظفين في موقع محدد
            place_ids = Place.query.filter_by(location_id=int(filter_id)).all()
            worker_ids = [p.worker_id for p in place_ids if p.worker_id]
            employees_query = employees_query.filter(Employee.id.in_(worker_ids))

        employees = employees_query.all()

        # جلب سجلات المصدر
        source_records = Attendance.query.filter(
            Attendance.date >= source_start,
            Attendance.date <= source_end
        )

        if filter_type != 'all' and filter_id:
            # تطبيق فلترة على الموظفين
            employee_ids = [e.id for e in employees]
            source_records = source_records.filter(Attendance.employee_id.in_(employee_ids))

        source_records = source_records.all()

        # تجميع سجلات المصدر حسب الموظف والتاريخ
        source_map = {}
        for record in source_records:
            key = f"{record.employee_id}_{record.date}"
            source_map[key] = record

        # جلب سجلات الهدف الموجودة مسبقاً
        target_records = Attendance.query.filter(
            Attendance.date >= target_start,
            Attendance.date <= target_end
        ).all()

        target_map = {}
        for record in target_records:
            key = f"{record.employee_id}_{record.date}"
            target_map[key] = record

        # حساب إحصائيات المعاينة
        total_possible = len(employees) * target_days
        existing_count = len(target_records)
        new_count = 0
        absence_count = 0
        preview_records = []

        # إنشاء سجلات المعاينة
        for employee in employees:
            # استثناء الإداريين إذا كان الخيار مفعل
            if exclude_management and employee.position in ['owner', 'supervisor', 'monitor']:
                continue

            for day_offset in range(target_days):
                current_date = target_start + timedelta(days=day_offset)
                key = f"{employee.id}_{current_date}"

                # البحث عن سجل في المصدر (بنفس إزاحة اليوم)
                source_date = source_start + timedelta(days=day_offset % source_days)
                source_key = f"{employee.id}_{source_date}"
                source_record = source_map.get(source_key)

                if key in target_map:
                    # سجل موجود مسبقاً
                    action = 'موجود'
                    status = target_map[key].status
                elif source_record and copy_mode:
                    # نسخ من المصدر
                    action = 'نسخ'
                    status = source_record.status
                    new_count += 1
                elif fill_absences:
                    # تعبئة غياب تلقائي
                    action = 'غياب تلقائي'
                    status = 'absent'
                    absence_count += 1
                else:
                    # لا شيء
                    continue

                # تحديد لون الصف
                row_class = ''
                if action == 'موجود':
                    row_class = 'table-info'
                elif action == 'نسخ':
                    row_class = 'table-success'
                elif action == 'غياب تلقائي':
                    row_class = 'table-warning'

                preview_records.append({
                    'employee_id': employee.id,
                    'employee_name': employee.full_name,
                    'position': {
                        'supervisor': 'مشرف',
                        'monitor': 'مراقب',
                        'worker': 'عامل'
                    }.get(employee.position, employee.position),
                    'company': employee.company.name if employee.company else '-',
                    'date': current_date.strftime('%Y-%m-%d'),
                    'action': action,
                    'status': status,
                    'status_ar': 'حاضر' if status == 'present' else 'غائب' if status == 'absent' else 'متأخر',
                    'row_class': row_class
                })

        return jsonify({
            'success': True,
            'stats': {
                'total': len(preview_records),
                'existing': existing_count,
                'new': new_count,
                'absences': absence_count,
                'employees': len(employees),
                'days': target_days
            },
            'records': preview_records[:100]  # حد أقصى 100 سجل للمعاينة
        })

    except Exception as e:
        app.logger.error(f"Error in transfer_preview: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/attendance/transfer-execute', methods=['POST'])
@login_required
def transfer_execute_smart():
    """تنفيذ الترحيل الذكي"""
    try:
        data = request.get_json()

        source_start = datetime.strptime(data['source_start'], '%Y-%m-%d').date()
        source_end = datetime.strptime(data['source_end'], '%Y-%m-%d').date()
        target_start = datetime.strptime(data['target_start'], '%Y-%m-%d').date()
        target_end = datetime.strptime(data['target_end'], '%Y-%m-%d').date()

        filter_type = data.get('filter_type', 'all')
        filter_id = data.get('filter_id')
        copy_mode = data.get('copy_mode', True)
        fill_absences = data.get('fill_absences', True)
        exclude_management = data.get('exclude_management', True)

        source_days = (source_end - source_start).days + 1
        target_days = (target_end - target_start).days + 1

        # بناء استعلام الموظفين حسب الفلترة
        employees_query = Employee.query.filter_by(is_active=True)

        if filter_type == 'company' and filter_id:
            employees_query = employees_query.filter_by(company_id=int(filter_id))
        elif filter_type == 'area' and filter_id:
            area = Area.query.get(int(filter_id))
            if area:
                location_ids = [loc.id for loc in area.locations]
                place_ids = Place.query.filter(Place.location_id.in_(location_ids)).all()
                worker_ids = [p.worker_id for p in place_ids if p.worker_id]
                employees_query = employees_query.filter(Employee.id.in_(worker_ids))
        elif filter_type == 'location' and filter_id:
            place_ids = Place.query.filter_by(location_id=int(filter_id)).all()
            worker_ids = [p.worker_id for p in place_ids if p.worker_id]
            employees_query = employees_query.filter(Employee.id.in_(worker_ids))

        employees = employees_query.all()

        # جلب سجلات المصدر
        source_records = Attendance.query.filter(
            Attendance.date >= source_start,
            Attendance.date <= source_end
        )

        if filter_type != 'all' and filter_id:
            employee_ids = [e.id for e in employees]
            source_records = source_records.filter(Attendance.employee_id.in_(employee_ids))

        source_records = source_records.all()

        # تجميع سجلات المصدر
        source_map = {}
        for record in source_records:
            key = f"{record.employee_id}_{record.date}"
            source_map[key] = record

        # حذف السجلات الموجودة في الهدف إذا كان وضع النسخ غير مفعل (نقل)
        if not copy_mode:
            Attendance.query.filter(
                Attendance.date >= target_start,
                Attendance.date <= target_end
            ).delete()
            db.session.flush()

        # إنشاء سجلات جديدة
        created_count = 0
        skipped_count = 0
        absence_count = 0

        for employee in employees:
            if exclude_management and employee.position in ['owner', 'supervisor', 'monitor']:
                continue

            for day_offset in range(target_days):
                current_date = target_start + timedelta(days=day_offset)
                key = f"{employee.id}_{current_date}"

                # التحقق من وجود سجل مسبق
                existing = Attendance.query.filter_by(
                    employee_id=employee.id,
                    date=current_date
                ).first()

                if existing and copy_mode:
                    skipped_count += 1
                    continue

                # البحث عن سجل في المصدر
                source_date = source_start + timedelta(days=day_offset % source_days)
                source_key = f"{employee.id}_{source_date}"
                source_record = source_map.get(source_key)

                if source_record and copy_mode:
                    # نسخ من المصدر
                    new_record = Attendance(
                        employee_id=employee.id,
                        date=current_date,
                        status=source_record.status,
                        shift_type=source_record.shift_type,
                        check_in=source_record.check_in,
                        check_out=source_record.check_out,
                        notes=f"منقول من {source_record.date.strftime('%Y-%m-%d')}"
                    )
                    db.session.add(new_record)
                    created_count += 1
                elif fill_absences and not existing:
                    # تعبئة غياب تلقائي
                    new_record = Attendance(
                        employee_id=employee.id,
                        date=current_date,
                        status='absent',
                        shift_type='morning',
                        notes='غياب تلقائي (تعبئة ذكية)'
                    )
                    db.session.add(new_record)
                    absence_count += 1

        db.session.commit()

        message = f'✅ تم الترحيل بنجاح!\n'
        message += f'📝 سجلات جديدة: {created_count}\n'
        message += f'⚠️ غيابات تلقائية: {absence_count}\n'
        if skipped_count > 0:
            message += f'⏭️ سجلات مكررة: {skipped_count}'

        return jsonify({
            'success': True,
            'message': message,
            'created': created_count,
            'absences': absence_count,
            'skipped': skipped_count
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in transfer_execute: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================
# ============================================
# تصدير تقرير الحضور
# ============================================
# ============================================
# تصدير تقرير الحضور
# ============================================
@app.route('/reports/attendance-record/export/<export_type>')
@login_required
def export_attendance_record(export_type):
    """تصدير تقرير سجل الحضور"""
    if not check_permission('can_view_attendance_reports'):
        flash('غير مصرح', 'error')
        return redirect(url_for('reports_index'))

    try:
        # الحصول على معاملات الفلترة
        from_date_str = request.args.get('from_date', '')
        to_date_str = request.args.get('to_date', '')
        employee_id = request.args.get('employee_id', type=int)
        company_id = request.args.get('company_id', type=int)

        # معالجة التواريخ
        if from_date_str and to_date_str:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
        else:
            from_date = date.today().replace(day=1)
            to_date = date.today()

        # بناء الاستعلام
        query = Attendance.query.join(Employee).filter(
            Attendance.date >= from_date,
            Attendance.date <= to_date
        )

        if employee_id:
            query = query.filter(Attendance.employee_id == employee_id)
        if company_id:
            query = query.filter(Employee.company_id == company_id)

        attendance_records = query.order_by(Attendance.date.desc()).all()
        today = datetime.now()

        if export_type == 'excel':
            # تجهيز البيانات لملف Excel
            rows = []
            for record in attendance_records:
                rows.append({
                    'التاريخ': record.date.strftime('%Y-%m-%d'),
                    'الموظف': record.employee.full_name if record.employee else '-',
                    'الوظيفة': record.employee.position if record.employee else '-',
                    'الشركة': record.employee.company.name if record.employee and record.employee.company else '-',
                    'الحالة': {
                        'present': 'حاضر',
                        'absent': 'غائب',
                        'late': 'متأخر'
                    }.get(record.status, record.status),
                    'الوردية': 'صباحية' if record.shift_type == 'morning' else 'مسائية',
                    'وقت الحضور': record.check_in.strftime('%H:%M') if record.check_in else '-',
                    'وقت الانصراف': record.check_out.strftime('%H:%M') if record.check_out else '-',
                    'ملاحظات': record.notes or ''
                })

            headers = ['التاريخ', 'الموظف', 'الوظيفة', 'الشركة', 'الحالة', 'الوردية', 'وقت الحضور', 'وقت الانصراف', 'ملاحظات']
            report_name = f"تقرير الحضور {from_date.strftime('%Y-%m-%d')} إلى {to_date.strftime('%Y-%m-%d')}"
            filename_prefix = f"attendance_report_{from_date.strftime('%Y%m%d')}_to_{to_date.strftime('%Y%m%d')}"
            return export_report(export_type, report_name, headers, rows, filename_prefix, 'landscape')

        elif export_type == 'pdf':
            from flask import render_template

            try:
                # تجهيز البيانات للقالب
                records_data = []
                for record in attendance_records:
                    records_data.append({
                        'date': record.date.strftime('%Y-%m-%d'),
                        'employee': record.employee.full_name if record.employee else '-',
                        'position': record.employee.position if record.employee else '-',
                        'company': record.employee.company.name if record.employee and record.employee.company else '-',
                        'status': record.status,
                        'status_text': {
                            'present': 'حاضر',
                            'absent': 'غائب',
                            'late': 'متأخر'
                        }.get(record.status, record.status),
                        'shift': 'صباحية' if record.shift_type == 'morning' else 'مسائية',
                        'check_in': record.check_in.strftime('%H:%M') if record.check_in else '-',
                        'check_out': record.check_out.strftime('%H:%M') if record.check_out else '-'
                    })

                html_content = render_template(
                    'reports/attendance_pdf_report.html',
                    records=records_data,
                    from_date=from_date.strftime('%Y-%m-%d'),
                    to_date=to_date.strftime('%Y-%m-%d'),
                    today=today,
                    current_user=current_user
                )

                # ✅ استخدام الدالة الذكية
                response = export_pdf(html_content, 'attendance_report')
                if response:
                    return response
                else:
                    flash('حدث خطأ في إنشاء PDF', 'error')
                    return redirect(url_for('report_attendance_record', **request.args))

            except Exception as pdf_error:
                app.logger.error(f"PDF Error: {str(pdf_error)}")
                flash(f'حدث خطأ في إنشاء PDF: {str(pdf_error)}', 'error')
                return redirect(url_for('report_attendance_record', **request.args))

    except Exception as e:
        app.logger.error(f"Error exporting attendance: {str(e)}")
        flash(f'حدث خطأ في التصدير: {str(e)}', 'error')
        return redirect(url_for('report_attendance_record', **request.args))

# ============================================
# تصدير تقرير الموظفين المتأخرين
# ============================================
# ============================================
# تصدير تقرير الموظفين المتأخرين
# ============================================
@app.route('/reports/late-employees/export/<export_type>')
@login_required
def export_late_employees(export_type):
    """تصدير تقرير الموظفين المتأخرين"""
    if not check_permission('can_view_attendance_reports'):
        flash('غير مصرح', 'error')
        return redirect(url_for('reports_index'))

    try:
        from datetime import date, timedelta

        thirty_days_ago = date.today() - timedelta(days=30)

        late_records = Attendance.query.filter(
            Attendance.status == 'late',
            Attendance.date >= thirty_days_ago
        ).all()

        late_counts = {}
        for record in late_records:
            if record.employee_id not in late_counts:
                late_counts[record.employee_id] = {
                    'count': 0,
                    'name': record.employee.full_name,
                    'department': record.employee.position,
                    'records': []
                }
            late_counts[record.employee_id]['count'] += 1
            late_counts[record.employee_id]['records'].append(record)

        rows = []
        for emp_id, data in late_counts.items():
            if data['count'] >= 2:
                latest = data['records'][-1]
                rows.append({
                    'name': data['name'],
                    'department': data['department'],
                    'late_date': latest.date.strftime('%Y-%m-%d'),
                    'check_in': latest.check_in.strftime('%H:%M') if latest.check_in else '-',
                    'late_count': data['count']
                })

        today = datetime.now()

        if export_type == 'excel':
            headers = ['الموظف', 'القسم', 'آخر تاريخ تأخير', 'وقت الحضور', 'عدد مرات التأخير']
            report_name = f"تقرير الموظفين المتأخرين {today.strftime('%Y-%m-%d')}"
            filename_prefix = f"late_employees_report_{today.strftime('%Y%m%d')}"
            return export_report(export_type, report_name, headers, rows, filename_prefix, 'portrait')

        elif export_type == 'pdf':
            from flask import render_template

            try:
                html_content = render_template(
                    'reports/late_employees_pdf_report.html',
                    late_employees=rows,
                    today=today,
                    current_user=current_user
                )
                # ✅ استخدام الدالة الذكية
                response = export_pdf(html_content, 'late_employees_report')
                if response:
                    return response
                else:
                    flash('حدث خطأ في إنشاء PDF', 'error')
                    return redirect(url_for('report_late_employees', **request.args))

            except Exception as pdf_error:
                app.logger.error(f"PDF Error: {str(pdf_error)}")
                flash(f'حدث خطأ في إنشاء PDF: {str(pdf_error)}', 'error')
                return redirect(url_for('report_late_employees', **request.args))

    except Exception as e:
        app.logger.error(f"Error exporting late employees: {str(e)}")
        flash(f'حدث خطأ في التصدير: {str(e)}', 'error')
        return redirect(url_for('report_late_employees', **request.args))


# ============================================
# تصدير تقرير كفاءة الموظفين
# ============================================
# ============================================
# تصدير تقرير كفاءة الموظفين
# ============================================
@app.route('/reports/employees-efficiency/export/<export_type>')
@login_required
def export_employees_efficiency(export_type):
    """تصدير تقرير كفاءة الموظفين"""
    if not check_permission('can_view_employee_efficiency'):
        flash('غير مصرح', 'error')
        return redirect(url_for('reports_index'))

    try:
        employees = Employee.query.filter_by(is_active=True).all()
        today = datetime.now()

        # تجهيز بيانات الموظفين للقالب
        employees_data = []
        high_count = 0
        medium_count = 0
        low_count = 0

        for emp in employees:
            evaluations_count = CleaningEvaluation.query.filter_by(evaluated_employee_id=emp.id).count()

            # تحديد مستوى الكفاءة
            if evaluations_count > 10:
                efficiency_level = 'عالية'
                high_count += 1
            elif evaluations_count > 5:
                efficiency_level = 'متوسطة'
                medium_count += 1
            else:
                efficiency_level = 'منخفضة'
                low_count += 1

            # تحديد اسم الوظيفة بالعربية
            if emp.position == 'supervisor':
                position_ar = 'مشرف'
            elif emp.position == 'monitor':
                position_ar = 'مراقب'
            elif emp.position == 'worker':
                position_ar = 'عامل'
            else:
                position_ar = emp.position

            employees_data.append({
                'full_name': emp.full_name,
                'position_ar': position_ar,
                'company_name': emp.company.name if emp.company else '-',
                'evaluations_count': evaluations_count,
                'efficiency_level': efficiency_level
            })

        # بيانات Excel
        if export_type == 'excel':
            rows = []
            for emp in employees_data:
                rows.append({
                    'الموظف': emp['full_name'],
                    'الوظيفة': emp['position_ar'],
                    'الشركة': emp['company_name'],
                    'عدد التقييمات': emp['evaluations_count'],
                    'مستوى الكفاءة': emp['efficiency_level']
                })

            headers = ['الموظف', 'الوظيفة', 'الشركة', 'عدد التقييمات', 'مستوى الكفاءة']
            report_name = f"تقرير كفاءة الموظفين {today.strftime('%Y-%m-%d')}"
            filename_prefix = f"efficiency_report_{today.strftime('%Y%m%d')}"
            return export_report(export_type, report_name, headers, rows, filename_prefix, 'portrait')

        # بيانات PDF
        elif export_type == 'pdf':
            from flask import render_template

            try:
                html_content = render_template(
                    'reports/efficiency_pdf_report.html',
                    employees=employees_data,
                    high_efficiency=high_count,
                    medium_efficiency=medium_count,
                    low_efficiency=low_count,
                    today=today,
                    current_user=current_user
                )

                # ✅ استخدام الدالة الذكية
                response = export_pdf(html_content, 'efficiency_report')
                if response:
                    return response
                else:
                    flash('حدث خطأ في إنشاء PDF', 'error')
                    return redirect(url_for('report_employees_efficiency', **request.args))

            except Exception as pdf_error:
                app.logger.error(f"PDF Error: {str(pdf_error)}")
                import traceback
                traceback.print_exc()
                flash(f'حدث خطأ في إنشاء PDF: {str(pdf_error)}', 'error')
                return redirect(url_for('report_employees_efficiency', **request.args))

    except Exception as e:
        app.logger.error(f"Error exporting efficiency: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'حدث خطأ في التصدير: {str(e)}', 'error')
        return redirect(url_for('report_employees_efficiency', **request.args))

# ============================================
# تصدير تقرير الغياب والتأخير
# ============================================
# ============================================
# تصدير تقرير الغياب والتأخير
# ============================================
@app.route('/reports/absence-rates/export/<export_type>')
@login_required
def export_absence_rates(export_type):
    """تصدير تقرير الغياب والتأخير"""
    if not check_permission('can_view_attendance_reports'):
        flash('غير مصرح', 'error')
        return redirect(url_for('reports_index'))

    try:
        from_date_str = request.args.get('from_date', '')
        to_date_str = request.args.get('to_date', '')

        if from_date_str and to_date_str:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
        else:
            to_date = date.today()
            from_date = to_date - timedelta(days=30)

        # جلب جميع الموظفين النشطين
        employees = Employee.query.filter_by(is_active=True).all()
        today = datetime.now()

        rows = []
        for emp in employees:
            absent_days = Attendance.query.filter(
                Attendance.employee_id == emp.id,
                Attendance.date >= from_date,
                Attendance.date <= to_date,
                Attendance.status == 'absent'
            ).count()

            late_days = Attendance.query.filter(
                Attendance.employee_id == emp.id,
                Attendance.date >= from_date,
                Attendance.date <= to_date,
                Attendance.status == 'late'
            ).count()

            total_days = (to_date - from_date).days + 1
            absence_rate = round((absent_days / total_days) * 100, 1) if total_days > 0 else 0

            if absent_days > 0 or late_days > 0:
                rows.append({
                    'الموظف': emp.full_name,
                    'الوظيفة': emp.position,
                    'الشركة': emp.company.name if emp.company else '-',
                    'أيام الغياب': absent_days,
                    'نسبة الغياب': f"{absence_rate}%",
                    'أيام التأخير': late_days,
                    'إجمالي': absent_days + late_days
                })

        if export_type == 'excel':
            headers = ['الموظف', 'الوظيفة', 'الشركة', 'أيام الغياب', 'نسبة الغياب', 'أيام التأخير', 'إجمالي']
            report_name = f"تقرير الغياب {from_date.strftime('%Y-%m-%d')} إلى {to_date.strftime('%Y-%m-%d')}"
            filename_prefix = f"absence_report_{from_date.strftime('%Y%m%d')}_to_{to_date.strftime('%Y%m%d')}"
            return export_report(export_type, report_name, headers, rows, filename_prefix, 'portrait')

        elif export_type == 'pdf':
            from flask import render_template

            try:
                html_content = render_template(
                    'reports/absence_pdf_report.html',
                    rows=rows,
                    from_date=from_date.strftime('%Y-%m-%d'),
                    to_date=to_date.strftime('%Y-%m-%d'),
                    today=today,
                    current_user=current_user
                )

                # ✅ استخدام الدالة الذكية
                response = export_pdf(html_content, 'absence_report')
                if response:
                    return response
                else:
                    flash('حدث خطأ في إنشاء PDF', 'error')
                    return redirect(url_for('report_absence_rates', **request.args))

            except Exception as pdf_error:
                app.logger.error(f"PDF Error: {str(pdf_error)}")
                flash(f'حدث خطأ في إنشاء PDF: {str(pdf_error)}', 'error')
                return redirect(url_for('report_absence_rates', **request.args))

    except Exception as e:
        app.logger.error(f"Error exporting absence: {str(e)}")
        flash(f'حدث خطأ في التصدير: {str(e)}', 'error')
        return redirect(url_for('report_absence_rates', **request.args))

# ============================================
# تصدير تقرير تقييمات الموظفين
# ============================================
# ============================================
# تصدير تقرير تقييمات الموظفين
# ============================================
@app.route('/reports/evaluations/export/<export_type>')
@login_required
def export_evaluations_report(export_type):
    """تصدير تقرير تقييمات الموظفين"""
    if not check_permission('can_view_evaluations'):
        flash('غير مصرح', 'error')
        return redirect(url_for('reports_index'))

    try:
        from_date_str = request.args.get('from_date', '')
        to_date_str = request.args.get('to_date', '')
        employee_id = request.args.get('employee_id', type=int)

        if from_date_str and to_date_str:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
        else:
            to_date = date.today()
            from_date = to_date - timedelta(days=30)

        # بناء الاستعلام
        query = CleaningEvaluation.query.filter(
            CleaningEvaluation.date >= from_date,
            CleaningEvaluation.date <= to_date
        )

        if employee_id:
            query = query.filter_by(evaluated_employee_id=employee_id)

        evaluations = query.order_by(CleaningEvaluation.date.desc()).all()
        today = datetime.now()

        if export_type == 'excel':
            rows = []
            for eval in evaluations:
                rows.append({
                    'التاريخ': eval.date.strftime('%Y-%m-%d'),
                    'الموظف': eval.evaluated_employee.full_name if eval.evaluated_employee else '-',
                    'المقيم': eval.evaluator.full_name if eval.evaluator else '-',
                    'المكان': eval.place.name if eval.place else '-',
                    'النظافة': eval.cleanliness,
                    'التنظيم': eval.organization,
                    'المعدات': eval.equipment_condition,
                    'السلامة': eval.safety_measures,
                    'النتيجة': f"{eval.overall_score * 20:.1f}%",
                    'ملاحظات': eval.comments or ''
                })

            headers = ['التاريخ', 'الموظف', 'المقيم', 'المكان', 'النظافة', 'التنظيم', 'المعدات', 'السلامة', 'النتيجة',
                       'ملاحظات']
            report_name = f"تقرير التقييمات {from_date.strftime('%Y-%m-%d')} إلى {to_date.strftime('%Y-%m-%d')}"
            filename_prefix = f"evaluations_report_{from_date.strftime('%Y%m%d')}_to_{to_date.strftime('%Y%m%d')}"
            return export_report(export_type, report_name, headers, rows, filename_prefix, 'landscape')

        elif export_type == 'pdf':
            from flask import render_template

            try:
                # تجهيز البيانات للقالب
                eval_data = []
                for e in evaluations:
                    eval_data.append({
                        'date': e.date.strftime('%Y-%m-%d'),
                        'employee': e.evaluated_employee.full_name if e.evaluated_employee else '-',
                        'evaluator': e.evaluator.full_name if e.evaluator else '-',
                        'place': e.place.name if e.place else '-',
                        'cleanliness': e.cleanliness,
                        'organization': e.organization,
                        'equipment': e.equipment_condition,
                        'safety': e.safety_measures,
                        'result': f"{e.overall_score * 20:.1f}%"
                    })

                html_content = render_template(
                    'reports/evaluations_pdf_report.html',
                    evaluations=eval_data,
                    from_date=from_date.strftime('%Y-%m-%d'),
                    to_date=to_date.strftime('%Y-%m-%d'),
                    today=today,
                    current_user=current_user
                )

                # ✅ استخدام الدالة الذكية
                response = export_pdf(html_content, 'evaluations_report')
                if response:
                    return response
                else:
                    flash('حدث خطأ في إنشاء PDF', 'error')
                    return redirect(url_for('evaluations_list', **request.args))

            except Exception as pdf_error:
                app.logger.error(f"PDF Error: {str(pdf_error)}")
                flash(f'حدث خطأ في إنشاء PDF: {str(pdf_error)}', 'error')
                return redirect(url_for('evaluations_list', **request.args))

    except Exception as e:
        app.logger.error(f"Error exporting evaluations: {str(e)}")
        flash(f'حدث خطأ في التصدير: {str(e)}', 'error')
        return redirect(url_for('evaluations_list', **request.args))


# ============================================
# تصدير تقرير التقييمات اليومية المتقدم
# ============================================
# ============================================
# تصدير تقرير التقييمات اليومية المتقدم
# ============================================
@app.route('/reports/daily-evaluations-advanced/export/<export_type>')
@login_required
def export_daily_evaluations_advanced(export_type):
    """تصدير تقرير التقييمات اليومية المتقدم"""
    if not check_permission('can_view_detailed_evaluations'):
        flash('غير مصرح', 'error')
        return redirect(url_for('reports_index'))

    try:
        today = date.today()
        selected_date_param = request.args.get('date', today.isoformat())
        selected_date = datetime.strptime(selected_date_param, '%Y-%m-%d').date()

        # استخدام الدالة المساعدة لجلب التقييمات المفلترة
        all_filtered_evaluations = get_filtered_evaluations(current_user)
        evaluations = [e for e in all_filtered_evaluations if e.date == selected_date]

        # إحصائيات
        total = len(evaluations)
        if total > 0:
            scores = [e.overall_score for e in evaluations if e.overall_score]
            avg_score = sum(scores) / len(scores) if scores else 0
            excellent_count = len([e for e in evaluations if e.overall_score and e.overall_score >= 4.5])
            poor_count = len([e for e in evaluations if e.overall_score and e.overall_score <= 3])
        else:
            avg_score = 0
            excellent_count = 0
            poor_count = 0

        daily_stats = {
            'total': total,
            'avg_score': round(avg_score, 1),
            'excellent_count': excellent_count,
            'poor_count': poor_count
        }

        # تجهيز بيانات التقييمات
        evaluations_data = []
        for e in evaluations:
            evaluations_data.append({
                'created_at': e.created_at.strftime('%H:%M') if e.created_at else '-',
                'employee': {
                    'full_name': e.evaluated_employee.full_name if e.evaluated_employee else '-'
                },
                'evaluator': e.evaluator.full_name if e.evaluator else '-',
                'location': e.place.name if e.place else '-',
                'cleanliness': e.cleanliness,
                'organization': e.organization,
                'equipment': e.equipment_condition,
                'safety': e.safety_measures,
                'result': f"{e.overall_score * 20:.1f}%" if e.overall_score else '0%'
            })

        now = datetime.now()

        if export_type == 'excel':
            rows = []
            for e in evaluations:
                rows.append({
                    'الوقت': e.created_at.strftime('%H:%M') if e.created_at else '-',
                    'الموظف': e.evaluated_employee.full_name if e.evaluated_employee else '-',
                    'المقيم': e.evaluator.full_name if e.evaluator else '-',
                    'المكان': e.place.name if e.place else '-',
                    'النظافة': e.cleanliness,
                    'التنظيم': e.organization,
                    'المعدات': e.equipment_condition,
                    'السلامة': e.safety_measures,
                    'النتيجة': f"{e.overall_score * 20:.1f}%" if e.overall_score else '0%'
                })

            headers = ['الوقت', 'الموظف', 'المقيم', 'المكان', 'النظافة', 'التنظيم', 'المعدات', 'السلامة', 'النتيجة']
            report_name = f"تقرير التقييمات اليومية {selected_date.strftime('%Y-%m-%d')}"
            filename_prefix = f"daily_evaluations_{selected_date.strftime('%Y%m%d')}"
            return export_report(export_type, report_name, headers, rows, filename_prefix, 'landscape')

        elif export_type == 'pdf':
            from flask import render_template

            try:
                html_content = render_template(
                    'reports/daily_evaluations_pdf_report.html',
                    evaluations=evaluations_data,
                    daily_stats=daily_stats,
                    selected_date=selected_date.strftime('%Y-%m-%d'),
                    today=now,
                    current_user=current_user
                )

                # ✅ استخدام الدالة الذكية
                response = export_pdf(html_content, 'daily_evaluations_report')
                if response:
                    return response
                else:
                    flash('حدث خطأ في إنشاء PDF', 'error')
                    return redirect(url_for('report_daily_evaluations_advanced', **request.args))

            except Exception as pdf_error:
                app.logger.error(f"PDF Error: {str(pdf_error)}")
                flash(f'حدث خطأ في إنشاء PDF: {str(pdf_error)}', 'error')
                return redirect(url_for('report_daily_evaluations_advanced', **request.args))

    except Exception as e:
        app.logger.error(f"Error exporting daily evaluations: {str(e)}")
        flash(f'حدث خطأ في التصدير: {str(e)}', 'error')
        return redirect(url_for('report_daily_evaluations_advanced', **request.args))


# ============================================
# تصدير تقرير أداء الموظفين
# ============================================
@app.route('/reports/employees-performance/export/<export_type>')
@login_required
def export_employees_performance(export_type):
    """تصدير تقرير أداء الموظفين"""
    if not check_permission('can_view_performance'):
        flash('غير مصرح', 'error')
        return redirect(url_for('reports_index'))

    try:
        employees = Employee.query.filter_by(is_active=True).all()
        today = datetime.now()

        rows = []
        for emp in employees:
            evaluations = CleaningEvaluation.query.filter_by(evaluated_employee_id=emp.id).all()
            if evaluations:
                avg_score = sum(e.overall_score for e in evaluations) / len(evaluations)
                performance = avg_score * 20
            else:
                performance = 0

            attendance_days = Attendance.query.filter_by(employee_id=emp.id, status='present').count()

            rows.append({
                'الموظف': emp.full_name,
                'الوظيفة': emp.position,
                'الشركة': emp.company.name if emp.company else '-',
                'عدد التقييمات': len(evaluations),
                'متوسط الأداء': f"{performance:.1f}%",
                'أيام الحضور': attendance_days,
                'الحالة': 'نشط' if emp.is_active else 'غير نشط'
            })

        if export_type == 'excel':
            headers = ['الموظف', 'الوظيفة', 'الشركة', 'عدد التقييمات', 'متوسط الأداء', 'أيام الحضور', 'الحالة']
            report_name = f"تقرير أداء الموظفين {today.strftime('%Y-%m-%d')}"
            filename_prefix = f"performance_report_{today.strftime('%Y%m%d')}"
            return export_report(export_type, report_name, headers, rows, filename_prefix, 'landscape')

        elif export_type == 'pdf':
            from flask import render_template

            try:
                # تجهيز البيانات للقالب
                performance_data = []
                for r in rows:
                    performance_data.append({
                        'employee': r['الموظف'],
                        'position': r['الوظيفة'],
                        'company': r['الشركة'],
                        'evaluations': r['عدد التقييمات'],
                        'avg_performance': r['متوسط الأداء'],
                        'attendance_days': r['أيام الحضور'],
                        'status': r['الحالة']
                    })

                html_content = render_template(
                    'reports/performance_pdf_report.html',
                    performance=performance_data,
                    today=today,
                    current_user=current_user
                )

                # ✅ استخدام الدالة الذكية
                response = export_pdf(html_content, 'performance_report')
                if response:
                    return response
                else:
                    flash('حدث خطأ في إنشاء PDF', 'error')
                    return redirect(url_for('report_employees_performance', **request.args))

            except Exception as pdf_error:
                app.logger.error(f"PDF Error: {str(pdf_error)}")
                flash(f'حدث خطأ في إنشاء PDF: {str(pdf_error)}', 'error')
                return redirect(url_for('report_employees_performance', **request.args))

    except Exception as e:
        app.logger.error(f"Error exporting performance: {str(e)}")
        flash(f'حدث خطأ في التصدير: {str(e)}', 'error')
        return redirect(url_for('report_employees_performance', **request.args))

# ============================================
# تصدير تقرير مؤشرات الأداء
# ============================================
# ============================================
# تصدير تقرير مؤشرات الأداء
# ============================================
@app.route('/reports/kpis/export/<export_type>')
@login_required
def export_kpis_report(export_type):
    """تصدير تقرير مؤشرات الأداء"""
    if not check_permission('can_view_kpis'):
        flash('غير مصرح', 'error')
        return redirect(url_for('reports_index'))

    try:
        total_employees = Employee.query.filter_by(is_active=True).count()
        total_evaluations = CleaningEvaluation.query.count()
        total_companies = Company.query.filter_by(is_active=True).count()

        kpis = {
            'employee_productivity': 85,
            'attendance_rate': 92,
            'evaluation_coverage': 78,
            'customer_satisfaction': 88,
            'task_completion': 82,
            'quality_score': 90
        }

        rows = [{
            'المؤشر': kpi_name,
            'القيمة': f"{kpi_value}%"
        } for kpi_name, kpi_value in kpis.items()]

        rows.append({'المؤشر': 'إجمالي الموظفين', 'القيمة': total_employees})
        rows.append({'المؤشر': 'إجمالي التقييمات', 'القيمة': total_evaluations})
        rows.append({'المؤشر': 'إجمالي الشركات', 'القيمة': total_companies})

        today = datetime.now()

        if export_type == 'excel':
            headers = ['المؤشر', 'القيمة']
            report_name = f"تقرير مؤشرات الأداء {today.strftime('%Y-%m-%d')}"
            filename_prefix = f"kpis_report_{today.strftime('%Y%m%d')}"
            return export_report(export_type, report_name, headers, rows, filename_prefix, 'portrait')

        elif export_type == 'pdf':
            from flask import render_template

            try:
                html_content = render_template(
                    'reports/kpis_pdf_report.html',
                    kpis=kpis,
                    total_employees=total_employees,
                    total_evaluations=total_evaluations,
                    total_companies=total_companies,
                    today=today,
                    current_user=current_user
                )

                # ✅ استخدام الدالة الذكية
                response = export_pdf(html_content, 'kpis_report')
                if response:
                    return response
                else:
                    flash('حدث خطأ في إنشاء PDF', 'error')
                    return redirect(url_for('report_kpis', **request.args))

            except Exception as pdf_error:
                app.logger.error(f"PDF Error: {str(pdf_error)}")
                flash(f'حدث خطأ في إنشاء PDF: {str(pdf_error)}', 'error')
                return redirect(url_for('report_kpis', **request.args))

    except Exception as e:
        app.logger.error(f"Error exporting kpis: {str(e)}")
        flash(f'حدث خطأ في التصدير: {str(e)}', 'error')
        return redirect(url_for('report_kpis', **request.args))

# ============================================
# تصدير تقرير أفضل الموظفين
# ============================================
# ============================================
# تصدير تقرير أفضل الموظفين
# ============================================
@app.route('/reports/top-employees/export/<export_type>')
@login_required
def export_top_employees(export_type):
    """تصدير تقرير أفضل الموظفين"""
    if not check_permission('can_view_top_employees'):
        flash('غير مصرح', 'error')
        return redirect(url_for('reports_index'))

    try:
        from_date_str = request.args.get('from_date', '')
        to_date_str = request.args.get('to_date', '')
        company_id = request.args.get('company_id', type=int)

        if from_date_str and to_date_str:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
        else:
            to_date = date.today()
            from_date = to_date - timedelta(days=30)

        # بناء استعلام الموظفين
        query = Employee.query.filter_by(is_active=True)
        if company_id:
            query = query.filter_by(company_id=company_id)

        employees = query.all()

        employees_data = []
        for emp in employees:
            evaluations = CleaningEvaluation.query.filter(
                CleaningEvaluation.evaluated_employee_id == emp.id,
                CleaningEvaluation.date >= from_date,
                CleaningEvaluation.date <= to_date
            ).all()

            if evaluations:
                avg_score = sum(e.overall_score for e in evaluations) / len(evaluations)
                performance = avg_score * 20
            else:
                performance = 0

            attendance_days = Attendance.query.filter(
                Attendance.employee_id == emp.id,
                Attendance.date >= from_date,
                Attendance.date <= to_date,
                Attendance.status.in_(['present', 'late'])
            ).count()

            total_days = (to_date - from_date).days + 1
            attendance_rate = round((attendance_days / total_days) * 100, 1) if total_days > 0 else 0

            # تحديد اسم الوظيفة بالعربية
            position_ar = {
                'supervisor': 'مشرف',
                'monitor': 'مراقب',
                'worker': 'عامل',
                'admin': 'إداري',
                'owner': 'مالك'
            }.get(emp.position, emp.position)

            employees_data.append({
                'الموظف': emp.full_name,
                'الوظيفة': position_ar,
                'الشركة': emp.company.name if emp.company else '-',
                'عدد التقييمات': len(evaluations),
                'معدل الأداء': f"{performance:.1f}%",
                'أيام الحضور': attendance_days,
                'نسبة الحضور': f"{attendance_rate}%"
            })

        # ترتيب حسب الأداء
        employees_data.sort(key=lambda x: float(x['معدل الأداء'].replace('%', '')), reverse=True)

        today = datetime.now()

        if export_type == 'excel':
            headers = ['الموظف', 'الوظيفة', 'الشركة', 'عدد التقييمات', 'معدل الأداء', 'أيام الحضور', 'نسبة الحضور']
            report_name = f"تقرير أفضل الموظفين {from_date.strftime('%Y-%m-%d')} إلى {to_date.strftime('%Y-%m-%d')}"
            filename_prefix = f"top_employees_{from_date.strftime('%Y%m%d')}_to_{to_date.strftime('%Y%m%d')}"
            return export_report(export_type, report_name, headers, employees_data, filename_prefix, 'landscape')

        elif export_type == 'pdf':
            from flask import render_template

            try:
                html_content = render_template(
                    'reports/top_employees_pdf_report.html',
                    employees_data=employees_data,
                    from_date=from_date.strftime('%Y-%m-%d'),
                    to_date=to_date.strftime('%Y-%m-%d'),
                    today=today,
                    current_user=current_user
                )

                # ✅ استخدام الدالة الذكية
                response = export_pdf(html_content, 'top_employees_report')
                if response:
                    return response
                else:
                    flash('حدث خطأ في إنشاء PDF', 'error')
                    return redirect(url_for('report_top_employees', **request.args))

            except Exception as pdf_error:
                app.logger.error(f"PDF Error: {str(pdf_error)}")
                import traceback
                traceback.print_exc()
                flash(f'حدث خطأ في إنشاء PDF: {str(pdf_error)}', 'error')
                return redirect(url_for('report_top_employees', **request.args))

    except Exception as e:
        app.logger.error(f"Error exporting top employees: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'حدث خطأ في التصدير: {str(e)}', 'error')
        return redirect(url_for('report_top_employees', **request.args))

# ============================================
# تصدير تقرير الشركات والمناطق
# ============================================
@app.route('/reports/companies-zones/export/<export_type>')
@login_required
def export_companies_zones(export_type):
    """تصدير تقرير الشركات والمناطق"""
    if not check_permission('can_view_companies'):
        flash('غير مصرح', 'error')
        return redirect(url_for('reports_index'))

    try:
        companies = Company.query.filter_by(is_active=True).all()

        # إحصائيات عامة
        total_companies = len(companies)
        total_areas = Area.query.filter_by(is_active=True).count()
        total_locations = Location.query.filter_by(is_active=True).count()

        # تجميع بيانات الشركات
        companies_data = []
        all_ratings = []

        for company in companies:
            areas = Area.query.filter_by(company_id=company.id, is_active=True).all()
            employees_count = Employee.query.filter_by(company_id=company.id, is_active=True).count()

            # حساب متوسط التقييم للشركة
            ratings = []
            for area in areas:
                locations = Location.query.filter_by(area_id=area.id, is_active=True).all()
                for location in locations:
                    places = Place.query.filter_by(location_id=location.id, is_active=True).all()
                    for place in places:
                        evals = CleaningEvaluation.query.filter_by(place_id=place.id).all()
                        ratings.extend([e.overall_score for e in evals if e.overall_score])

            avg_rating = (sum(ratings) / len(ratings)) * 20 if ratings else 0
            all_ratings.extend(ratings)

            companies_data.append({
                'name': company.name,
                'areas_count': len(areas),
                'employees_count': employees_count,
                'rating': round(avg_rating, 1),
                'is_active': company.is_active
            })

        # حساب المتوسطات
        avg_company_rating = (sum(all_ratings) / len(all_ratings)) * 20 if all_ratings else 0
        avg_areas_per_company = round(total_areas / total_companies, 1) if total_companies > 0 else 0
        avg_locations_per_area = round(total_locations / total_areas, 1) if total_areas > 0 else 0

        # أعلى شركة تقييماً
        top_rated = max(companies_data, key=lambda x: x['rating']) if companies_data else {'name': '-', 'rating': 0}

        today = datetime.now()

        # تجهيز بيانات Excel
        if export_type == 'excel':
            rows = []
            for company in companies_data:
                rows.append({
                    'الشركة': company['name'],
                    'عدد المناطق': company['areas_count'],
                    'عدد الموظفين': company['employees_count'],
                    'متوسط التقييم': f"{company['rating']}%",
                    'الحالة': 'نشط' if company['is_active'] else 'غير نشط'
                })

            headers = ['الشركة', 'عدد المناطق', 'عدد الموظفين', 'متوسط التقييم', 'الحالة']
            report_name = f"تقرير الشركات والمناطق {today.strftime('%Y-%m-%d')}"
            filename_prefix = f"companies_report_{today.strftime('%Y%m%d')}"
            return export_report(export_type, report_name, headers, rows, filename_prefix, 'portrait')

        # تجهيز بيانات PDF
        elif export_type == 'pdf':
            from flask import render_template

            try:
                html_content = render_template(
                    'reports/companies_zones_pdf_report.html',
                    companies=companies,
                    companies_data=companies_data,
                    total_companies=total_companies,
                    total_areas=total_areas,
                    total_locations=total_locations,
                    avg_company_rating=round(avg_company_rating, 1),
                    avg_areas_per_company=avg_areas_per_company,
                    avg_locations_per_area=avg_locations_per_area,
                    top_rated_company=top_rated['name'],
                    today=today,
                    current_user=current_user
                )

                # ✅ استخدام الدالة الذكية
                response = export_pdf(html_content, 'companies_report')
                if response:
                    return response
                else:
                    flash('حدث خطأ في إنشاء PDF', 'error')
                    return redirect(url_for('report_companies_zones', **request.args))

            except Exception as pdf_error:
                app.logger.error(f"PDF Error: {str(pdf_error)}")
                import traceback
                traceback.print_exc()
                flash(f'حدث خطأ في إنشاء PDF: {str(pdf_error)}', 'error')
                return redirect(url_for('report_companies_zones', **request.args))

    except Exception as e:
        app.logger.error(f"Error exporting companies zones: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'حدث خطأ في التصدير: {str(e)}', 'error')
        return redirect(url_for('report_companies_zones', **request.args))

# ============================================
# تصدير تقرير الاتجاهات الشهرية
# ============================================
@app.route('/reports/monthly-trends/export/<export_type>')
@login_required
def export_monthly_trends(export_type):
    """تصدير تقرير الاتجاهات الشهرية"""
    try:
        from datetime import date, timedelta

        months = []
        evaluations_count = []

        for i in range(6):
            month_date = date.today() - timedelta(days=30 * i)
            month_name = month_date.strftime('%B')
            months.append(month_name)

            count = CleaningEvaluation.query.filter(
                CleaningEvaluation.date >= month_date - timedelta(days=30),
                CleaningEvaluation.date < month_date
            ).count()
            evaluations_count.append(count)

        rows = []
        months_data = []
        for i in range(6):
            rows.append({
                'الشهر': months[i],
                'عدد التقييمات': evaluations_count[i]
            })
            months_data.append((months[i], evaluations_count[i]))

        today = datetime.now()

        if export_type == 'excel':
            headers = ['الشهر', 'عدد التقييمات']
            report_name = f"تقرير الاتجاهات الشهرية {today.strftime('%Y-%m-%d')}"
            filename_prefix = f"monthly_trends_report_{today.strftime('%Y%m%d')}"
            return export_report(export_type, report_name, headers, rows, filename_prefix, 'portrait')

        elif export_type == 'pdf':
            from flask import render_template

            try:
                html_content = render_template(
                    'reports/monthly_trends_pdf_report.html',
                    months_data=months_data,
                    today=today,
                    current_user=current_user
                )

                # ✅ استخدام الدالة الذكية
                response = export_pdf(html_content, 'monthly_trends_report')
                if response:
                    return response
                else:
                    flash('حدث خطأ في إنشاء PDF', 'error')
                    return redirect(url_for('report_monthly_trends', **request.args))

            except Exception as pdf_error:
                app.logger.error(f"PDF Error: {str(pdf_error)}")
                flash(f'حدث خطأ في إنشاء PDF: {str(pdf_error)}', 'error')
                return redirect(url_for('report_monthly_trends', **request.args))

    except Exception as e:
        app.logger.error(f"Error exporting monthly trends: {str(e)}")
        flash(f'حدث خطأ في التصدير: {str(e)}', 'error')
        return redirect(url_for('report_monthly_trends', **request.args))


# ============================================
# تصدير تقرير السلف
# ============================================
@app.route('/reports/loans/export/<export_type>')
@login_required
def export_loans_report(export_type):
    """تصدير تقرير السلف"""
    if current_user.role != 'owner':
        flash('غير مصرح', 'error')
        return redirect(url_for('dashboard'))

    try:
        from models import EmployeeLoan, Employee

        # الحصول على معاملات الفلترة
        employee_id = request.args.get('employee_id', type=int)
        status = request.args.get('status', '')
        from_date_str = request.args.get('from_date', '')
        to_date_str = request.args.get('to_date', '')

        # بناء الاستعلام
        query = EmployeeLoan.query

        if employee_id:
            query = query.filter_by(employee_id=employee_id)
        if status:
            query = query.filter_by(status=status)
        if from_date_str:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            query = query.filter(EmployeeLoan.loan_date >= from_date)
        if to_date_str:
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
            query = query.filter(EmployeeLoan.loan_date <= to_date)

        loans = query.order_by(EmployeeLoan.loan_date.desc()).all()

        # جلب جميع الموظفين للفلتر
        employees = Employee.query.filter_by(is_active=True).all()

        # حساب الإحصائيات
        total_loans = sum(loan.amount for loan in loans)
        total_paid = sum(loan.paid_amount for loan in loans)
        total_remaining = total_loans - total_paid
        active_loans = sum(1 for loan in loans if loan.status == 'active')
        paid_loans = sum(1 for loan in loans if loan.status == 'paid')

        today = datetime.now()

        if export_type == 'excel':
            # تجهيز البيانات لملف Excel
            rows = []
            for loan in loans:
                rows.append({
                    'التاريخ': loan.loan_date.strftime('%Y-%m-%d'),
                    'الموظف': loan.employee.full_name if loan.employee else '-',
                    'المبلغ': loan.amount,
                    'عدد الأقساط': loan.installments,
                    'القسط الشهري': loan.monthly_installment,
                    'المدفوع': loan.paid_amount,
                    'المتبقي': loan.remaining,
                    'الحالة': 'نشط' if loan.status == 'active' else 'مسدد' if loan.status == 'paid' else 'ملغي',
                    'السبب': loan.reason or ''
                })

            headers = ['التاريخ', 'الموظف', 'المبلغ', 'عدد الأقساط', 'القسط الشهري', 'المدفوع', 'المتبقي', 'الحالة',
                       'السبب']
            report_name = f"تقرير السلف {today.strftime('%Y-%m-%d')}"
            filename_prefix = f"loans_report_{today.strftime('%Y%m%d')}"

            return export_report(export_type, report_name, headers, rows, filename_prefix, 'landscape')

        elif export_type == 'pdf':
            from flask import render_template

            try:
                # استخدام القالب المبسط
                template_name = 'financial/loans_pdf_simple.html'

                html_content = render_template(
                    template_name,
                    loans=loans,
                    employees=employees,
                    total_loans=total_loans,
                    total_paid=total_paid,
                    total_remaining=total_remaining,
                    active_loans=active_loans,
                    paid_loans=paid_loans,
                    today=today,
                    current_user=current_user,
                    from_date=from_date_str,
                    to_date=to_date_str,
                    selected_employee=employee_id,
                    selected_status=status
                )

                # ✅ استخدام الدالة الذكية
                response = export_pdf(html_content, 'loans_report')
                if response:
                    return response
                else:
                    flash('حدث خطأ في إنشاء PDF', 'error')
                    return redirect(url_for('loans_list', **request.args))

            except Exception as pdf_error:
                app.logger.error(f"PDF Generation Error: {str(pdf_error)}")
                flash(f'حدث خطأ في إنشاء PDF: {str(pdf_error)}', 'error')
                return redirect(url_for('loans_list', **request.args))

    except Exception as e:
        app.logger.error(f"Error exporting loans: {str(e)}")
        flash(f'حدث خطأ في التصدير: {str(e)}', 'error')
        return redirect(url_for('loans_list', **request.args))

# ============================================
# تصدير تقرير الجزاءات
# ============================================
@app.route('/reports/penalties/export/<export_type>')
@login_required
def export_penalties_report(export_type):
    """تصدير تقرير الجزاءات"""

    # ===== كود التشخيص =====
    print("\n" + "=" * 50)
    print("🔍 تشخيص تصدير الجزاءات")
    print(f"📤 نوع التصدير: {export_type}")
    print(f"👤 المستخدم: {current_user.username}")
    print(f"📊 معاملات الطلب: {dict(request.args)}")
    print("=" * 50 + "\n")
    # ========================

    if current_user.role != 'owner':
        flash('غير مصرح', 'error')
        return redirect(url_for('dashboard'))

    try:
        from models import Penalty, Employee

        employee_id = request.args.get('employee_id', type=int)
        from_date_str = request.args.get('from_date', '')
        to_date_str = request.args.get('to_date', '')
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        status = request.args.get('status', '')

        # بناء الاستعلام
        query = Penalty.query

        if employee_id:
            query = query.filter_by(employee_id=employee_id)
        if from_date_str:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            query = query.filter(Penalty.penalty_date >= from_date)
        if to_date_str:
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
            query = query.filter(Penalty.penalty_date <= to_date)
        if year:
            query = query.filter_by(year=year)
        if month:
            query = query.filter_by(month=month)
        if status == 'deducted':
            query = query.filter_by(is_deducted=True)
        elif status == 'pending':
            query = query.filter_by(is_deducted=False)

        penalties = query.order_by(Penalty.penalty_date.desc()).all()

        # جلب جميع الموظفين للفلتر
        employees = Employee.query.filter_by(is_active=True).all()

        today = datetime.now()

        # ===== كود التشخيص =====
        print(f"📊 عدد الجزاءات: {len(penalties)}")
        if penalties:
            print(f"💰 إجمالي المبلغ: {sum(p.amount for p in penalties)}")
        print("=" * 50 + "\n")
        # ========================

        if export_type == 'excel':
            rows = []
            for p in penalties:
                rows.append({
                    'التاريخ': p.penalty_date.strftime('%Y-%m-%d'),
                    'الموظف': p.employee.full_name if p.employee else '-',
                    'المبلغ': p.amount,
                    'السبب': p.reason,
                    'الوصف': p.description or '',
                    'تم الخصم': 'نعم' if p.is_deducted else 'لا'
                })

            headers = ['التاريخ', 'الموظف', 'المبلغ', 'السبب', 'الوصف', 'تم الخصم']
            report_name = f"تقرير الجزاءات {today.strftime('%Y-%m-%d')}"
            filename_prefix = f"penalties_report_{today.strftime('%Y%m%d')}"

            return export_report(export_type, report_name, headers, rows, filename_prefix, 'landscape')

        elif export_type == 'pdf':
            from flask import render_template

            try:
                # استخدام قالب PDF المخصص للجزاءات
                template_name = 'financial/penalties_pdf_report.html'

                print(f"📄 استخدام القالب: {template_name}")

                html_content = render_template(
                    template_name,
                    penalties=penalties,
                    employees=employees,
                    today=today,
                    current_user=current_user,
                    from_date=from_date_str,
                    to_date=to_date_str,
                    selected_employee=employee_id
                )

                print(f"✅ تم إنشاء HTML بنجاح")
                print(f"📏 حجم HTML: {len(html_content)} حرف")

                # ✅ استخدام الدالة الذكية
                response = export_pdf(html_content, 'penalties_report')
                if response:
                    return response
                else:
                    flash('حدث خطأ في إنشاء PDF', 'error')
                    return redirect(url_for('penalties_list', **request.args))

            except Exception as pdf_error:
                print(f"❌ خطأ في إنشاء PDF: {str(pdf_error)}")
                import traceback
                traceback.print_exc()

                app.logger.error(f"PDF Generation Error: {str(pdf_error)}")
                flash(f'حدث خطأ في إنشاء PDF: {str(pdf_error)}', 'error')
                return redirect(url_for('penalties_list', **request.args))

    except Exception as e:
        print(f"❌ خطأ عام: {str(e)}")
        import traceback
        traceback.print_exc()

        app.logger.error(f"Error exporting penalties: {str(e)}")
        flash(f'حدث خطأ في التصدير: {str(e)}', 'error')
        return redirect(url_for('penalties_list', **request.args))

@app.route('/profile')
@login_required
def profile():
    """عرض الملف الشخصي للمستخدم"""
    try:
        # جلب بيانات إضافية للمستخدم
        employee_data = None
        if current_user.employee_profile:
            employee_data = current_user.employee_profile

            # جلب آخر التقييمات للعاملين
            if current_user.role == 'worker':
                recent_evaluations = CleaningEvaluation.query \
                    .filter_by(evaluated_employee_id=employee_data.id) \
                    .order_by(CleaningEvaluation.date.desc()) \
                    .limit(5) \
                    .all()
            else:
                recent_evaluations = []
        else:
            recent_evaluations = []

        return render_template('profile.html',
                               employee_data=employee_data,
                               recent_evaluations=recent_evaluations)

    except Exception as e:
        app.logger.error(f"Error in profile: {str(e)}")
        flash('حدث خطأ في تحميل الملف الشخصي', 'error')
        return render_template('profile.html')


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """صفحة إعدادات المستخدم"""
    from models import User, Employee, db

    user = current_user
    employee = None

    # محاولة جلب بيانات الموظف إذا وجدت
    if hasattr(user, 'employee_profile') and user.employee_profile:
        employee = user.employee_profile

    if request.method == 'POST':
        try:
            # تحديث معلومات المستخدم الأساسية
            new_username = request.form.get('username')
            new_email = request.form.get('email')

            if new_username and new_username != user.username:
                # التحقق من عدم وجود اسم مستخدم مكرر
                existing_user = User.query.filter_by(username=new_username).first()
                if existing_user and existing_user.id != user.id:
                    flash('اسم المستخدم موجود مسبقاً', 'error')
                    return redirect(url_for('settings'))
                user.username = new_username

            if new_email and new_email != user.email:
                # التحقق من عدم وجود بريد إلكتروني مكرر
                existing_user = User.query.filter_by(email=new_email).first()
                if existing_user and existing_user.id != user.id:
                    flash('البريد الإلكتروني موجود مسبقاً', 'error')
                    return redirect(url_for('settings'))
                user.email = new_email

            # تحديث كلمة المرور إذا تم إدخالها
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            if current_password and new_password and confirm_password:
                # التحقق من كلمة المرور الحالية
                if not user.check_password(current_password):
                    flash('كلمة المرور الحالية غير صحيحة', 'error')
                    return redirect(url_for('settings'))

                # التحقق من تطابق كلمة المرور الجديدة
                if new_password != confirm_password:
                    flash('كلمة المرور الجديدة غير متطابقة', 'error')
                    return redirect(url_for('settings'))

                # التحقق من قوة كلمة المرور
                if len(new_password) < 6:
                    flash('كلمة المرور يجب أن تكون 6 أحرف على الأقل', 'error')
                    return redirect(url_for('settings'))

                user.set_password(new_password)
                flash('تم تغيير كلمة المرور بنجاح', 'success')

            # تحديث معلومات الموظف إذا وجد
            if employee:
                employee.full_name = request.form.get('full_name', employee.full_name)
                employee.phone = request.form.get('phone', employee.phone)
                employee.address = request.form.get('address', employee.address)

                # تحديث المسمى الوظيفي (للمالك فقط)
                if current_user.role == 'owner' and request.form.get('position'):
                    employee.position = request.form.get('position')

            # تحديث الإعدادات المحفوظة في قاعدة البيانات
            # يمكنك إضافة جدول للإعدادات إذا أردت

            db.session.commit()
            flash('تم تحديث الإعدادات بنجاح', 'success')
            return redirect(url_for('settings'))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تحديث الإعدادات: {str(e)}', 'error')
            return redirect(url_for('settings'))

    # إحصائيات إضافية للعرض
    stats = {
        'total_evaluations': 0,
        'total_attendances': 0,
        'member_since': user.created_at if hasattr(user, 'created_at') else None,
        'last_login': user.last_login if hasattr(user, 'last_login') else None
    }

    # حساب الإحصائيات حسب دور المستخدم
    if employee:
        if hasattr(employee, 'evaluations_received'):
            stats['total_evaluations'] = len(employee.evaluations_received)
        if hasattr(employee, 'attendances'):
            stats['total_attendances'] = len(employee.attendances)

    return render_template('settings.html',
                           user=user,
                           employee=employee,
                           stats=stats)

@app.route('/reports/generate')
@login_required
def generate_report():
    return render_template('reports/daily_evaluations.html')

@app.route('/schedules/create', methods=['GET', 'POST'])
@login_required
def create_schedule():
    return render_template('schedules/create.html')


# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500


# Route to handle flutter_service_worker.js requests
@app.route('/flutter_service_worker.js')
def flutter_service_worker():
    return '', 404


# مسارات التصحيح وتهيئة البيانات
@app.route('/create-complete-data')
@login_required
def create_complete_data():
    """إنشاء بيانات شاملة وكاملة للتجربة"""
    if current_user.role != 'owner':
        flash('غير مصرح', 'error')
        return redirect(url_for('dashboard'))

    try:
        # 1. استخدام الشركة الموجودة
        company = Company.query.filter_by(name='شركة النظافة المثاليه').first()
        if not company:
            company = Company(
                name='شركة النظافة المثاليه',
                address='الرياض - المملكة العربية السعودية',
                contact_person='أحمد محمد',
                phone='+966500000000',
                email='info@example.com',
                is_active=True
            )
            db.session.add(company)
            db.session.flush()

        # 2. استخدام المنطقة الموجودة وتعيين مشرف
        area = Area.query.filter_by(name='المنطقة الرئيسية').first()
        if area:
            # تعيين المشرف الأول للمنطقة
            supervisor = Employee.query.filter_by(position='supervisor').first()
            if supervisor:
                area.supervisor_id = supervisor.id

        # 3. استخدام الموقع الموجود وتعيين مراقب
        location = Location.query.filter_by(name='المبنى الإداري').first()
        if location:
            # تعيين المراقب الأول للموقع
            monitor = Employee.query.filter_by(position='monitor').first()
            if monitor:
                location.monitor_id = monitor.id

        # 4. إنشاء أماكن إضافية
        additional_places = [
            'المكتب الرئيسي',
            'قاعة الاجتماعات',
            'المطبخ',
            'دورات المياه',
            'الممرات',
            'المدخل الرئيسي',
            'غرفة الأرشيف',
            'المكتبة',
            'غرفة الخادم',
            'المستودع',
            'المختبر',
            'الصالة',
            'المصعد',
            'السلم',
            'الموقف'
        ]

        created_places = 0
        for place_name in additional_places:
            existing_place = Place.query.filter_by(name=place_name, location_id=location.id).first()
            if not existing_place:
                place = Place(
                    name=place_name,
                    location_id=location.id,
                    is_active=True
                )
                db.session.add(place)
                created_places += 1

        # 5. تعيين عامل للأماكن
        worker = Employee.query.filter_by(position='worker').first()
        if worker:
            # تعيين العامل لبعض الأماكن
            places_to_assign = Place.query.limit(5).all()
            for place in places_to_assign:
                place.worker_id = worker.id

        # 6. إنشاء تقييمات تجريبية
        evaluation_samples = [
            {
                'cleanliness': 5,
                'organization': 4,
                'equipment_condition': 5,
                'safety_measures': 4,
                'comments': 'أداء ممتاز في النظافة'
            },
            {
                'cleanliness': 4,
                'organization': 3,
                'equipment_condition': 4,
                'safety_measures': 5,
                'comments': 'جيد ولكن يحتاج تحسين في التنظيم'
            },
            {
                'cleanliness': 3,
                'organization': 4,
                'equipment_condition': 3,
                'safety_measures': 4,
                'comments': 'أداء مقبول يحتاج لمزيد من الاهتمام'
            },
            {
                'cleanliness': 5,
                'organization': 5,
                'equipment_condition': 4,
                'safety_measures': 5,
                'comments': 'أداء متميز في جميع المجالات'
            }
        ]

        created_evaluations = 0
        places = Place.query.all()
        employees = Employee.query.all()

        if places and employees:
            for i, sample in enumerate(evaluation_samples):
                # استخدام أماكن وموظفين مختلفين لكل تقييم
                place = places[i % len(places)]
                evaluated_employee = employees[i % len(employees)]
                evaluator = employees[(i + 1) % len(employees)]  # مقيم مختلف

                # تاريخ مختلف لكل تقييم
                eval_date = date.today() - timedelta(days=i * 2)

                evaluation = CleaningEvaluation(
                    date=eval_date,
                    place_id=place.id,
                    evaluated_employee_id=evaluated_employee.id,
                    evaluator_id=evaluator.id,
                    cleanliness=sample['cleanliness'],
                    organization=sample['organization'],
                    equipment_condition=sample['equipment_condition'],
                    safety_measures=sample['safety_measures'],
                    overall_score=0.0,
                    comments=sample['comments']
                )

                # حساب النتيجة الإجمالية
                evaluation.calculate_overall_score()

                db.session.add(evaluation)
                created_evaluations += 1

        # 7. إنشاء سجلات حضور
        attendance_samples = [
            {'status': 'present', 'check_in': '08:00', 'check_out': '16:00'},
            {'status': 'present', 'check_in': '08:15', 'check_out': '16:30'},
            {'status': 'late', 'check_in': '09:30', 'check_out': '17:00'},
            {'status': 'present', 'check_in': '08:05', 'check_out': '16:15'}
        ]

        created_attendance = 0
        for i, employee in enumerate(employees):
            for day in range(5):  # 5 أيام حضور
                att_date = date.today() - timedelta(days=day)
                sample = attendance_samples[(i + day) % len(attendance_samples)]

                attendance = Attendance(
                    employee_id=employee.id,
                    date=att_date,
                    status=sample['status'],
                    check_in=datetime.strptime(sample['check_in'], '%H:%M').time() if sample['check_in'] else None,
                    check_out=datetime.strptime(sample['check_out'], '%H:%M').time() if sample['check_out'] else None,
                    notes=f'حضور يوم {att_date.strftime("%Y-%m-%d")}'
                )

                db.session.add(attendance)
                created_attendance += 1

        db.session.commit()

        flash(
            f'تم إنشاء البيانات بنجاح! ({created_places} مكان، {created_evaluations} تقييم، {created_attendance} سجل حضور)',
            'success')
        return redirect(url_for('debug_data'))

    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في إنشاء البيانات: {str(e)}', 'error')
        return redirect(url_for('dashboard'))


@app.route('/fix-permissions')
@login_required
def fix_permissions():
    """إصلاح الصلاحيات وتعيين المسؤولين"""
    if current_user.role != 'owner':
        flash('غير مصرح', 'error')
        return redirect(url_for('dashboard'))

    try:
        # 1. تعيين المشرف للمنطقة
        area = Area.query.filter_by(name='المنطقة الرئيسية').first()
        supervisor = Employee.query.filter_by(position='supervisor').first()
        if area and supervisor:
            area.supervisor_id = supervisor.id

        # 2. تعيين المراقب للموقع
        location = Location.query.filter_by(name='المبنى الإداري').first()
        monitor = Employee.query.filter_by(position='monitor').first()
        if location and monitor:
            location.monitor_id = monitor.id

        # 3. تعيين العامل لبعض الأماكن
        worker = Employee.query.filter_by(position='worker').first()
        places = Place.query.all()
        if worker and places:
            for i, place in enumerate(places[:5]):  # تعيين أول 5 أماكن
                place.worker_id = worker.id

        db.session.commit()
        flash('تم إصلاح الصلاحيات والتعيينات بنجاح!', 'success')
        return redirect(url_for('debug_data'))

    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في إصلاح الصلاحيات: {str(e)}', 'error')
        return redirect(url_for('dashboard'))


@app.route('/debug-data')
@login_required
def debug_data():
    """فحص سريع للبيانات الحالية"""
    if current_user.role != 'owner':
        return "غير مصرح", 403

    data = {
        'companies': Company.query.all(),
        'areas': Area.query.all(),
        'locations': Location.query.all(),
        'places': Place.query.all(),
        'employees': Employee.query.all(),
        'evaluations': CleaningEvaluation.query.all(),
        'attendance': Attendance.query.all()
    }

    result = f"""
    <h1>فحص البيانات الحالية</h1>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        td, th {{ border: 1px solid #ddd; padding: 8px; text-align: right; }}
        th {{ background-color: #f2f2f2; }}
        .actions {{ margin: 20px 0; }}
        .btn {{ padding: 10px 15px; margin: 5px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
        .btn-success {{ background: #28a745; }}
    </style>

    <div class="actions">
        <a href="/create-complete-data" class="btn btn-success">إنشاء بيانات شاملة</a>
        <a href="/fix-permissions" class="btn">إصلاح الصلاحيات</a>
        <a href="/evaluations/add" class="btn">إضافة تقييم</a>
    </div>

    <h2>الشركات ({len(data['companies'])})</h2>
    <table>
        <tr><th>ID</th><th>الاسم</th><th>الحالة</th></tr>
        {"".join([f"<tr><td>{c.id}</td><td>{c.name}</td><td>{'نشط' if c.is_active else 'غير نشط'}</td></tr>" for c in data['companies']])}
    </table>

    <h2>المناطق ({len(data['areas'])})</h2>
    <table>
        <tr><th>ID</th><th>الاسم</th><th>الشركة</th><th>المشرف</th></tr>
        {"".join([f"<tr><td>{a.id}</td><td>{a.name}</td><td>{a.company.name if a.company else 'لا يوجد'}</td><td>{a.supervisor.full_name if a.supervisor else 'غير محدد'}</td></tr>" for a in data['areas']])}
    </table>

    <h2>المواقع ({len(data['locations'])})</h2>
    <table>
        <tr><th>ID</th><th>الاسم</th><th>المنطقة</th><th>المراقب</th></tr>
        {"".join([f"<tr><td>{l.id}</td><td>{l.name}</td><td>{l.area.name if l.area else 'لا يوجد'}</td><td>{l.monitor.full_name if l.monitor else 'غير محدد'}</td></tr>" for l in data['locations']])}
    </table>

    <h2>الأماكن ({len(data['places'])})</h2>
    <table>
        <tr><th>ID</th><th>الاسم</th><th>الموقع</th><th>العامل</th></tr>
        {"".join([f"<tr><td>{p.id}</td><td>{p.name}</td><td>{p.location.name if p.location else 'لا يوجد'}</td><td>{p.worker.full_name if p.worker else 'غير محدد'}</td></tr>" for p in data['places']])}
    </table>

    <h2>الموظفين ({len(data['employees'])})</h2>
    <table>
        <tr><th>ID</th><th>الاسم</th><th>الوظيفة</th><th>الحالة</th></tr>
        {"".join([f"<tr><td>{e.id}</td><td>{e.full_name}</td><td>{e.position}</td><td>{'نشط' if e.is_active else 'غير نشط'}</td></tr>" for e in data['employees']])}
    </table>

    <h2>التقييمات ({len(data['evaluations'])})</h2>
    <table>
        <tr><th>ID</th><th>التاريخ</th><th>المكان</th><th>الموظف المقيّم</th><th>المقيّم</th></tr>
        {"".join([f"<tr><td>{e.id}</td><td>{e.date}</td><td>{e.place.name if e.place else 'لا يوجد'}</td><td>{e.evaluated_employee.full_name if e.evaluated_employee else 'لا يوجد'}</td><td>{e.evaluator.full_name if e.evaluator else 'لا يوجد'}</td></tr>" for e in data['evaluations']])}
    </table>
    """

    return result

#@app.route('/init-db')
#def init_database():
  #  """إعادة تهيئة قاعدة البيانات"""
   # try:
    #    with app.app_context():
     #       db.drop_all()  # حذف جميع الجداول (اختياري)
      #      db.create_all()  # إنشاء جميع الجداول
       #     initialize_database()  # إضافة البيانات الأولية
        #return "✅ تم تهيئة قاعدة البيانات بنجاح"
    #except Exception as e:
     #   return f"❌ خطأ في تهيئة قاعدة البيانات: {str(e)}"

@app.route('/check-db')
def check_database():
    """فحص حالة قاعدة البيانات"""
    try:
        with app.app_context():
            # محاولة الاستعلام من جدول users
            users_count = User.query.count()
            return f"✅ قاعدة البيانات تعمل بشكل صحيح. عدد المستخدمين: {users_count}"
    except Exception as e:
        return f"❌ خطأ في قاعدة البيانات: {str(e)}"


# ============================================
# ✅ نقاط نهاية للمزامنة (Sync Endpoints)
# ============================================

@app.route('/api/sync/pull', methods=['POST'])
@login_required
def sync_pull():
    """جلب البيانات المحدثة من الخادم للمزامنة"""
    try:
        data = request.get_json()
        last_sync = data.get('last_sync')

        if last_sync:
            last_sync_date = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
        else:
            last_sync_date = datetime(2000, 1, 1)

        response_data = {
            'employees': [],
            'attendance': [],
            'evaluations': [],
            'companies': [],
            'areas': [],
            'locations': [],
            'places': [],
            'sync_token': datetime.utcnow().isoformat() + 'Z'
        }

        # جلب الموظفين المحدثين
        if check_permission('can_view_employees'):
            employees = Employee.query.filter(
                db.or_(
                    Employee.updated_at > last_sync_date,
                    Employee.created_at > last_sync_date
                )
            ).all()

            response_data['employees'] = [{
                'id': emp.id,
                'code': emp.code,
                'full_name': emp.full_name,
                'phone': emp.phone,
                'position': emp.position,
                'salary': float(emp.salary) if emp.salary else 0,
                'hire_date': emp.hire_date.isoformat() if emp.hire_date else None,
                'is_active': emp.is_active,
                'company_id': emp.company_id,
                'supervisor_id': emp.supervisor_id,
                'updated_at': emp.updated_at.isoformat() if emp.updated_at else None,
                '_deleted': not emp.is_active
            } for emp in employees]

        # جلب الحضور المحدث (آخر 30 يوم فقط للتقليل)
        if check_permission('can_view_attendance'):
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            attendance = Attendance.query.filter(
                db.or_(
                    Attendance.updated_at > last_sync_date,
                    Attendance.created_at > last_sync_date
                ),
                Attendance.date >= thirty_days_ago.date()
            ).all()

            response_data['attendance'] = [{
                'id': att.id,
                'employee_id': att.employee_id,
                'date': att.date.isoformat(),
                'status': att.status,
                'shift_type': att.shift_type,
                'check_in': att.check_in.isoformat() if att.check_in else None,
                'check_out': att.check_out.isoformat() if att.check_out else None,
                'notes': att.notes,
                'updated_at': att.updated_at.isoformat() if att.updated_at else None
            } for att in attendance]

        # جلب التقييمات المحدثة (آخر 30 يوم)
        if check_permission('can_view_evaluations'):
            evaluations = CleaningEvaluation.query.filter(
                db.or_(
                    CleaningEvaluation.updated_at > last_sync_date,
                    CleaningEvaluation.created_at > last_sync_date
                ),
                CleaningEvaluation.date >= (datetime.utcnow() - timedelta(days=30)).date()
            ).all()

            response_data['evaluations'] = [{
                'id': ev.id,
                'date': ev.date.isoformat(),
                'place_id': ev.place_id,
                'evaluated_employee_id': ev.evaluated_employee_id,
                'evaluator_id': ev.evaluator_id,
                'cleanliness': ev.cleanliness,
                'organization': ev.organization,
                'equipment_condition': ev.equipment_condition,
                'safety_measures': ev.safety_measures,
                'overall_score': float(ev.overall_score) if ev.overall_score else 0,
                'comments': ev.comments,
                'updated_at': ev.updated_at.isoformat() if ev.updated_at else None
            } for ev in evaluations]

        return jsonify({
            'success': True,
            'data': response_data
        })

    except Exception as e:
        app.logger.error(f"❌ Error in sync_pull: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/sync/push', methods=['POST'])
@login_required
def sync_push():
    """استقبال التغييرات المحلية من العميل"""
    try:
        data = request.get_json()
        changes = data.get('changes', {})
        results = {
            'success': True,
            'synced': [],
            'conflicts': []
        }

        # معالجة الموظفين المضافة محلياً
        for emp_data in changes.get('employees', []):
            try:
                if emp_data.get('_deleted'):
                    # حذف (أو تعطيل) الموظف
                    employee = Employee.query.get(emp_data['id'])
                    if employee:
                        employee.is_active = False
                        employee.updated_at = datetime.utcnow()
                        db.session.add(employee)
                        results['synced'].append({
                            'type': 'employee',
                            'id': emp_data['id'],
                            'action': 'delete'
                        })
                elif emp_data.get('_local_id') and not emp_data.get('id'):
                    # إضافة موظف جديد
                    employee = Employee(
                        code=emp_data.get('code', Employee.generate_code()),
                        full_name=emp_data['full_name'],
                        phone=emp_data.get('phone'),
                        position=emp_data.get('position', 'worker'),
                        salary=emp_data.get('salary', 0),
                        hire_date=datetime.fromisoformat(emp_data['hire_date']).date() if emp_data.get(
                            'hire_date') else date.today(),
                        company_id=emp_data.get('company_id'),
                        supervisor_id=emp_data.get('supervisor_id'),
                        is_active=emp_data.get('is_active', True)
                    )
                    db.session.add(employee)
                    db.session.flush()

                    results['synced'].append({
                        'type': 'employee',
                        'local_id': emp_data['_local_id'],
                        'server_id': employee.id,
                        'action': 'create'
                    })
                else:
                    # تحديث موظف موجود
                    employee = Employee.query.get(emp_data['id'])
                    if employee:
                        # التحقق من التضارب
                        server_updated = employee.updated_at.isoformat() if employee.updated_at else None
                        client_updated = emp_data.get('updated_at')

                        if server_updated and client_updated and server_updated > client_updated:
                            # تضارب - استخدام نسخة الخادم
                            results['conflicts'].append({
                                'type': 'employee',
                                'id': emp_data['id'],
                                'server_version': employee.to_dict(),
                                'client_version': emp_data
                            })
                        else:
                            # تحديث البيانات
                            employee.full_name = emp_data.get('full_name', employee.full_name)
                            employee.phone = emp_data.get('phone', employee.phone)
                            employee.position = emp_data.get('position', employee.position)
                            employee.salary = emp_data.get('salary', employee.salary)
                            employee.is_active = emp_data.get('is_active', employee.is_active)
                            employee.updated_at = datetime.utcnow()

                            results['synced'].append({
                                'type': 'employee',
                                'id': emp_data['id'],
                                'action': 'update'
                            })
            except Exception as e:
                app.logger.error(f"Error syncing employee: {str(e)}")

        # معالجة الحضور المضاف محلياً
        for att_data in changes.get('attendance', []):
            try:
                if att_data.get('_local_id') and not att_data.get('id'):
                    # إضافة سجل حضور جديد
                    attendance = Attendance(
                        employee_id=att_data['employee_id'],
                        date=datetime.fromisoformat(att_data['date']).date(),
                        status=att_data['status'],
                        shift_type=att_data.get('shift_type', 'morning'),
                        check_in=datetime.fromisoformat(att_data['check_in']).time() if att_data.get(
                            'check_in') else None,
                        check_out=datetime.fromisoformat(att_data['check_out']).time() if att_data.get(
                            'check_out') else None,
                        notes=att_data.get('notes')
                    )
                    db.session.add(attendance)
                    db.session.flush()

                    results['synced'].append({
                        'type': 'attendance',
                        'local_id': att_data['_local_id'],
                        'server_id': attendance.id,
                        'action': 'create'
                    })
                else:
                    # تحديث سجل موجود
                    attendance = Attendance.query.get(att_data['id'])
                    if attendance:
                        attendance.status = att_data.get('status', attendance.status)
                        attendance.check_in = datetime.fromisoformat(att_data['check_in']).time() if att_data.get(
                            'check_in') else attendance.check_in
                        attendance.check_out = datetime.fromisoformat(att_data['check_out']).time() if att_data.get(
                            'check_out') else attendance.check_out
                        attendance.notes = att_data.get('notes', attendance.notes)
                        attendance.updated_at = datetime.utcnow()

                        results['synced'].append({
                            'type': 'attendance',
                            'id': att_data['id'],
                            'action': 'update'
                        })
            except Exception as e:
                app.logger.error(f"Error syncing attendance: {str(e)}")

        db.session.commit()

        return jsonify({
            'success': True,
            'results': results
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"❌ Error in sync_push: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/sync/status')
@login_required
def sync_status():
    """الحصول على حالة المزامنة"""
    try:
        # حساب عدد التغييرات الأخيرة
        last_hour = datetime.utcnow() - timedelta(hours=1)

        recent_employees = Employee.query.filter(
            db.or_(
                Employee.updated_at > last_hour,
                Employee.created_at > last_hour
            )
        ).count()

        recent_attendance = Attendance.query.filter(
            db.or_(
                Attendance.updated_at > last_hour,
                Attendance.created_at > last_hour
            )
        ).count()

        recent_evaluations = CleaningEvaluation.query.filter(
            db.or_(
                CleaningEvaluation.updated_at > last_hour,
                CleaningEvaluation.created_at > last_hour
            )
        ).count()

        return jsonify({
            'success': True,
            'server_time': datetime.utcnow().isoformat() + 'Z',
            'changes': {
                'employees': recent_employees,
                'attendance': recent_attendance,
                'evaluations': recent_evaluations
            },
            'total': recent_employees + recent_attendance + recent_evaluations
        })

    except Exception as e:
        app.logger.error(f"❌ Error in sync_status: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# يمكنك إضافة هذا المسار مؤقتاً للتحديث
@app.route('/update-db')
@login_required
def update_database():
    if current_user.role != 'owner':
        return "غير مصرح", 403

    try:
        db.create_all()
        return "✅ تم تحديث قاعدة البيانات بنجاح"
    except Exception as e:
        return f"❌ خطأ: {str(e)}"

if __name__ == '__main__':
    try:
        print("=" * 50)
        print("🚀 بدء تشغيل تطبيق أرض الجوهرة للنظافة...")
        print("📊 يمكنك الوصول للتطبيق على: http://localhost:5000")
        print("👤 اسم المستخدم: owner")
        print("🔑 كلمة المرور: admin123")
        print("=" * 50)
        print("🔄 بدء تشغيل الخادم...")

        import os

        # 🔹 استخدم المنفذ الذي توفره Render تلقائيًا
        port = int(os.environ.get("PORT", 5000))

        # 🔹 استخدم وضع DEBUG من البيئة
        debug_mode = os.environ.get("DEBUG", "True").lower() == "true"

        app.run(
            host='0.0.0.0',
            port=port,
            debug=debug_mode
        )

    except Exception as e:
        print(f"❌ خطأ في تشغيل التطبيق: {e}")
        import traceback
        print(f"🔍 تفاصيل الخطأ: {traceback.format_exc()}")

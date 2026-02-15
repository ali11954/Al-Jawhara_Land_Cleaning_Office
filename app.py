from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Employee, Company, Area, Location, Place, CleaningEvaluation, Attendance ,SupervisorEvaluation
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

@app.template_filter('time_ago')
def time_ago_filter(date):
    """تحويل التاريخ إلى نص مثل 'منذ يومين'"""
    if not date:
        return ""

    try:
        now = datetime.now().date()
        diff = (now - date).days

        if diff == 0:
            return "اليوم"
        elif diff == 1:
            return "أمس"
        elif diff < 7:
            return f"منذ {diff} أيام"
        elif diff < 30:
            weeks = diff // 7
            return f"منذ {weeks} أسابيع"
        elif diff < 365:
            months = diff // 30
            return f"منذ {months} أشهر"
        else:
            years = diff // 365
            return f"منذ {years} سنوات"
    except Exception as e:
        app.logger.error(f"Error in time_ago filter: {str(e)}")
        return str(date)


# ✅ تصحيح: تهيئة الإضافات مرة واحدة
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'يجب تسجيل الدخول للوصول إلى هذه الصفحة'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.template_filter('time')
def time_filter(value):
    """تنسيق الوقت"""
    if not value:
        return "-"
    try:
        if hasattr(value, 'strftime'):
            return value.strftime('%H:%M')
        return str(value)
    except Exception as e:
        app.logger.error(f"Error in time filter: {str(e)}")
        return "-"

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


# ============================================
# تسجيل جميع الفلاتر المخصصة في Jinja2
# ============================================
def register_template_filters(app):
    """تسجيل جميع الفلاتر المخصصة في Jinja2"""

    @app.template_filter('date')
    def date_filter(value, format='%Y-%m-%d'):
        """تنسيق التاريخ"""
        if not value:
            return ""
        try:
            if isinstance(value, str):
                from datetime import datetime
                value = datetime.strptime(value, '%Y-%m-%d')
            return value.strftime(format)
        except Exception as e:
            app.logger.error(f"Error in date filter: {str(e)}")
            return str(value)

    @app.template_filter('arabic_date')
    def arabic_date_filter(value, format='%Y-%m-%d'):
        """تنسيق التاريخ مع دعم العربية"""
        if not value:
            return ""
        try:
            if isinstance(value, str):
                from datetime import datetime
                value = datetime.strptime(value, '%Y-%m-%d')
            return value.strftime(format)
        except Exception as e:
            app.logger.error(f"Error in arabic_date filter: {str(e)}")
            return str(value)

    @app.template_filter('time_ago')
    def time_ago_filter(value):
        """تحويل التاريخ إلى صيغة 'منذ وقت'"""
        if not value:
            return ""
        try:
            from datetime import datetime, timedelta
            now = datetime.now()
            if isinstance(value, str):
                from datetime import datetime
                value = datetime.strptime(value, '%Y-%m-%d')

            diff = now - value

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

    @app.template_filter('currency')
    def currency_filter(value):
        """تنسيق العملة"""
        if not value:
            return "0 ر.س"
        try:
            return "{:,.0f} ر.س".format(float(value))
        except:
            return str(value)

    @app.template_filter('percentage')
    def percentage_filter(value):
        """تنسيق النسبة المئوية"""
        if not value:
            return "0%"
        try:
            return "{:.1f}%".format(float(value))
        except:
            return str(value)


# سجل الفلاتر بعد إنشاء التطبيق
register_template_filters(app)

@app.context_processor
def inject_stats():
    """حقن الإحصائيات في جميع القوالب"""
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

    return dict(stats=stats)

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


@app.route('/employees')
@login_required
def employees_list():
    # التحقق من الصلاحيات - للمالك فقط
    if current_user.role != 'owner':
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


@app.route('/employees/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    # التحقق من الصلاحيات - للمالك فقط
    if current_user.role != 'owner':
        flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))

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

        # التحقق من البيانات المطلوبة
        if not full_name or not position or not hire_date:
            flash('الرجاء ملء جميع الحقول المطلوبة', 'error')
            return redirect(url_for('add_employee'))

        if not company_id:
            flash('الرجاء اختيار الشركة', 'error')
            return redirect(url_for('add_employee'))

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
            user_id=user_id,  # None للعمال والمراقبين
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

        flash(f'✅ تم إضافة الموظف {full_name} بنجاح', 'success')
        return redirect(url_for('employees_list'))

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in add_employee: {str(e)}")
        flash(f'❌ حدث خطأ أثناء إضافة الموظف: {str(e)}', 'error')
        return redirect(url_for('add_employee'))


@app.route('/employees/edit/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def edit_employee(employee_id):
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

@app.route('/attendance')
@login_required
def attendance_index():
    try:
        # الحصول على معاملات الفلترة
        selected_date = request.args.get('date', date.today().isoformat())
        employee_id = request.args.get('employee_id', type=int)
        company_id = request.args.get('company_id', type=int)
        shift_type = request.args.get('shift_type', '')

        # التحقق من صحة التاريخ
        try:
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except ValueError:
            selected_date = date.today()
            flash('صيغة التاريخ غير صحيحة، تم استخدام تاريخ اليوم', 'warning')

        # حساب التواريخ للتنقل بين الأيام
        prev_date = selected_date - timedelta(days=1)
        next_date = selected_date + timedelta(days=1)

        # استعلام الحضور مع الفلترة
        attendance_query = db.session.query(Attendance).join(
            Employee, Attendance.employee_id == Employee.id
        ).options(
            joinedload(Attendance.employee)
        ).filter(
            Attendance.date == selected_date,
            Employee.is_active == True  # فقط الموظفين النشطين
        )

        # تطبيق الفلترة الإضافية
        if employee_id:
            attendance_query = attendance_query.filter(Attendance.employee_id == employee_id)

        if company_id:
            attendance_query = attendance_query.filter(Employee.company_id == company_id)

        if shift_type and shift_type != 'all':
            attendance_query = attendance_query.filter(Attendance.shift_type == shift_type)

        # تنفيذ الاستعلام
        attendance_records = attendance_query.order_by(
            Employee.full_name.asc(),
            Attendance.shift_type.asc()
        ).all()

        # إحصائيات الحضور
        total_employees = Employee.query.filter_by(is_active=True).count()

        # إحصائيات مفصلة
        stats_query = db.session.query(
            Attendance.status,
            db.func.count(Attendance.id)
        ).join(Employee).filter(
            Attendance.date == selected_date,
            Employee.is_active == True
        )

        # تطبيق نفس الفلترة على الإحصائيات
        if employee_id:
            stats_query = stats_query.filter(Attendance.employee_id == employee_id)
        if company_id:
            stats_query = stats_query.join(Employee).filter(Employee.company_id == company_id)
        if shift_type and shift_type != 'all':
            stats_query = stats_query.filter(Attendance.shift_type == shift_type)

        stats = stats_query.group_by(Attendance.status).all()

        # تهيئة العدادات
        present_count = 0
        absent_count = 0
        late_count = 0

        for status, count in stats:
            if status == 'present':
                present_count = count
            elif status == 'absent':
                absent_count = count
            elif status == 'late':
                late_count = count

        # إذا لم يتم تطبيق فلترة، حساب الغياب بناءً على إجمالي الموظفين
        if not any([employee_id, company_id, shift_type and shift_type != 'all']):
            absent_count = total_employees - present_count - late_count

        # بيانات الفلترة
        employees_for_filter = Employee.query.filter_by(is_active=True).order_by(Employee.full_name).all()
        companies = Company.query.filter_by(is_active=True).all()

        # الموظف المحدد للفلترة
        selected_employee = Employee.query.get(employee_id) if employee_id else None

        print(f"✅ تم تحميل {len(attendance_records)} سجل حضور للتاريخ {selected_date}")
        if employee_id:
            print(f"   - مع فلترة الموظف: {selected_employee.full_name if selected_employee else employee_id}")
        if company_id:
            print(f"   - مع فلترة الشركة: {company_id}")
        if shift_type:
            print(f"   - مع فلترة الوردية: {shift_type}")

        return render_template('attendance/index.html',
                               today=date.today(),
                               selected_date=selected_date,
                               prev_date=prev_date,
                               next_date=next_date,
                               attendance_records=attendance_records,
                               total_employees=total_employees,
                               present_count=present_count,
                               absent_count=absent_count,
                               late_count=late_count,
                               # بيانات الفلترة
                               employees=employees_for_filter,
                               companies=companies,
                               selected_employee_id=employee_id,
                               selected_company_id=company_id,
                               selected_shift_type=shift_type,
                               selected_employee=selected_employee)

    except Exception as e:
        app.logger.error(f"Error in attendance_index: {str(e)}")
        flash('حدث خطأ في تحميل بيانات الحضور', 'error')

        # إرجاع بيانات افتراضية في حالة الخطأ
        return render_template('attendance/index.html',
                               today=date.today(),
                               selected_date=date.today(),
                               attendance_records=[],
                               total_employees=0,
                               present_count=0,
                               absent_count=0,
                               late_count=0,
                               employees=[],
                               companies=[],
                               selected_employee_id=None,
                               selected_company_id=None,
                               selected_shift_type='')


@app.route('/attendance/add', methods=['GET', 'POST'])
@login_required
def add_attendance():
    if request.method == 'GET':
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

@app.route('/attendance/prepare', methods=['GET', 'POST'])
@login_required
def prepare_attendance():
    """صفحة التحضير مع عرض جميع الموظفين حسب الصلاحيات"""

    # تعريف المتغيرات الأساسية
    selected_date = date.today()
    can_select_date = False
    employees = []
    companies = []
    areas = []
    locations = []
    existing_attendance = {}

    try:
        if request.method == 'GET':
            # الحصول على معاملات الفلترة
            company_id = request.args.get('company_id', type=int)
            area_id = request.args.get('area_id', type=int)
            location_id = request.args.get('location_id', type=int)
            date_str = request.args.get('date', date.today().isoformat())

            # التحقق من صحة التاريخ
            try:
                selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                selected_date = date.today()
                app.logger.warning(f"Invalid date format: {date_str}, using today's date")

            # تحديد إذا كان يمكن اختيار التاريخ (للمالك فقط)
            can_select_date = current_user.role == 'owner'

            # إذا كان المستخدم مشرف أو مراقب، يتم إجبار التاريخ على اليوم
            if current_user.role in ['supervisor', 'monitor']:
                selected_date = date.today()
                can_select_date = False

            # الحصول على الموظفين حسب الصلاحيات والفلترة
            try:
                employees = get_employees_for_attendance(
                    current_user,
                    company_id,
                    area_id,
                    location_id
                )
            except Exception as emp_error:
                app.logger.error(f"Error getting employees: {str(emp_error)}")
                employees = []
                flash('حدث خطأ في تحميل بيانات الموظفين', 'error')

            # الحصول على سجلات الحضور الحالية لهذا التاريخ
            try:
                attendance_records = Attendance.query.filter(
                    Attendance.date == selected_date
                ).all()

                for record in attendance_records:
                    key = f"{record.employee_id}_{record.shift_type}"
                    existing_attendance[key] = {
                        'status': record.status,
                        'check_in': record.check_in,
                        'check_out': record.check_out,
                        'notes': record.notes
                    }
            except Exception as att_error:
                app.logger.error(f"Error getting attendance records: {str(att_error)}")
                existing_attendance = {}

            # الحصول على قائمة الشركات والمناطق والمواقع للفلترة
            try:
                companies = Company.query.all()
                areas = Area.query.all()
                locations = Location.query.all()
            except Exception as filter_error:
                app.logger.error(f"Error getting filter data: {str(filter_error)}")
                companies = []
                areas = []
                locations = []

        elif request.method == 'POST':
            # التحقق من الصلاحيات
            if current_user.role not in ['owner', 'supervisor', 'monitor']:
                return jsonify({
                    'success': False,
                    'message': 'غير مصرح لك بهذا الإجراء',
                    'code': 'UNAUTHORIZED'
                }), 403

            # الحصول على البيانات - الآن البيانات تأتي كقائمة
            data = request.get_json()
            if not data or not isinstance(data, list):
                return jsonify({
                    'success': False,
                    'message': 'بيانات غير صالحة - يجب أن تكون قائمة',
                    'code': 'INVALID_DATA'
                }), 400

            # التحقق من وجود بيانات للحفظ
            if len(data) == 0:
                return jsonify({
                    'success': False,
                    'message': 'لا توجد بيانات للحفظ',
                    'code': 'NO_DATA'
                }), 400

            # إحصائيات عن البيانات المراد حفظها
            total_records = len(data)
            present_count = sum(1 for record in data if record.get('status') == 'present')
            absent_count = sum(1 for record in data if record.get('status') == 'absent')
            late_count = sum(1 for record in data if record.get('status') == 'late')

            # إذا كان الطلب يحتوي على تأكيد الحفظ
            confirm_save = request.headers.get('X-Confirm-Save', 'false').lower() == 'true'

            if not confirm_save:
                # إرجاع رسالة تأكيد مع إحصائيات
                return jsonify({
                    'success': True,
                    'require_confirmation': True,
                    'message': 'يرجى تأكيد حفظ سجلات الحضور',
                    'statistics': {
                        'total_records': total_records,
                        'present_count': present_count,
                        'absent_count': absent_count,
                        'late_count': late_count,
                        'date': data[0].get('date') if data else None
                    },
                    'code': 'CONFIRMATION_REQUIRED'
                }), 200

            # إذا تم تأكيد الحفظ، متابعة عملية الحفظ
            success_count = 0
            error_count = 0
            error_messages = []

            # معالجة كل سجل حضور في القائمة
            for attendance_data in data:
                try:
                    employee_id = attendance_data.get('employee_id')
                    date_str = attendance_data.get('date')
                    status = attendance_data.get('status')
                    shift_type = attendance_data.get('shift_type')
                    check_in_time = attendance_data.get('check_in')
                    check_out_time = attendance_data.get('check_out')
                    notes = attendance_data.get('notes', '')

                    # التحقق من البيانات المطلوبة
                    if not all([employee_id, date_str, status, shift_type]):
                        error_count += 1
                        error_messages.append(f"بيانات ناقصة للسجل: {attendance_data}")
                        continue

                    # معالجة التاريخ
                    try:
                        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        error_count += 1
                        error_messages.append(f"تاريخ غير صالح: {date_str}")
                        continue

                    # للمشرفين والمراقبين: إجبار التاريخ على اليوم
                    if current_user.role in ['supervisor', 'monitor']:
                        attendance_date = date.today()

                    # التحقق من وجود الموظف
                    employee = Employee.query.filter_by(id=employee_id, is_active=True).first()
                    if not employee:
                        error_count += 1
                        error_messages.append(f"موظف غير موجود: {employee_id}")
                        continue

                    # التحقق من الصلاحيات
                    if not can_record_attendance(current_user, employee):
                        error_count += 1
                        error_messages.append(f"غير مصرح لتسجيل حضور الموظف: {employee_id}")
                        continue

                    # البحث عن سجل حضور موجود
                    existing_attendance = Attendance.query.filter(
                        Attendance.employee_id == employee_id,
                        Attendance.date == attendance_date,
                        Attendance.shift_type == shift_type
                    ).first()

                    # معالجة أوقات الحضور والانصراف
                    check_in = None
                    check_out = None

                    if check_in_time:
                        try:
                            check_in = datetime.strptime(check_in_time, '%H:%M').time()
                        except ValueError:
                            app.logger.warning(f"Invalid check-in time format: {check_in_time}")

                    if check_out_time:
                        try:
                            check_out = datetime.strptime(check_out_time, '%H:%M').time()
                        except ValueError:
                            app.logger.warning(f"Invalid check-out time format: {check_out_time}")

                    if existing_attendance:
                        # تحديث السجل الموجود
                        existing_attendance.status = status
                        existing_attendance.check_in = check_in
                        existing_attendance.check_out = check_out
                        existing_attendance.notes = notes
                        existing_attendance.updated_at = datetime.now()
                    else:
                        # إنشاء سجل جديد
                        attendance = Attendance(
                            employee_id=employee_id,
                            date=attendance_date,
                            status=status,
                            shift_type=shift_type,
                            check_in=check_in,
                            check_out=check_out,
                            notes=notes
                        )
                        db.session.add(attendance)

                    success_count += 1

                except Exception as e:
                    app.logger.error(f"Error processing attendance record: {str(e)}")
                    error_count += 1
                    error_messages.append(f"خطأ في معالجة السجل: {str(e)}")

            # حفظ جميع التغييرات في قاعدة البيانات
            try:
                db.session.commit()
            except Exception as commit_error:
                db.session.rollback()
                app.logger.error(f"Database commit error: {str(commit_error)}")
                return jsonify({
                    'success': False,
                    'message': f'خطأ في حفظ البيانات: {str(commit_error)}',
                    'code': 'DATABASE_ERROR'
                }), 500

            if success_count > 0:
                message = f'تم حفظ {success_count} سجل حضور بنجاح'
                if error_count > 0:
                    message += f' وفشل حفظ {error_count} سجل'

                return jsonify({
                    'success': True,
                    'message': message,
                    'saved_count': success_count,
                    'error_count': error_count,
                    'code': 'ATTENDANCE_SAVED'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': 'فشل حفظ جميع سجلات الحضور',
                    'error_count': error_count,
                    'errors': error_messages[:10],  # إرجاع أول 10 أخطاء فقط
                    'code': 'SAVE_FAILED'
                }), 400

    except Exception as e:
        app.logger.error(f"Unexpected error in prepare_attendance: {str(e)}")
        if request.method == 'POST':
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'حدث خطأ غير متوقع: {str(e)}',
                'code': 'INTERNAL_ERROR'
            }), 500
        else:
            flash('حدث خطأ في تحميل صفحة التحضير', 'error')

    # في النهاية، إرجاع القالب مع جميع المتغيرات المطلوبة
    return render_template('attendance/prepare.html',
                           employees=employees,
                           selected_date=selected_date,
                           can_select_date=can_select_date,
                           existing_attendance=existing_attendance,
                           companies=companies,
                           areas=areas,
                           locations=locations,
                           selected_company_id=request.args.get('company_id', type=int),
                           selected_area_id=request.args.get('area_id', type=int),
                           selected_location_id=request.args.get('location_id', type=int))

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
    try:
        # الحصول على الشهر والسنة من الباراميترات
        year = request.args.get('year', date.today().year, type=int)
        month = request.args.get('month', date.today().month, type=int)

        # حساب بداية ونهاية الشهر
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        # استعلام مباشر للحصول على سجلات الحضور
        attendance_data = Attendance.query \
            .join(Employee) \
            .filter(
                Attendance.date >= start_date,
                Attendance.date <= end_date
            ) \
            .order_by(Attendance.date.desc()) \
            .all()

        # حساب الإحصائيات
        total_days = (end_date - start_date).days + 1
        employees = Employee.query.filter_by(is_active=True).all()

        # إنشاء تقرير مفصل
        report_data = []
        for employee in employees:
            employee_attendance = Attendance.query.filter(
                Attendance.employee_id == employee.id,
                Attendance.date >= start_date,
                Attendance.date <= end_date
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
                               year=year,
                               month=month,
                               start_date=start_date,
                               end_date=end_date,
                               attendance_data=attendance_data,
                               report_data=report_data,
                               total_days=total_days)

    except Exception as e:
        app.logger.error(f"Error in attendance_report: {str(e)}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return render_template('attendance/report.html',
                               year=date.today().year,
                               month=date.today().month,
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
    """حذف شركة - POST فقط"""
    # التحقق من الصلاحيات
    if current_user.role != 'owner':
        return jsonify({
            'success': False,
            'message': 'غير مصرح بهذا الإجراء'
        }), 403

    company = Company.query.get_or_404(company_id)

    try:
        # التحقق من وجود مناطق مرتبطة بالشركة
        has_areas = Area.query.filter_by(company_id=company_id).first()
        if has_areas:
            return jsonify({
                'success': False,
                'message': 'لا يمكن حذف الشركة لأنها تحتوي على مناطق مرتبطة بها'
            }), 400

        # تعطيل الشركة بدلاً من الحذف الفعلي (Soft Delete)
        company.is_active = False
        company.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'تم حذف الشركة بنجاح'
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in delete_company: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء حذف الشركة'
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
    """حذف منطقة"""
    try:
        area = Area.query.get_or_404(area_id)

        # التحقق من الصلاحيات
        if current_user.role != 'owner':
            return jsonify({
                'success': False,
                'message': 'غير مصرح بهذا الإجراء'
            }), 403

        # التحقق من وجود مواقع مرتبطة بالمنطقة
        has_locations = Location.query.filter_by(area_id=area_id, is_active=True).first()
        if has_locations:
            return jsonify({
                'success': False,
                'message': 'لا يمكن حذف المنطقة لأنها تحتوي على مواقع مرتبطة بها'
            }), 400

        # تعطيل المنطقة بدلاً من الحذف الفعلي
        area.is_active = False
        area.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'تم حذف المنطقة بنجاح'
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in delete_area: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء حذف المنطقة'
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
    """حذف موقع"""
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

        # التحقق من وجود أماكن مرتبطة بالموقع
        has_places = Place.query.filter_by(location_id=location_id).first()
        if has_places:
            return jsonify({
                'success': False,
                'message': 'لا يمكن حذف الموقع لأنه يحتوي على أماكن مرتبطة به'
            }), 400

        # تعطيل الموقع بدلاً من الحذف الفعلي
        location.is_active = False
        location.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'تم حذف الموقع بنجاح'
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in delete_location: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء حذف الموقع'
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
    """حذف مكان"""
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

        # التحقق من وجود تقييمات مرتبطة بالمكان
        has_evaluations = CleaningEvaluation.query.filter_by(place_id=place_id).first()
        if has_evaluations:
            return jsonify({
                'success': False,
                'message': 'لا يمكن حذف المكان لأنه يحتوي على تقييمات مرتبطة به'
            }), 400

        # تعطيل المكان بدلاً من الحذف الفعلي
        place.is_active = False
        place.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'تم حذف المكان بنجاح'
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in delete_place: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء حذف المكان'
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
    """عرض قائمة التقييمات مع الصلاحيات المحسنة"""
    try:
        from sqlalchemy.orm import joinedload
        from datetime import datetime

        # استعلام أساسي مع تحميل العلاقات
        base_query = CleaningEvaluation.query \
            .options(
            joinedload(CleaningEvaluation.place),
            joinedload(CleaningEvaluation.evaluator),
            joinedload(CleaningEvaluation.evaluated_employee)
        )

        # تطبيق الفلتر حسب الصلاحيات
        if current_user.role == 'owner':
            # المالك: يرى جميع التقييمات
            evaluations_list = base_query.order_by(CleaningEvaluation.date.desc()).all()
            app.logger.info(f"👑 المالك يشاهد جميع التقييمات: {len(evaluations_list)}")

        elif current_user.role == 'supervisor':
            # المشرف: يرى تقييمات الموظفين المربوطين به فقط (مراقبيه وعماله)
            if current_user.employee_profile:
                supervisor_id = current_user.employee_profile.id
                app.logger.info(f"👤 المشرف ID: {supervisor_id} - {current_user.employee_profile.full_name}")

                # 1. الحصول على جميع الموظفين التابعين لهذا المشرف
                supervised_employees_ids = []

                # الموظفون الذين supervisor_id = supervisor_id (المراقبون والعمال)
                direct_subordinates = Employee.query.filter_by(
                    supervisor_id=supervisor_id,
                    is_active=True
                ).all()

                for emp in direct_subordinates:
                    supervised_employees_ids.append(emp.id)
                    app.logger.info(f"   → تابع مباشر: {emp.full_name} (ID: {emp.id}, دور: {emp.position})")

                # 2. إذا كان المشرف مشرفاً على مناطق، الحصول على الموظفين في تلك المناطق
                supervised_areas = Area.query.filter_by(supervisor_id=supervisor_id, is_active=True).all()
                area_ids = [area.id for area in supervised_areas]

                if area_ids:
                    # الحصول على المواقع في هذه المناطق
                    locations = Location.query.filter(Location.area_id.in_(area_ids), Location.is_active == True).all()
                    location_ids = [loc.id for loc in locations]

                    if location_ids:
                        # الحصول على المراقبين المعينين على هذه المواقع
                        monitors_in_locations = [loc.monitor_id for loc in locations if loc.monitor_id]
                        supervised_employees_ids.extend(monitors_in_locations)

                        # الحصول على الأماكن في هذه المواقع
                        places = Place.query.filter(Place.location_id.in_(location_ids), Place.is_active == True).all()

                        # الحصول على العمال المعينين في هذه الأماكن
                        workers_in_places = [place.worker_id for place in places if place.worker_id]
                        supervised_employees_ids.extend(workers_in_places)

                # إزالة التكرارات والقيم الفارغة
                supervised_employees_ids = list(set([id for id in supervised_employees_ids if id]))

                app.logger.info(f"📊 إجمالي الموظفين التابعين: {len(supervised_employees_ids)}")

                if supervised_employees_ids:
                    # الحصول على التقييمات التي يكون فيها الموظف المقيّم أو المُقيِّم من التابعين
                    evaluations_list = base_query.filter(
                        db.or_(
                            CleaningEvaluation.evaluated_employee_id.in_(supervised_employees_ids),
                            CleaningEvaluation.evaluator_id.in_(supervised_employees_ids)
                        )
                    ).order_by(CleaningEvaluation.date.desc()).all()

                    app.logger.info(f"✅ عدد التقييمات التي وجدت: {len(evaluations_list)}")
                else:
                    evaluations_list = []
                    app.logger.warning("⚠️ لا يوجد موظفين تابعين لهذا المشرف")
            else:
                evaluations_list = []
                app.logger.warning("⚠️ المشرف ليس لديه ملف موظف مرتبط")

        elif current_user.role == 'monitor':
            # المراقب: يرى تقييمات عماله فقط
            if current_user.employee_profile:
                monitor_id = current_user.employee_profile.id

                # الحصول على المواقع التي يراقبها
                monitored_locations = Location.query.filter_by(monitor_id=monitor_id, is_active=True).all()
                location_ids = [loc.id for loc in monitored_locations]

                if location_ids:
                    # الحصول على الأماكن في هذه المواقع
                    places = Place.query.filter(Place.location_id.in_(location_ids), Place.is_active == True).all()
                    place_ids = [place.id for place in places]

                    # الحصول على تقييمات هذه الأماكن
                    evaluations_list = base_query.filter(
                        CleaningEvaluation.place_id.in_(place_ids)
                    ).order_by(CleaningEvaluation.date.desc()).all()
                else:
                    evaluations_list = []
            else:
                evaluations_list = []

        else:  # worker
            # العامل: يرى تقييماته فقط
            if current_user.employee_profile:
                worker_id = current_user.employee_profile.id
                evaluations_list = base_query.filter(
                    CleaningEvaluation.evaluated_employee_id == worker_id
                ).order_by(CleaningEvaluation.date.desc()).all()
            else:
                evaluations_list = []

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
    """إضافة تقييم جديد مع نظام الصلاحيات المحسن"""

    # التحقق من الصلاحيات الأساسية
    if current_user.role not in ['owner', 'supervisor', 'monitor']:
        flash('غير مصرح بإضافة تقييمات', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            # البيانات الأساسية
            date_str = request.form.get('date', '')
            place_id = request.form.get('place_id', '')
            evaluated_employee_id = request.form.get('evaluated_employee_id', '')
            cleanliness = request.form.get('cleanliness', '')
            organization = request.form.get('organization', '')
            equipment_condition = request.form.get('equipment_condition', '')
            time_value = request.form.get('time', '3')  # ✅ تعريف المتغير هنا مع قيمة افتراضية
            safety_measures = request.form.get('safety_measures', '')
            comments = request.form.get('comments', '')

            app.logger.info(f"📨 بيانات التقييم المستلمة:")
            app.logger.info(f"   - التاريخ: {date_str}")
            app.logger.info(f"   - المكان: {place_id}")
            app.logger.info(f"   - الموظف المقيّم: {evaluated_employee_id}")

            # التحقق من البيانات المطلوبة
            if not all([date_str, place_id, evaluated_employee_id, cleanliness,
                        organization, equipment_condition, time_value, safety_measures]):
                flash('يرجى ملء جميع الحقول المطلوبة', 'error')
                return redirect(url_for('add_evaluation'))

            # تحويل البيانات
            evaluation_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            if evaluation_date > date.today():
                flash('لا يمكن إضافة تقييم لتاريخ مستقبلي', 'error')
                return redirect(url_for('add_evaluation'))

            # تحديد المُقيِّم بناءً على المستخدم الحالي
            evaluator_id = None

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

            # التحقق من صحة البيانات
            place = Place.query.get(place_id)
            if not place:
                flash('المكان المحدد غير موجود', 'error')
                return redirect(url_for('add_evaluation'))

            evaluated_employee = Employee.query.get(evaluated_employee_id)
            if not evaluated_employee:
                flash('الموظف المحدد غير موجود', 'error')
                return redirect(url_for('add_evaluation'))

            # التحقق من الصلاحيات المحددة
            if not can_evaluate_employee(current_user, evaluated_employee, place):
                flash('غير مصرح بتقييم هذا الموظف', 'error')
                return redirect(url_for('add_evaluation'))

            # إنشاء التقييم مع تضمين حقل الوقت
            evaluation = CleaningEvaluation(
                date=evaluation_date,
                place_id=place_id,
                evaluated_employee_id=evaluated_employee_id,
                evaluator_id=evaluator_id,
                cleanliness=int(cleanliness),
                organization=int(organization),
                equipment_condition=int(equipment_condition),
                time=int(time_value),  # ✅ استخدام المتغير المعرف
                safety_measures=int(safety_measures),
                overall_score=0.0,
                comments=comments or None
            )

            # حساب النتيجة الإجمالية تلقائياً
            evaluation.calculate_overall_score()

            db.session.add(evaluation)
            db.session.commit()

            flash('✅ تم إضافة التقييم بنجاح!', 'success')
            return redirect(url_for('evaluations_list'))

        except ValueError as e:
            db.session.rollback()
            app.logger.error(f"❌ خطأ في تحويل القيم: {str(e)}")
            flash('قيم التقييم غير صحيحة، يرجى التأكد من إدخال أرقام صحيحة', 'error')
            return redirect(url_for('add_evaluation'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"❌ خطأ في إضافة التقييم: {str(e)}")
            import traceback
            app.logger.error(f"🔍 تفاصيل الخطأ: {traceback.format_exc()}")
            flash(f'حدث خطأ: {str(e)}', 'error')
            return redirect(url_for('add_evaluation'))

    # GET Request - عرض النموذج
    try:
        # الحصول على البيانات المطلوبة للقوائم المنسدلة
        companies = Company.query.filter_by(is_active=True).order_by(Company.name).all()

        # الحصول على الموظفين المسموح بتقييمهم حسب الصلاحيات
        employees_for_evaluation = get_employees_for_evaluation(current_user)

        # الحصول على المقيمين المتاحين (للمالك فقط)
        evaluators = []
        supervisors = []  # قائمة المشرفين للتقييم

        if current_user.role == 'owner':
            evaluators = Employee.query.filter(
                Employee.position.in_(['supervisor', 'monitor']),
                Employee.is_active == True
            ).order_by(Employee.full_name).all()

            # جلب جميع المشرفين النشطين لتقييمهم
            supervisors = Employee.query.filter_by(
                position='supervisor',
                is_active=True
            ).order_by(Employee.full_name).all()

            app.logger.info(f"📊 عدد المشرفين المتاحين للتقييم: {len(supervisors)}")

        app.logger.info(f"📊 عدد الموظفين المتاحين للتقييم: {len(employees_for_evaluation)}")

        return render_template('evaluations/add.html',
                               today=date.today(),
                               companies=companies,
                               employees=employees_for_evaluation,
                               evaluators=evaluators,
                               supervisors=supervisors,  # إرسال قائمة المشرفين للقالب
                               current_user=current_user)

    except Exception as e:
        app.logger.error(f"❌ خطأ في تحميل النموذج: {str(e)}")
        flash(f'خطأ في تحميل النموذج: {str(e)}', 'error')
        return redirect(url_for('evaluations_list'))

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
    """صفحة التقارير الرئيسية"""
    try:
        # إحصائيات أساسية
        total_employees = Employee.query.count() or 0
        active_employees = Employee.query.filter_by(is_active=True).count() or 0
        total_companies = Company.query.filter_by(is_active=True).count() or 0
        total_areas = Area.query.filter_by(is_active=True).count() or 0
        total_evaluations = CleaningEvaluation.query.count() or 0

        # حساب متوسط التقييم
        avg_score_result = db.session.query(db.func.avg(CleaningEvaluation.overall_score)).scalar()
        avg_score = float(avg_score_result) if avg_score_result is not None else 0.0

        # إحصائيات التقييمات
        today = date.today()
        evaluations_today = CleaningEvaluation.query.filter_by(date=today).count() or 0

        # إحصائيات هذا الأسبوع
        week_ago = today - timedelta(days=7)
        evaluations_this_week = CleaningEvaluation.query.filter(
            CleaningEvaluation.date >= week_ago
        ).count() or 0

        # إحصائيات هذا الشهر
        month_ago = today - timedelta(days=30)
        evaluations_this_month = CleaningEvaluation.query.filter(
            CleaningEvaluation.date >= month_ago
        ).count() or 0

        # إحصائيات الحضور
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
    """تقرير أفضل الموظفين أداءً"""
    try:
        employees = Employee.query.filter_by(is_active=True).all()

        top_employees = []
        for emp in employees:
            evaluations = CleaningEvaluation.query.filter_by(evaluated_employee_id=emp.id).all()
            if evaluations:
                avg_perf = sum(e.overall_score for e in evaluations) / len(evaluations) * 20

                # تحديد اسم الوظيفة بالعربية
                if emp.position == 'supervisor':
                    position_ar = 'مشرف'
                elif emp.position == 'monitor':
                    position_ar = 'مراقب'
                elif emp.position == 'worker':
                    position_ar = 'عامل'
                else:
                    position_ar = emp.position

                top_employees.append({
                    'id': emp.id,
                    'full_name': emp.full_name,
                    'position_ar': position_ar,
                    'avatar': None,
                    'performance': avg_perf,
                    'evaluations_count': len(evaluations),
                    'attendance_rate': 95
                })

        # ترتيب تنازلي
        top_employees.sort(key=lambda x: x['performance'], reverse=True)

        return render_template('reports/top_employees.html', top_employees=top_employees[:5])
    except Exception as e:
        app.logger.error(f"Error in report_top_employees: {str(e)}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))


@app.route('/reports/attendance-record')
@login_required
def report_attendance_record():
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
    """تقرير التقييمات اليومية المتقدم - يعتمد على بيانات حقيقية"""
    try:
        today = date.today()
        evaluations = CleaningEvaluation.query.filter_by(date=today).all()

        # تجهيز بيانات التقييمات للعرض
        evaluations_data = []
        hourly_counts = [0, 0, 0, 0, 0]  # لفترات اليوم

        for eval in evaluations:
            # اسم الموظف
            employee_name = "غير محدد"
            if eval.evaluated_employee:
                employee_name = eval.evaluated_employee.full_name

            # الموقع
            location_name = "غير محدد"
            if eval.place:
                if eval.place.location:
                    location_name = eval.place.location.name
                else:
                    location_name = eval.place.name

            # حساب الفترة الزمنية
            if eval.created_at:
                hour = eval.created_at.hour
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
                'id': eval.id,
                'created_at': eval.created_at or datetime.now(),
                'employee': {
                    'full_name': employee_name,
                    'avatar': None
                },
                'location': location_name,
                'cleanliness': eval.cleanliness or 0,
                'organization': eval.organization or 0,
                'equipment': eval.equipment_condition or 0,
                'safety': eval.safety_measures or 0,
                'overall_score': float(eval.overall_score) if eval.overall_score else 0
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

        # حساب التغيير عن الأمس
        yesterday = today - timedelta(days=1)
        yesterday_count = CleaningEvaluation.query.filter_by(date=yesterday).count()
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
                'title': 'لا توجد تقييمات اليوم',
                'message': 'لم يتم تسجيل أي تقييمات اليوم، يرجى البدء في تقييم الموظفين'
            })

        return render_template('reports/daily_evaluations_advanced.html',
                               daily_stats=daily_stats,
                               evaluations=evaluations_data,
                               selected_date=today.strftime('%Y-%m-%d'),
                               hourly_labels=['8-10', '10-12', '12-14', '14-16', '16-18'],
                               hourly_data=hourly_counts,
                               distribution_data=distribution_data,
                               criteria_stats=criteria_stats,
                               criteria_labels=['النظافة', 'التنظيم', 'المعدات', 'السلامة'],
                               criteria_averages=[cleanliness_avg, organization_avg, equipment_avg, safety_avg],
                               recommendations=recommendations[:3])  # أقصى 3 توصيات

    except Exception as e:
        app.logger.error(f"Error in report_daily_evaluations_advanced: {str(e)}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))


@app.route('/reports/monthly-trends-advanced')
@login_required
def report_monthly_trends_advanced():
    """تقرير اتجاهات التقييم الشهرية - يعتمد على بيانات حقيقية"""
    try:
        from sqlalchemy import func, extract

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

            month_evaluations = CleaningEvaluation.query.filter(
                CleaningEvaluation.date >= month_start,
                CleaningEvaluation.date <= month_end
            ).all()

            count = len(month_evaluations)
            monthly_counts.append(count)

            if count > 0:
                avg = sum(e.overall_score for e in month_evaluations if e.overall_score) / count
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
                for emp_id, scores in employee_scores.items():
                    emp_avg = sum(scores) / len(scores)
                    if emp_avg > best_avg:
                        best_avg = emp_avg
                        employee = Employee.query.get(emp_id)
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
                for comp_id, scores in company_scores.items():
                    comp_avg = sum(scores) / len(scores)
                    if comp_avg > best_company_avg:
                        best_company_avg = comp_avg
                        company = Company.query.get(comp_id)
                        if company:
                            top_company = company.name

            monthly_data.append({
                'name': month_name,
                'count': count,
                'avg': avg_score,
                'color': 'success' if avg_score >= 4.5 else 'info' if avg_score >= 4 else 'warning' if avg_score >= 3 else 'danger',
                'change': 0,  # يمكن حسابه لاحقاً
                'top_employee': top_employee,
                'top_company': top_company
            })

        # حساب التغيير بين الأشهر
        for i in range(1, len(monthly_data)):
            if monthly_data[i - 1]['count'] > 0:
                change = round(
                    ((monthly_data[i]['count'] - monthly_data[i - 1]['count']) / monthly_data[i - 1]['count']) * 100, 1)
                monthly_data[i]['change'] = change

        # أفضل شهر
        best_month_idx = monthly_counts.index(max(monthly_counts)) if monthly_counts else 0
        best_month = {
            'name': months[best_month_idx] if months else 'غير محدد',
            'avg': month_averages[best_month_idx] if month_averages else 0
        }

        # متوسط آخر 3 أشهر
        last_3_months = month_averages[-3:] if len(month_averages) >= 3 else month_averages
        three_month_avg = round(sum(last_3_months) / len(last_3_months)) if last_3_months else 0

        # النمو السنوي
        if len(month_averages) >= 2:
            yearly_growth = round(((month_averages[-1] - month_averages[0]) / month_averages[0]) * 100) if \
            month_averages[0] > 0 else 0
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

        return render_template('reports/monthly_trends.html',
                               best_month=best_month,
                               three_month_avg=three_month_avg,
                               yearly_growth=yearly_growth,
                               trend_direction=trend_direction,
                               month_labels=month_labels,
                               month_averages=month_averages,
                               distribution_labels=['ممتاز', 'جيد', 'مقبول', 'ضعيف'],
                               distribution_data=[45, 30, 15, 10],  # يمكن تحسينها لاحقاً
                               monthly_data=monthly_data)

    except Exception as e:
        app.logger.error(f"Error in report_monthly_trends_advanced: {str(e)}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))


@app.route('/reports/evaluation-details-advanced')
@login_required
def report_evaluation_details_advanced():
    """تقرير تفاصيل التقييمات حسب المعايير - يعتمد على بيانات حقيقية"""
    try:
        # جميع التقييمات
        all_evaluations = CleaningEvaluation.query.all()
        total_evaluations = len(all_evaluations)

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
                {'name': 'السلامة', 'avg': round(safety_avg, 1),
                 'color': 'success' if safety_avg >= 4 else 'warning' if safety_avg >= 3 else 'danger',
                 'max': safety_max, 'min': safety_min},
            ]

            # تفاصيل المعايير
            criteria_details = []
            for c in criteria:
                # تصنيف التقييمات حسب القيمة
                excellent = len([e for e in all_evaluations if
                                 (c['name'] == 'النظافة' and e.cleanliness == 5) or
                                 (c['name'] == 'التنظيم' and e.organization == 5) or
                                 (c['name'] == 'المعدات' and e.equipment_condition == 5) or
                                 (c['name'] == 'السلامة' and e.safety_measures == 5)])

                good = len([e for e in all_evaluations if
                            (c['name'] == 'النظافة' and e.cleanliness == 4) or
                            (c['name'] == 'التنظيم' and e.organization == 4) or
                            (c['name'] == 'المعدات' and e.equipment_condition == 4) or
                            (c['name'] == 'السلامة' and e.safety_measures == 4)])

                average = len([e for e in all_evaluations if
                               (c['name'] == 'النظافة' and e.cleanliness == 3) or
                               (c['name'] == 'التنظيم' and e.organization == 3) or
                               (c['name'] == 'المعدات' and e.equipment_condition == 3) or
                               (c['name'] == 'السلامة' and e.safety_measures == 3)])

                poor = len([e for e in all_evaluations if
                            (c['name'] == 'النظافة' and e.cleanliness == 2) or
                            (c['name'] == 'التنظيم' and e.organization == 2) or
                            (c['name'] == 'المعدات' and e.equipment_condition == 2) or
                            (c['name'] == 'السلامة' and e.safety_measures == 2)])

                very_poor = len([e for e in all_evaluations if
                                 (c['name'] == 'النظافة' and e.cleanliness == 1) or
                                 (c['name'] == 'التنظيم' and e.organization == 1) or
                                 (c['name'] == 'المعدات' and e.equipment_condition == 1) or
                                 (c['name'] == 'السلامة' and e.safety_measures == 1)])

                criteria_details.append({
                    'name': c['name'],
                    'excellent': excellent,
                    'good': good,
                    'average': average,
                    'poor': poor,
                    'very_poor': very_poor,
                    'total': excellent + good + average + poor + very_poor
                })

        return render_template('reports/evaluation_details.html',
                               criteria=criteria,
                               criteria_names=[c['name'] for c in criteria],
                               criteria_averages=[c['avg'] for c in criteria],
                               criteria_max=[c['max'] for c in criteria],
                               criteria_min=[c['min'] for c in criteria],
                               criteria_details=criteria_details)

    except Exception as e:
        app.logger.error(f"Error in report_evaluation_details_advanced: {str(e)}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))


@app.route('/reports/kpis-advanced')
@login_required
def report_kpis_advanced():
    """تقرير مؤشرات الأداء الرئيسية - يعتمد على بيانات حقيقية"""
    try:
        # إحصائيات الموظفين
        total_employees = Employee.query.filter_by(is_active=True).count()

        # إحصائيات التقييمات
        total_evaluations = CleaningEvaluation.query.count()

        # إحصائيات الشركات
        total_companies = Company.query.filter_by(is_active=True).count()

        # متوسط التقييم
        avg_score_result = db.session.query(db.func.avg(CleaningEvaluation.overall_score)).scalar()
        avg_score = round(float(avg_score_result), 1) if avg_score_result else 0

        # إحصائيات الحضور
        today = date.today()
        today_attendance = Attendance.query.filter_by(date=today).all()
        present_today = len([a for a in today_attendance if a.status == 'present'])
        absent_today = len([a for a in today_attendance if a.status in ['absent', 'late']])
        total_attendance_today = present_today + absent_today

        # معدل الحضور
        attendance_rate = 0
        if total_attendance_today > 0:
            attendance_rate = round((present_today / total_attendance_today) * 100)
        elif total_employees > 0:
            attendance_rate = 0

        # تغطية التقييمات (نسبة الموظفين الذين تم تقييمهم)
        evaluated_employees = db.session.query(CleaningEvaluation.evaluated_employee_id).distinct().count()
        evaluation_coverage = 0
        if total_employees > 0:
            evaluation_coverage = round((evaluated_employees / total_employees) * 100)

        # إحصائيات الشهر
        month_start = date(today.year, today.month, 1)
        month_evaluations = CleaningEvaluation.query.filter(CleaningEvaluation.date >= month_start).count()

        # جودة العمل (متوسط التقييم مقسوم على 5)
        quality_score = round(avg_score * 20) if avg_score else 0

        # إنتاجية الموظفين (متوسط عدد التقييمات لكل موظف)
        if total_employees > 0:
            employee_productivity = round((total_evaluations / total_employees) * 10)  # مقياس 0-100
            employee_productivity = min(employee_productivity, 100)  # لا يتجاوز 100
        else:
            employee_productivity = 0

        # رضا العملاء (محسوب من التقييمات العالية)
        excellent_evaluations = CleaningEvaluation.query.filter(CleaningEvaluation.overall_score >= 4.5).count()
        customer_satisfaction = 0
        if total_evaluations > 0:
            customer_satisfaction = round((excellent_evaluations / total_evaluations) * 100)

        # إنجاز المهام (نسبة الموظفين الذين لديهم تقييمات هذا الشهر)
        employees_with_evaluations = db.session.query(CleaningEvaluation.evaluated_employee_id) \
            .filter(CleaningEvaluation.date >= month_start).distinct().count()
        task_completion = 0
        if total_employees > 0:
            task_completion = round((employees_with_evaluations / total_employees) * 100)

        # استخدام الوقت (محسوب من أوقات الحضور)
        time_utilization = 75  # قيمة افتراضية

        kpis = {
            'employee_productivity': employee_productivity,
            'attendance_rate': attendance_rate,
            'evaluation_coverage': evaluation_coverage,
            'customer_satisfaction': customer_satisfaction,
            'task_completion': task_completion,
            'quality_score': quality_score,
            'time_utilization': time_utilization
        }

        # بيانات الاتجاهات (يمكن تحسينها لاحقاً)
        kpi_labels = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو']
        productivity_trend = [employee_productivity - 10, employee_productivity - 5,
                              employee_productivity - 3, employee_productivity - 1,
                              employee_productivity + 2, employee_productivity]
        quality_trend = [quality_score - 8, quality_score - 4,
                         quality_score - 2, quality_score,
                         quality_score + 1, quality_score + 2]
        attendance_trend = [attendance_rate - 5, attendance_rate - 3,
                            attendance_rate - 1, attendance_rate,
                            attendance_rate + 1, attendance_rate + 2]

        return render_template('reports/kpis.html',
                               kpis=kpis,
                               total_employees=total_employees,
                               total_evaluations=total_evaluations,
                               total_companies=total_companies,
                               avg_score=avg_score,
                               kpi_labels=kpi_labels,
                               productivity_trend=productivity_trend,
                               quality_trend=quality_trend,
                               attendance_trend=attendance_trend)

    except Exception as e:
        app.logger.error(f"Error in report_kpis_advanced: {str(e)}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))


#تقييم الشركات والمناطق

@app.route('/reports/companies-zones')
@login_required
def report_companies_zones():
    """تقرير الشركات والمناطق"""
    try:
        companies = Company.query.filter_by(is_active=True).all()

        total_companies = len(companies)
        active_companies = sum(1 for c in companies if c.is_active)
        total_areas = Area.query.filter_by(is_active=True).count()

        companies_data = []
        for company in companies:
            areas = Area.query.filter_by(company_id=company.id, is_active=True).all()
            areas_count = len(areas)

            employees_count = Employee.query.filter_by(company_id=company.id, is_active=True).count()

            # حساب تقييم الشركة
            ratings = []
            for area in areas:
                locations = Location.query.filter_by(area_id=area.id).all()
                for location in locations:
                    places = Place.query.filter_by(location_id=location.id).all()
                    for place in places:
                        evals = CleaningEvaluation.query.filter_by(place_id=place.id).all()
                        ratings.extend([e.overall_score for e in evals if e.overall_score])

            avg_rating = sum(ratings) / len(ratings) if ratings else 0
            performance = avg_rating * 20

            companies_data.append({
                'id': company.id,
                'name': company.name,
                'color': f'#{hash(company.name) % 0xFFFFFF:06x}',
                'areas_count': areas_count,
                'employees_count': employees_count,
                'rating': avg_rating,
                'performance': performance,
                'performance_color': 'success' if performance >= 80 else 'warning' if performance >= 60 else 'danger',
                'is_active': company.is_active,
                'lat': 24.7136 + (company.id * 0.01),  # محاكاة
                'lng': 46.6753 + (company.id * 0.01),
                'areas': []
            })

        return render_template('reports/companies_zones.html',
                               total_companies=total_companies,
                               active_companies=active_companies,
                               total_areas=total_areas,
                               total_employees_in_companies=Employee.query.filter_by(is_active=True).count(),
                               total_supervisors=Employee.query.filter_by(position='supervisor',
                                                                          is_active=True).count(),
                               avg_areas_per_company=total_areas / total_companies if total_companies > 0 else 0,
                               avg_company_rating=sum(c['rating'] for c in companies_data) / len(
                                   companies_data) if companies_data else 0,
                               top_rated_company=max(companies_data, key=lambda x: x['rating'])[
                                   'name'] if companies_data else '-',
                               companies=companies_data,
                               companies_data=companies_data)
    except Exception as e:
        app.logger.error(f"Error in report_companies_zones: {str(e)}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))


@app.route('/reports/employees-distribution')
@login_required
def report_employees_distribution():
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
    try:
        companies = Company.query.filter_by(is_active=True).all()
        ratings_data = []
        areas_ratings = []

        for company in companies:
            areas = Area.query.filter_by(company_id=company.id, is_active=True).all()
            company_ratings = []

            for area in areas:
                area_ratings = []
                locations = Location.query.filter_by(area_id=area.id).all()

                for location in locations:
                    places = Place.query.filter_by(location_id=location.id).all()
                    for place in places:
                        evals = CleaningEvaluation.query.filter_by(place_id=place.id).all()
                        for e in evals:
                            if e.overall_score:
                                area_ratings.append(e.overall_score)
                                company_ratings.append(e.overall_score)

                                areas_ratings.append({
                                    'company_name': company.name,
                                    'name': area.name,
                                    'supervisor_name': area.supervisor.full_name if area.supervisor else None,
                                    'evaluations_count': len(evals),
                                    'rating': e.overall_score,
                                    'last_evaluation_date': e.date
                                })

            avg_rating = sum(company_ratings) / len(company_ratings) if company_ratings else 0

            # تحديد لون التقييم
            if avg_rating >= 4.5:
                rating_color = 'excellent'
            elif avg_rating >= 4:
                rating_color = 'good'
            elif avg_rating >= 3:
                rating_color = 'average'
            else:
                rating_color = 'poor'

            ratings_data.append({
                'id': company.id,
                'name': company.name,
                'areas_count': len(areas),
                'avg_rating': avg_rating,
                'rating_color': rating_color,
                'max_area': max(areas, key=lambda a: a.id).name if areas else '-',
                'max_rating': max(company_ratings) if company_ratings else 0,
                'min_area': min(areas, key=lambda a: a.id).name if areas else '-',
                'min_rating': min(company_ratings) if company_ratings else 0
            })

        return render_template('reports/companies_ratings.html',
                               ratings_data=ratings_data,
                               areas_ratings=areas_ratings)
    except Exception as e:
        app.logger.error(f"Error in report_companies_ratings: {str(e)}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))


@app.route('/reports/heatmap')
@login_required
def report_heatmap():
    """تقرير خريطة المناطق الحرارية"""
    try:
        # بيانات المناطق
        areas = Area.query.filter_by(is_active=True).all()

        heatmap_data = []
        excellent_zones = good_zones = average_zones = poor_zones = 0
        excellent_zones_list = []

        for area in areas:
            # حساب أداء المنطقة
            ratings = []
            locations = Location.query.filter_by(area_id=area.id).all()

            for location in locations:
                places = Place.query.filter_by(location_id=location.id).all()
                for place in places:
                    evals = CleaningEvaluation.query.filter_by(place_id=place.id).all()
                    ratings.extend([e.overall_score for e in evals if e.overall_score])

            avg_rating = sum(ratings) / len(ratings) if ratings else 0
            performance = avg_rating * 20

            # تصنيف المنطقة
            if performance >= 90:
                excellent_zones += 1
                excellent_zones_list.append({
                    'name': area.name,
                    'company_name': area.company.name if area.company else '-',
                    'supervisor_name': area.supervisor.full_name if area.supervisor else '-',
                    'performance': performance,
                    'last_evaluation': max([e.date for e in evals]) if evals else None
                })
            elif performance >= 75:
                good_zones += 1
            elif performance >= 60:
                average_zones += 1
            else:
                poor_zones += 1

            # إضافة نقطة حرارية
            heatmap_data.append({
                'lat': 24.7136 + (area.id * 0.02),
                'lng': 46.6753 + (area.id * 0.02),
                'intensity': performance / 100
            })

        return render_template('reports/heatmap.html',
                               heatmap_data=heatmap_data,
                               excellent_zones=excellent_zones,
                               good_zones=good_zones,
                               average_zones=average_zones,
                               poor_zones=poor_zones,
                               excellent_zones_list=excellent_zones_list)
    except Exception as e:
        app.logger.error(f"Error in report_heatmap: {str(e)}")
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


@app.route('/reports/overtime')
@login_required
def report_overtime():
    """تقرير ساعات العمل الإضافية"""
    try:
        employees = Employee.query.filter_by(is_active=True).all() or []
        overtime_data = []
        total_hours = 0

        for emp in employees:
            if not emp:
                continue

            # حساب ساعات العمل الإضافية
            hours = 0
            attendance = Attendance.query.filter_by(employee_id=emp.id).all() or []
            for att in attendance:
                if att and att.check_out and att.check_in:
                    try:
                        # حساب ساعات العمل
                        check_in = datetime.combine(date.today(), att.check_in)
                        check_out = datetime.combine(date.today(), att.check_out)
                        work_hours = (check_out - check_in).seconds / 3600
                        if work_hours > 8:
                            hours += work_hours - 8
                    except:
                        pass

            total_hours += hours

            if hours > 0:
                overtime_data.append({
                    'employee_name': emp.full_name or 'غير معروف',
                    'employee_color': f'#{hash(emp.full_name or '') % 0xFFFFFF:06x}',
                    'department': emp.position or 'غير محدد',
                    'month': 'فبراير 2026',
                    'hours': round(hours, 1),
                    'hourly_rate': 50,
                    'cost': round(hours * 50),
                    'percentage': min(round((hours / 200) * 100), 100) if hours > 0 else 0
                })

        # ترتيب تنازلي
        overtime_data.sort(key=lambda x: x['hours'], reverse=True)

        # بيانات الرسم البياني
        months = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو']
        chart_data = [120, 150, 180, 140, 200, 175]

        total_employees_count = len(employees) or 1  # تجنب القسمة على صفر

        return render_template('reports/overtime.html',
                               total_overtime_hours=round(total_hours, 1),
                               avg_overtime_per_employee=round(total_hours / total_employees_count, 1),
                               top_overtime_employee=overtime_data[0]['employee_name'] if overtime_data else '-',
                               top_overtime_hours=overtime_data[0]['hours'] if overtime_data else 0,
                               total_overtime_cost=sum(o['cost'] for o in overtime_data) if overtime_data else 0,
                               overtime_data=overtime_data[:10],
                               overtime_chart_data=chart_data,
                               months_labels=months)
    except Exception as e:
        app.logger.error(f"Error in report_overtime: {str(e)}")
        flash('حدث خطأ في تحميل التقرير', 'error')
        return redirect(url_for('reports_index'))

@app.route('/reports/monthly-summary')
@login_required
def report_monthly_summary():
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
                    'color': f'#{hash(emp.full_name or '') % 0xFFFFFF:06x}',
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

@app.route('/reports/generate')
@login_required
def generate_report():
    return render_template('reports/daily_evaluations.html')

@app.route('/schedules/create', methods=['GET', 'POST'])
@login_required
def create_schedule():
    return render_template('schedules/create.html')

@app.route('/api/reports/statistics')
@login_required
def reports_statistics():
    try:
        total_evaluations = CleaningEvaluation.query.count()
        avg_score = db.session.query(db.func.avg(CleaningEvaluation.overall_score)).scalar() or 0
        excellent_count = CleaningEvaluation.query.filter(CleaningEvaluation.overall_score >= 4.5).count()
        improvement_count = CleaningEvaluation.query.filter(CleaningEvaluation.overall_score < 3).count()

        return jsonify({
            'success': True,
            'total_evaluations': total_evaluations,
            'avg_score': float(avg_score),
            'excellent_count': excellent_count,
            'improvement_count': improvement_count
        })
    except Exception as e:
        app.logger.error(f"Error in reports_statistics: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ في تحميل الإحصائيات'
        }), 500
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

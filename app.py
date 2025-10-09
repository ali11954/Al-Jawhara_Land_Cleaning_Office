from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Employee, Company, Area, Location, Place, CleaningEvaluation, Attendance
from config import Config
from datetime import datetime, date, timedelta
import json
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'يجب تسجيل الدخول للوصول إلى هذه الصفحة'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def initialize_database():
    """تهيئة قاعدة البيانات والبيانات الأولية"""
    with app.app_context():
        db.create_all()

        # Create default owner if not exists
        if not User.query.filter_by(role='owner').first():
            owner = User(
                username='owner',
                email='owner@jewel-land.com',
                role='owner',
                is_active=True
            )
            owner.set_password('admin123')
            db.session.add(owner)

            # Create sample supervisor
            supervisor_user = User(
                username='supervisor1',
                email='supervisor@jewel-land.com',
                role='supervisor',
                is_active=True
            )
            supervisor_user.set_password('supervisor123')
            db.session.add(supervisor_user)
            db.session.flush()

            supervisor = Employee(
                user_id=supervisor_user.id,
                full_name='محمد أحمد',
                phone='+966500000001',
                position='supervisor',
                salary=8000.0,
                hire_date=date.today(),
                is_active=True
            )
            db.session.add(supervisor)

            # Create sample monitor
            monitor_user = User(
                username='monitor1',
                email='monitor@jewel-land.com',
                role='monitor',
                is_active=True
            )
            monitor_user.set_password('monitor123')
            db.session.add(monitor_user)
            db.session.flush()

            monitor = Employee(
                user_id=monitor_user.id,
                full_name='خالد سعيد',
                phone='+966500000002',
                position='monitor',
                salary=5000.0,
                hire_date=date.today(),
                is_active=True
            )
            db.session.add(monitor)

            # Create sample worker
            worker_user = User(
                username='worker1',
                email='worker@jewel-land.com',
                role='worker',
                is_active=True
            )
            worker_user.set_password('worker123')
            db.session.add(worker_user)
            db.session.flush()

            worker = Employee(
                user_id=worker_user.id,
                full_name='علي حسن',
                phone='+966500000003',
                position='worker',
                salary=3000.0,
                hire_date=date.today(),
                is_active=True
            )
            db.session.add(worker)

            # Create sample company and areas
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

            # Create sample area
            area = Area(
                name='المنطقة الرئيسية',
                company_id=company.id,
                is_active=True
            )
            db.session.add(area)
            db.session.flush()

            # Create sample location
            location = Location(
                name='المبنى الإداري',
                area_id=area.id,
                is_active=True
            )
            db.session.add(location)
            db.session.flush()

            # Create sample place
            place = Place(
                name='الطابق الأرضي',
                location_id=location.id,
                is_active=True
            )
            db.session.add(place)

            db.session.commit()

            print("✅ تم تهيئة قاعدة البيانات والبيانات الأولية بنجاح")
            print("👥 تم إنشاء 3 موظفين تجريبيين:")
            print("   - مشرف: supervisor1 / supervisor123")
            print("   - مراقب: monitor1 / monitor123")
            print("   - عامل: worker1 / worker123")
            print("   - مالك: owner / admin123")


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
# Dashboard
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    # Basic stats
    total_employees = Employee.query.count()
    active_employees = Employee.query.filter_by(is_active=True).count()
    inactive_employees = total_employees - active_employees

    # Employee position stats
    supervisors_count = Employee.query.filter_by(position='supervisor', is_active=True).count()
    monitors_count = Employee.query.filter_by(position='monitor', is_active=True).count()
    workers_count = Employee.query.filter_by(position='worker', is_active=True).count()

    # Company and area stats
    total_companies = Company.query.filter_by(is_active=True).count()
    total_areas = Area.query.filter_by(is_active=True).count()

    # Evaluation stats
    total_evaluations_today = CleaningEvaluation.query.filter_by(date=date.today()).count()
    avg_score_today = db.session.query(db.func.avg(CleaningEvaluation.overall_score)) \
                          .filter(CleaningEvaluation.date == date.today()).scalar() or 0

    # This week evaluations
    week_ago = date.today() - timedelta(days=7)
    evaluations_this_week = CleaningEvaluation.query.filter(
        CleaningEvaluation.date >= week_ago
    ).count()

    # New employees this month
    month_ago = date.today() - timedelta(days=30)
    new_employees_this_month = Employee.query.filter(
        Employee.hire_date >= month_ago
    ).count()

    avg_score = db.session.query(db.func.avg(CleaningEvaluation.overall_score)) \
        .filter(CleaningEvaluation.date == date.today()).scalar()
    avg_score = avg_score or 0  # إذا لم يكن هناك تقييم، ضع 0

    stats = {
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
        'new_employees_this_month': new_employees_this_month
    }

    # Recent evaluations
    # Recent evaluations - مع التحميل الآمن للعلاقات
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
    # Recent employees
    recent_employees = Employee.query \
        .order_by(Employee.created_at.desc()) \
        .limit(5) \
        .all()
    # Top performers - استخدام العلاقات الجديدة
    top_performers = db.session.query(
        Employee,
        db.func.avg(CleaningEvaluation.overall_score).label('avg_score'),
        db.func.count(CleaningEvaluation.id).label('evaluations_count')
    ).join(CleaningEvaluation, CleaningEvaluation.evaluator_id == Employee.id) \
        .group_by(Employee.id) \
        .order_by(db.desc('avg_score')) \
        .limit(5) \
        .all()

    # Format top performers data
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
    return render_template('dashboard/index.html',
                           stats=stats,
                           recent_evaluations=recent_evaluations,
                           recent_employees=recent_employees,
                           top_performers=formatted_performers,
                           today=date.today())


# Employee Management (Owner only)
@app.route('/employees')
@login_required
def employees_list():
    if current_user.role != 'owner':
        flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))

    employees_list = Employee.query.all()
    return render_template('employees/list.html', employees=employees_list)


@app.route('/employees/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    # التحقق من الصلاحيات - للمالك فقط
    if current_user.role != 'owner':
        flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            # التحقق من عدم وجود مستخدم بنفس اسم المستخدم
            existing_user = User.query.filter_by(username=request.form['username']).first()
            if existing_user:
                flash('اسم المستخدم موجود مسبقاً', 'error')
                return render_template('employees/add.html', today=date.today())

            # Create user account
            user = User(
                username=request.form['username'],
                email=request.form['email'],
                role=request.form['position']
            )
            user.set_password(request.form['password'])
            db.session.add(user)
            db.session.flush()  # Get the user ID

            # Create employee profile
            employee = Employee(
                user_id=user.id,
                full_name=request.form['full_name'],
                phone=request.form.get('phone'),
                address=request.form.get('address'),
                position=request.form['position'],
                salary=float(request.form.get('salary', 0)),
                hire_date=datetime.strptime(request.form['hire_date'], '%Y-%m-%d').date(),
                is_active=request.form.get('is_active') == 'on'
            )
            db.session.add(employee)
            db.session.commit()

            flash('تم إضافة الموظف بنجاح', 'success')
            return redirect(url_for('employees_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة الموظف: {str(e)}', 'error')

    return render_template('employees/add.html', today=date.today())


from datetime import datetime, date, timedelta
from flask import request, jsonify, render_template, flash
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest

from datetime import datetime, date, timedelta
from flask import request, jsonify, render_template, flash
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest


@app.route('/attendance')
@login_required
def attendance_index():
    try:
        # الحصول على التاريخ المطلوب من الباراميتر أو استخدام تاريخ اليوم
        selected_date = request.args.get('date', date.today().isoformat())

        # التحقق من صحة التاريخ
        try:
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except ValueError:
            selected_date = date.today()

        # حساب التواريخ للتنقل بين الأيام
        prev_date = selected_date - timedelta(days=1)
        next_date = selected_date + timedelta(days=1)

        # استعلام آمن للحصول على سجلات الحضور للتاريخ المحدد
        attendance_records = []
        total_employees = 0
        present_count = 0
        absent_count = 0

        try:
            # استعلام مصحح بدون joinedload
            attendance_records = db.session.query(Attendance).join(Employee).filter(
                Attendance.date == selected_date
            ).order_by(Employee.full_name, Attendance.shift_type).all()

            # إحصائيات الحضور
            total_employees = Employee.query.filter_by(is_active=True).count()
            present_count = db.session.query(Attendance).filter(
                Attendance.date == selected_date,
                Attendance.status == 'present'
            ).count()
            absent_count = total_employees - present_count

            print(f"✅ تم تحميل {len(attendance_records)} سجل حضور")
            for record in attendance_records:
                print(f"   - {record.employee.full_name if record.employee else 'غير معروف'}: {record.status} - {record.shift_type}")

        except Exception as e:
            app.logger.error(f"Database error in attendance_index: {str(e)}")
            flash('حدث خطأ في تحميل بيانات الحضور', 'error')
            # محاولة بديلة
            try:
                attendance_records = Attendance.query.filter_by(date=selected_date).all()
                print(f"✅ تم تحميل {len(attendance_records)} سجل حضور (الطريقة البديلة)")
            except Exception as e2:
                print(f"❌ فشل الطريقة البديلة: {e2}")

        return render_template('attendance/index.html',
                               today=date.today(),
                               selected_date=selected_date,
                               prev_date=prev_date,
                               next_date=next_date,
                               attendance_records=attendance_records,
                               total_employees=total_employees,
                               present_count=present_count,
                               absent_count=absent_count)

    except Exception as e:
        app.logger.error(f"Error in attendance_index: {str(e)}")
        flash('حدث خطأ في تحميل بيانات الحضور', 'error')
        return render_template('attendance/index.html',
                               today=date.today(),
                               selected_date=date.today(),
                               attendance_records=[],
                               total_employees=0,
                               present_count=0,
                               absent_count=0)

@app.route('/attendance/add', methods=['GET', 'POST'])
@login_required
def add_attendance():
    if request.method == 'GET':
        try:
            # الحصول على الموظفين المسموح بتسجيل حضورهم حسب الصلاحيات
            employees = get_employees_for_attendance(current_user)

            # التاريخ الافتراضي هو اليوم
            default_date = date.today().isoformat()

            return render_template('attendance/add.html',
                                   employees=employees,
                                   default_date=default_date)

        except Exception as e:
            app.logger.error(f"Error in add_attendance (GET): {str(e)}")
            flash('حدث خطأ في تحميل بيانات الموظفين', 'error')
            return render_template('attendance/add.html', employees=[])

    elif request.method == 'POST':
        try:
            # التحقق من الصلاحيات
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

            # تنظيف البيانات المدخلة
            employee_id = request.form['employee_id'].strip()
            date_str = request.form['date'].strip()
            status = request.form['status'].strip()
            shift_type = request.form['shift_type'].strip()
            notes = request.form.get('notes', '').strip()
            check_in_time = request.form.get('check_in', '').strip()
            check_out_time = request.form.get('check_out', '').strip()

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

            # التحقق من صلاحيات المستخدم لتسجيل حضور هذا الموظف
            if not can_record_attendance(current_user, employee):
                return jsonify({
                    'success': False,
                    'message': 'غير مصرح بتسجيل حضور هذا الموظف',
                    'code': 'UNAUTHORIZED_EMPLOYEE'
                }), 403

            # التحقق من عدم تكرار سجل الحضور لنفس الموظف في نفس اليوم ونفس الوردية
            existing_attendance = Attendance.query.filter(
                Attendance.employee_id == employee_id,
                Attendance.date == attendance_date,
                Attendance.shift_type == shift_type
            ).first()

            if existing_attendance:
                shift_name = 'صباحية' if shift_type == 'morning' else 'مسائية'
                return jsonify({
                    'success': False,
                    'message': f'تم تسجيل الحضور لهذا الموظف مسبقاً في الوردية {shift_name} لهذا التاريخ',
                    'code': 'DUPLICATE_ATTENDANCE'
                }), 409

            # معالجة أوقات الحضور والانصراف
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

            # التحقق من أن وقت الانصراف بعد وقت الحضور
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
            app.logger.error(f"Unexpected error in add_attendance (POST): {str(e)}")
            return jsonify({
                'success': False,
                'message': f'حدث خطأ غير متوقع: {str(e)}',
                'code': 'INTERNAL_ERROR'
            }), 500

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


def get_employees_for_attendance(user):
    """الحصول على قائمة الموظفين المسموح للمستخدم بتسجيل حضورهم"""

    if user.role == 'owner':
        # المالك: جميع الموظفين النشطين
        return Employee.query.filter_by(is_active=True).order_by(Employee.full_name).all()

    elif user.role == 'supervisor':
        # المشرف: جميع الموظفين النشطين
        return Employee.query.filter_by(is_active=True).order_by(Employee.full_name).all()

    elif user.role == 'monitor':
        # المراقب: العمال في موقعه فقط
        monitor_employee = Employee.query.filter_by(user_id=user.id).first()
        if not monitor_employee:
            return []

        # الحصول على المواقع التي يراقبها
        monitored_locations = Location.query.filter_by(monitor_id=monitor_employee.id).all()
        location_ids = [loc.id for loc in monitored_locations]

        if not location_ids:
            return []

        # الحصول على الأماكن في هذه المواقع
        places = Place.query.filter(Place.location_id.in_(location_ids)).all()

        # الحصول على العمال في هذه الأماكن
        worker_ids = [place.worker_id for place in places if place.worker_id]
        if worker_ids:
            workers = Employee.query.filter(
                Employee.id.in_(worker_ids),
                Employee.is_active == True
            ).order_by(Employee.full_name).all()
            return workers

        return []

    return []
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
        company = Company.query.get_or_404(company_id)

        # التحقق من الصلاحيات
        if current_user.role != 'owner' and not (
                current_user.role == 'supervisor' and
                current_user.employee_profile and
                any(area.supervisor_id == current_user.employee_profile.id for area in company.areas)
        ):
            flash('غير مصرح بالوصول إلى هذه الصفحة', 'error')
            return redirect(url_for('companies_list'))

        areas = Area.query.filter_by(company_id=company_id).order_by(Area.name).all()

        # الموظفون الذين يمكن تعيينهم كمشرفين
        available_supervisors = Employee.query.filter_by(
            position='supervisor',
            is_active=True
        ).all()

        return render_template('companies/areas.html',
                               company=company,
                               areas=areas,
                               available_supervisors=available_supervisors)

    except Exception as e:
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
    """إضافة موقع جديد - الإصدار المصحح"""
    print(f"🎯 تم استدعاء add_location للمنطقة {area_id} بطريقة {request.method}")

    if request.method == 'GET':
        # للتصحيح فقط
        return jsonify({
            'debug': True,
            'message': 'هذا مسار GET للتصحيح',
            'area_id': area_id,
            'endpoint': 'add_location'
        })

    # معالجة طلب POST
    try:
        print(f"📨 بيانات POST المستلمة: {dict(request.form)}")

        # التحقق من وجود المنطقة
        area = Area.query.get_or_404(area_id)
        print(f"✅ المنطقة: {area.name} (ID: {area.id})")

        # التحقق من الصلاحيات
        if current_user.role != 'owner' and not (
                current_user.role == 'supervisor' and
                current_user.employee_profile and
                area.supervisor_id == current_user.employee_profile.id
        ):
            print(f"❌ صلاحيات غير كافية: المستخدم {current_user.username} لديه دور {current_user.role}")
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
            print("❌ اسم الموقع مفقود")
            return jsonify({
                'success': False,
                'message': 'اسم الموقع مطلوب'
            }), 400

        # التحقق من طول الاسم
        if len(name) < 2:
            return jsonify({
                'success': False,
                'message': 'اسم الموقع يجب أن يكون على الأقل حرفين'
            }), 400

        # التحقق من عدم التكرار
        existing_location = Location.query.filter(
            db.func.lower(Location.name) == db.func.lower(name),
            Location.area_id == area_id,
            Location.is_active == True
        ).first()

        if existing_location:
            print(f"❌ الموقع موجود مسبقاً: {name}")
            return jsonify({
                'success': False,
                'message': f'اسم الموقع "{name}" موجود مسبقاً في هذه المنطقة'
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
            'location_id': location.id,
            'location_name': location.name
        })

    except Exception as e:
        db.session.rollback()
        print(f"❌ خطأ في إضافة الموقع: {str(e)}")
        import traceback
        print(f"🔍 تفاصيل الخطأ: {traceback.format_exc()}")

        return jsonify({
            'success': False,
            'message': f'حدث خطأ أثناء إضافة الموقع: {str(e)}'
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
    """إضافة مكان جديد - الإصدار المصحح"""
    print(f"🎯 تم استدعاء add_place للموقع {location_id} بطريقة {request.method}")

    if request.method == 'GET':
        # للتصحيح فقط
        return jsonify({
            'debug': True,
            'message': 'هذا مسار GET للتصحيح',
            'location_id': location_id,
            'endpoint': 'add_place'
        })

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
# دوال التعديل والحذف للمناطق
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

        name = request.form['name'].strip()
        supervisor_id = request.form.get('supervisor_id')

        # التحقق من البيانات
        if not name:
            return jsonify({
                'success': False,
                'message': 'اسم المنطقة مطلوب'
            }), 400

        # تحديث المنطقة
        area.name = name
        area.supervisor_id = supervisor_id if supervisor_id else None
        area.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'تم تحديث المنطقة بنجاح'
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
        has_locations = Location.query.filter_by(area_id=area_id).first()
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
    """عرض قائمة التقييمات مع الصلاحيات المحدثة"""
    try:
        from sqlalchemy.orm import joinedload

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

        elif current_user.role == 'supervisor':
            # المشرف: يرى تقييمات مراقبيه وعماله فقط
            if current_user.employee_profile:
                # الحصول على المناطق التي يشرف عليها
                supervised_areas = Area.query.filter_by(supervisor_id=current_user.employee_profile.id).all()
                area_ids = [area.id for area in supervised_areas]

                # الحصول على المواقع في هذه المناطق
                locations = Location.query.filter(Location.area_id.in_(area_ids)).all()
                location_ids = [loc.id for loc in locations]

                # الحصول على الأماكن في هذه المواقع
                places = Place.query.filter(Place.location_id.in_(location_ids)).all()
                place_ids = [place.id for place in places]

                evaluations_list = base_query.filter(
                    CleaningEvaluation.place_id.in_(place_ids)
                ).order_by(CleaningEvaluation.date.desc()).all()
            else:
                evaluations_list = []

        elif current_user.role == 'monitor':
            # المراقب: يرى تقييمات عماله فقط
            if current_user.employee_profile:
                # الحصول على المواقع التي يراقبها
                monitored_locations = Location.query.filter_by(monitor_id=current_user.employee_profile.id).all()
                location_ids = [loc.id for loc in monitored_locations]

                # الحصول على الأماكن في هذه المواقع
                places = Place.query.filter(Place.location_id.in_(location_ids)).all()
                place_ids = [place.id for place in places]

                evaluations_list = base_query.filter(
                    CleaningEvaluation.place_id.in_(place_ids)
                ).order_by(CleaningEvaluation.date.desc()).all()
            else:
                evaluations_list = []

        else:
            # العامل: يرى تقييماته فقط
            if current_user.employee_profile:
                evaluations_list = base_query.filter(
                    CleaningEvaluation.evaluated_employee_id == current_user.employee_profile.id
                ).order_by(CleaningEvaluation.date.desc()).all()
            else:
                evaluations_list = []

        return render_template('evaluations/list.html',
                               evaluations=evaluations_list,
                               today=date.today())

    except Exception as e:
        app.logger.error(f"Error in evaluations_list: {str(e)}")
        flash('حدث خطأ في تحميل قائمة التقييمات', 'error')
        return render_template('evaluations/list.html', evaluations=[])


@app.route('/evaluations/add', methods=['GET', 'POST'])
@login_required
def add_evaluation():
    """إضافة تقييم جديد مع نظام الصلاحيات المحدث"""

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
            safety_measures = request.form.get('safety_measures', '')
            comments = request.form.get('comments', '')

            print(f"📨 بيانات التقييم المستلمة:")
            print(f"   - التاريخ: {date_str}")
            print(f"   - المكان: {place_id}")
            print(f"   - الموظف المقيّم: {evaluated_employee_id}")
            print(f"   - النقاط: {cleanliness}, {organization}, {equipment_condition}, {safety_measures}")

            # التحقق من البيانات المطلوبة
            if not all([date_str, place_id, evaluated_employee_id, cleanliness, organization, equipment_condition,
                        safety_measures]):
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
                # للمالك: استخدام أول مشرف نشط كمقيم افتراضي
                supervisor = Employee.query.filter_by(position='supervisor', is_active=True).first()
                if supervisor:
                    evaluator_id = supervisor.id
                    print(f"👑 المالك يستخدم المشرف: {supervisor.full_name}")
                else:
                    flash('لا يوجد مشرفين في النظام', 'error')
                    return redirect(url_for('add_evaluation'))
            else:
                # للمشرفين والمراقبين: استخدام حسابهم كمقيم
                employee_profile = Employee.query.filter_by(user_id=current_user.id).first()
                if employee_profile:
                    evaluator_id = employee_profile.id
                    print(f"👤 المستخدم يستخدم حسابه: {employee_profile.full_name}")
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

            # إنشاء التقييم
            evaluation = CleaningEvaluation(
                date=evaluation_date,
                place_id=place_id,
                evaluated_employee_id=evaluated_employee_id,
                evaluator_id=evaluator_id,
                cleanliness=int(cleanliness),
                organization=int(organization),
                equipment_condition=int(equipment_condition),
                safety_measures=int(safety_measures),
                overall_score=0.0,
                comments=comments or None
            )

            # حساب النتيجة الإجمالية تلقائياً
            evaluation.calculate_overall_score()

            db.session.add(evaluation)
            db.session.commit()

            flash('تم إضافة التقييم بنجاح!', 'success')
            return redirect(url_for('evaluations_list'))

        except ValueError as e:
            db.session.rollback()
            flash('قيم التقييم غير صحيحة، يرجى التأكد من إدخال أرقام صحيحة', 'error')
            return redirect(url_for('add_evaluation'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'error')
            return redirect(url_for('add_evaluation'))

    # GET Request - عرض النموذج
    try:
        # الحصول على البيانات المطلوبة للقوائم المنسدلة
        companies = Company.query.filter_by(is_active=True).order_by(Company.name).all()

        # الحصول على الموظفين المسموح بتقييمهم حسب الصلاحيات
        employees_for_evaluation = get_employees_for_evaluation(current_user)

        return render_template('evaluations/add.html',
                               today=date.today(),
                               companies=companies,
                               employees=employees_for_evaluation,
                               current_user=current_user)

    except Exception as e:
        flash(f'خطأ في تحميل النموذج: {str(e)}', 'error')
        return redirect(url_for('evaluations_list'))


def can_evaluate_employee(evaluator_user, evaluated_employee, place):
    """التحقق من صلاحية المستخدم في تقييم موظف معين"""

    if evaluator_user.role == 'owner':
        # المالك: يقيّم جميع الموظفين
        return True

    elif evaluator_user.role == 'supervisor':
        # المشرف: يقيّم المراقبين والعمال في مناطق إشرافه

        # الحصول على ملف المشرف
        supervisor_employee = Employee.query.filter_by(user_id=evaluator_user.id).first()
        if not supervisor_employee:
            return False

        # التحقق من أن المكان يقع في منطقة يشرف عليها
        if place.location.area.supervisor_id == supervisor_employee.id:
            # يمكنه تقييم المراقبين والعمال في منطقته
            return evaluated_employee.position in ['monitor', 'worker']
        return False

    elif evaluator_user.role == 'monitor':
        # المراقب: يقيّم العمال في موقعه فقط

        # الحصول على ملف المراقب
        monitor_employee = Employee.query.filter_by(user_id=evaluator_user.id).first()
        if not monitor_employee:
            return False

        # التحقق من أن المكان يقع في موقع يراقبه
        if place.location.monitor_id == monitor_employee.id:
            # يمكنه تقييم العمال فقط
            return evaluated_employee.position == 'worker'
        return False

    return False


def get_employees_for_evaluation(user):
    """الحصول على قائمة الموظفين المسموح للمستخدم بتقييمهم"""

    if user.role == 'owner':
        # المالك: جميع الموظفين النشطين
        return Employee.query.filter_by(is_active=True).order_by(Employee.full_name).all()

    elif user.role == 'supervisor':
        # المشرف: المراقبون والعمال في مناطق إشرافه

        # الحصول على ملف المشرف
        supervisor_employee = Employee.query.filter_by(user_id=user.id).first()
        if not supervisor_employee:
            return []

        # الحصول على المناطق التي يشرف عليها
        supervised_areas = Area.query.filter_by(supervisor_id=supervisor_employee.id).all()
        area_ids = [area.id for area in supervised_areas]

        if not area_ids:
            return []

        # الحصول على المواقع في هذه المناطق
        locations = Location.query.filter(Location.area_id.in_(area_ids)).all()
        location_ids = [loc.id for loc in locations]

        # الحصول على الأماكن في هذه المواقع
        places = Place.query.filter(Place.location_id.in_(location_ids)).all()

        # الحصول على جميع المراقبين والعمال في هذه الهيكل
        employees = []

        # المراقبون في المواقع التابعة
        monitor_ids = [loc.monitor_id for loc in locations if loc.monitor_id]
        if monitor_ids:
            monitors = Employee.query.filter(
                Employee.id.in_(monitor_ids),
                Employee.is_active == True
            ).all()
            employees.extend(monitors)

        # العمال في الأماكن التابعة
        worker_ids = [place.worker_id for place in places if place.worker_id]
        if worker_ids:
            workers = Employee.query.filter(
                Employee.id.in_(worker_ids),
                Employee.is_active == True
            ).all()
            employees.extend(workers)

        return list(set(employees))  # إزالة التكرارات

    elif user.role == 'monitor':
        # المراقب: العمال في موقعه فقط

        # الحصول على ملف المراقب
        monitor_employee = Employee.query.filter_by(user_id=user.id).first()
        if not monitor_employee:
            return []

        # الحصول على المواقع التي يراقبها
        monitored_locations = Location.query.filter_by(monitor_id=monitor_employee.id).all()
        location_ids = [loc.id for loc in monitored_locations]

        if not location_ids:
            return []

        places = Place.query.filter(Place.location_id.in_(location_ids)).all()

        worker_ids = [place.worker_id for place in places if place.worker_id]
        if worker_ids:
            workers = Employee.query.filter(
                Employee.id.in_(worker_ids),
                Employee.is_active == True
            ).all()
            return workers

        return []

    return []

# API للحصول على الموظفين المسموح بتقييمهم
@app.route('/api/employees/evaluatable')
@login_required
def get_evaluatable_employees():
    """API للحصول على الموظفين المسموح للمستخدم الحالي بتقييمهم"""
    try:
        employees = get_employees_for_evaluation(current_user)

        employees_data = [{
            'id': emp.id,
            'full_name': emp.full_name,
            'position': emp.position,
            'position_ar': 'مشرف' if emp.position == 'supervisor' else 'مراقب' if emp.position == 'monitor' else 'عامل'
        } for emp in employees]

        return jsonify({
            'success': True,
            'data': employees_data,
            'count': len(employees_data)
        })

    except Exception as e:
        app.logger.error(f"Error in get_evaluatable_employees: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ في تحميل بيانات الموظفين',
            'data': [],
            'count': 0
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
    # Basic stats for reports page
    total_employees = Employee.query.count()
    total_companies = Company.query.filter_by(is_active=True).count()
    total_evaluations = CleaningEvaluation.query.count()
    avg_score = db.session.query(db.func.avg(CleaningEvaluation.overall_score)).scalar() or 0

    stats = {
        'total_employees': total_employees,
        'total_companies': total_companies,
        'total_evaluations': total_evaluations,
        'avg_score': avg_score
    }

    return render_template('reports/index.html', today=date.today(), stats=stats)


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
if __name__ == '__main__':
    # Initialize database on startup
    initialize_database()
    print("🚀 بدء تشغيل تطبيق أرض الجوهرة للنظافة...")
    print("📊 يمكنك الوصول للتطبيق على: http://localhost:5000")
    print("👤 اسم المستخدم: owner")
    print("🔑 كلمة المرور: admin123")
    app.run(debug=True)
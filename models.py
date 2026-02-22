import os
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash


# دعم SQLite للتنمية المحلية وPostgreSQL للإنتاج
def get_database_url():
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        return database_url.replace('postgres://', 'postgresql://')
    return 'sqlite:///cleaning_company.db'


db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'clean_users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # owner, supervisor, monitor, worker, admin
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ✅ حقول الصلاحيات - أضف هذه الأسطر
    # تقارير الموظفين
    can_view_employees = db.Column(db.Boolean, default=True)
    can_edit_employees = db.Column(db.Boolean, default=False)
    can_add_employees = db.Column(db.Boolean, default=False)
    can_delete_employees = db.Column(db.Boolean, default=False)

    # تقارير الحضور
    can_view_attendance = db.Column(db.Boolean, default=True)
    can_record_attendance = db.Column(db.Boolean, default=True)
    can_view_attendance_reports = db.Column(db.Boolean, default=True)
    can_view_overtime = db.Column(db.Boolean, default=False)
    can_view_absence_rates = db.Column(db.Boolean, default=False)

    # تقارير التقييمات
    can_view_evaluations = db.Column(db.Boolean, default=True)
    can_add_evaluations = db.Column(db.Boolean, default=True)
    can_view_evaluation_reports = db.Column(db.Boolean, default=False)
    can_view_detailed_evaluations = db.Column(db.Boolean, default=False)

    # تقارير الأداء
    can_view_performance = db.Column(db.Boolean, default=False)
    can_view_top_employees = db.Column(db.Boolean, default=False)
    can_view_employee_efficiency = db.Column(db.Boolean, default=False)

    # تقارير الشركات والمناطق
    can_view_companies = db.Column(db.Boolean, default=True)
    can_view_company_stats = db.Column(db.Boolean, default=False)
    can_view_zones = db.Column(db.Boolean, default=False)

    # تقارير مالية
    can_view_salaries = db.Column(db.Boolean, default=False)
    can_view_salary_reports = db.Column(db.Boolean, default=False)
    can_view_financial = db.Column(db.Boolean, default=False)
    can_view_invoices = db.Column(db.Boolean, default=False)
    can_view_penalties = db.Column(db.Boolean, default=False)

    # لوحة التحكم
    can_view_dashboard = db.Column(db.Boolean, default=True)
    can_view_kpis = db.Column(db.Boolean, default=False)
    can_view_heatmap = db.Column(db.Boolean, default=False)

    # إعدادات النظام
    can_manage_users = db.Column(db.Boolean, default=False)
    can_manage_roles = db.Column(db.Boolean, default=False)

    # العلاقة مع Employee
    employee_profile = db.relationship('Employee', backref='user', uselist=False, foreign_keys='Employee.user_id')

    def set_password(self, password):
        """تعيين كلمة المرور للمستخدم"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """التحقق من كلمة المرور"""
        return check_password_hash(self.password_hash, password)

    def has_permission(self, permission_name):
        """التحقق من صلاحية معينة"""
        if self.role == 'owner':
            return True  # المالك له جميع الصلاحيات
        return getattr(self, permission_name, False)

    def __repr__(self):
        return f'<User {self.username}>'

class Employee(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)

    # ✅ الرقم التسلسلي للموظف (يبدأ من 1001) - باسم code
    code = db.Column(db.String(20), unique=True, nullable=True)

    # ✅ المؤهل العلمي
    qualification = db.Column(db.String(100), nullable=True)

    # ✅ التخصص (للمشرفين والإداريين)
    specialization = db.Column(db.String(100), nullable=True)

    # ✅ user_id أصبح اختيارياً (nullable=True) لأن فقط المشرفين لديهم حسابات
    user_id = db.Column(db.Integer, db.ForeignKey('clean_users.id'), unique=True, nullable=True)

    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    position = db.Column(db.String(20), nullable=False)  # supervisor, monitor, worker, admin
    salary = db.Column(db.Float, default=0.0)
    hire_date = db.Column(db.Date, nullable=False)

    # ✅ الحقول الجديدة المطلوبة
    company_id = db.Column(db.Integer, db.ForeignKey('clean_companies.id'), nullable=True)  # الشركة التي يعمل بها
    supervisor_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)  # المشرف المباشر

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ✅ العلاقات الجديدة
    company = db.relationship('Company', backref='employees', foreign_keys=[company_id])
    supervisor = db.relationship('Employee', remote_side=[id], backref='subordinates', foreign_keys=[supervisor_id])

    # العلاقات القديمة
    supervised_areas = db.relationship('Area', backref='supervisor', foreign_keys='Area.supervisor_id')
    monitored_locations = db.relationship('Location', backref='monitor', foreign_keys='Location.monitor_id')
    assigned_places = db.relationship('Place', backref='worker', foreign_keys='Place.worker_id')

    def __repr__(self):
        emp_code = f' [{self.code}]' if self.code else ''
        return f'<Employee {self.full_name}{emp_code}>'

    @staticmethod
    def generate_code():
        """توليد رقم تسلسلي للموظف يبدأ من 1001"""
        try:
            last_employee = Employee.query.filter(Employee.code.isnot(None)) \
                .order_by(Employee.code.desc()) \
                .first()

            if last_employee and last_employee.code:
                try:
                    last_number = int(last_employee.code)
                    return str(last_number + 1)
                except ValueError:
                    return "1001"
            else:
                return "1001"
        except Exception as e:
            print(f"خطأ في توليد كود الموظف: {e}")
            return "1001"

class Company(db.Model):
    __tablename__ = 'clean_companies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    address = db.Column(db.Text)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    areas = db.relationship('Area', backref='company', lazy=True)

    def __repr__(self):
        return f'<Company {self.name}>'


class Area(db.Model):
    __tablename__ = 'areas'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('clean_companies.id'), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    locations = db.relationship('Location', backref='area', lazy=True)

    def __repr__(self):
        return f'<Area {self.name}>'


class Location(db.Model):
    __tablename__ = 'clean_locations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey('areas.id'), nullable=False)
    monitor_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    places = db.relationship('Place', backref='location', lazy=True)

    def __repr__(self):
        return f'<Location {self.name}>'


class Place(db.Model):
    __tablename__ = 'clean_places'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('clean_locations.id'), nullable=False)
    worker_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    evaluations = db.relationship('CleaningEvaluation', backref='place', lazy=True)

    def __repr__(self):
        return f'<Place {self.name}>'


class CleaningEvaluation(db.Model):
    __tablename__ = 'cleaning_evaluations'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    place_id = db.Column(db.Integer, db.ForeignKey('clean_places.id'), nullable=False)
    evaluated_employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)

    # حقول التقييم (5 معايير)
    cleanliness = db.Column(db.Integer, nullable=False)  # النظافة
    organization = db.Column(db.Integer, nullable=False)  # التنظيم
    equipment_condition = db.Column(db.Integer, nullable=False)  # حالة المعدات
    time = db.Column(db.Integer, nullable=False, default=3)  # الالتزام بوقت الدوام (جديد)
    safety_measures = db.Column(db.Integer, nullable=False)  # إجراءات السلامة

    # النتيجة الإجمالية
    overall_score = db.Column(db.Float, nullable=False, default=0.0)

    # ملاحظات
    comments = db.Column(db.Text)

    # الطوابع الزمنية
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    evaluated_employee = db.relationship('Employee', foreign_keys=[evaluated_employee_id],
                                         backref='evaluations_received')
    evaluator = db.relationship('Employee', foreign_keys=[evaluator_id], backref='evaluations_given')

    def calculate_overall_score(self):
        """حساب النتيجة الإجمالية للتقييم (معدل المعايير الخمسة)"""
        total = (self.cleanliness + self.organization + self.equipment_condition +
                 self.time + self.safety_measures)
        self.overall_score = total / 5  # متوسط مباشر من 5
        return self.overall_score

    def __repr__(self):
        return f'<CleaningEvaluation {self.id} - {self.date}>'


class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    shift_type = db.Column(db.String(20), nullable=False, default='morning')

    status = db.Column(db.String(20), nullable=False)  # present, absent, late
    check_in = db.Column(db.Time)
    check_out = db.Column(db.Time)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    employee = db.relationship('Employee', backref='attendance_records')

    def __repr__(self):
        return f'<Attendance {self.employee_id} - {self.date}>'


class SupervisorEvaluation(db.Model):
    """نموذج تقييم المشرفين"""
    __tablename__ = 'supervisor_evaluations'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)

    # العلاقات
    supervisor_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('clean_companies.id'), nullable=False)

    # حقول التقييم الجديدة للمشرف
    # 1. متابعة العمال
    workers_followup = db.Column(db.Integer, nullable=False)  # 1-5
    workers_followup_notes = db.Column(db.Text)

    # 2. الكفاءة في العمل
    work_efficiency = db.Column(db.Integer, nullable=False)  # 1-5
    efficiency_notes = db.Column(db.Text)

    # 3. الرفع بالتقارير
    reports_submission = db.Column(db.Integer, nullable=False)  # 1-5
    reports_notes = db.Column(db.Text)

    # 4. الالتزام بالسياسات
    policies_compliance = db.Column(db.Integer, nullable=False)  # 1-5
    policies_notes = db.Column(db.Text)

    # 5. إجراءات السلامة
    safety_procedures = db.Column(db.Integer, nullable=False)  # 1-5
    safety_notes = db.Column(db.Text)

    # 6. الالتزام بوقت العمل
    attendance_commitment = db.Column(db.Integer, nullable=False)  # 1-5
    attendance_notes = db.Column(db.Text)

    # 7. مهارات القيادة
    leadership_skills = db.Column(db.Integer, nullable=False)  # 1-5
    leadership_notes = db.Column(db.Text)

    # 8. حل المشكلات
    problem_solving = db.Column(db.Integer, nullable=False)  # 1-5
    problem_solving_notes = db.Column(db.Text)

    # النتيجة الإجمالية (تحسب تلقائياً)
    overall_score = db.Column(db.Float, default=0.0)

    # ملاحظات عامة
    general_comments = db.Column(db.Text)

    # تتبع الوقت
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    supervisor = db.relationship('Employee', foreign_keys=[supervisor_id], backref='supervisor_evaluations_received')
    evaluator = db.relationship('Employee', foreign_keys=[evaluator_id], backref='supervisor_evaluations_given')
    company = db.relationship('Company', backref='supervisor_evaluations')

    def calculate_overall_score(self):
        """حساب النتيجة الإجمالية للتقييم (معدل المعايير الثمانية)"""
        try:
            # قائمة المعايير مع التحقق من وجود قيم
            scores = []

            # متابعة العمال
            if self.workers_followup is not None:
                scores.append(self.workers_followup)

            # الكفاءة في العمل
            if self.work_efficiency is not None:
                scores.append(self.work_efficiency)

            # الرفع بالتقارير
            if self.reports_submission is not None:
                scores.append(self.reports_submission)

            # الالتزام بالسياسات
            if self.policies_compliance is not None:
                scores.append(self.policies_compliance)

            # إجراءات السلامة
            if self.safety_procedures is not None:
                scores.append(self.safety_procedures)

            # الالتزام بوقت العمل
            if self.attendance_commitment is not None:
                scores.append(self.attendance_commitment)

            # مهارات القيادة
            if self.leadership_skills is not None:
                scores.append(self.leadership_skills)

            # حل المشكلات
            if self.problem_solving is not None:
                scores.append(self.problem_solving)

            # إذا كانت القائمة فارغة، استخدم قيمة افتراضية
            if not scores:
                self.overall_score = 3.0
            else:
                # حساب المتوسط
                self.overall_score = sum(scores) / len(scores)

            return self.overall_score

        except Exception as e:
            print(f"خطأ في حساب التقييم: {e}")
            self.overall_score = 3.0
            return self.overall_score

    def __repr__(self):
        return f'<SupervisorEvaluation {self.id}>'

# 🔧 دوال إنشاء البيانات
def create_tables():
    """إنشاء جميع الجداول"""
    try:
        print("🔧 جاري إنشاء الجداول...")
        db.create_all()

        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        print("✅ تم إنشاء الجداول بنجاح")
        print(f"📋 الجداول المنشأة: {tables}")
        return True

    except Exception as e:
        print(f"❌ خطأ في إنشاء الجداول: {e}")
        import traceback
        traceback.print_exc()
        return False


def initialize_default_data():
    """إنشاء البيانات الافتراضية"""
    try:
        print("📦 جاري إنشاء البيانات الافتراضية...")

        user_count = User.query.count()
        company_count = Company.query.count()

        if user_count == 0 and company_count == 0:
            print("🆕 لا توجد بيانات، جاري الإنشاء...")

            # إنشاء شركة افتراضية
            company = Company(
                name="شركة النظافة العامة",
                address="اليمن - صنعاء",
                contact_person="المدير العام",
                phone="+967123456789",
                email="info@cleaning.com",
                is_active=True
            )
            db.session.add(company)
            db.session.flush()

            # إنشاء مستخدم مالك
            owner_user = User(
                username="owner",
                email="owner@cleaning.com",
                role="owner",
                is_active=True
            )
            owner_user.set_password("admin123")
            db.session.add(owner_user)
            db.session.flush()

            # إنشاء موظف للمالك
            owner_employee = Employee(
                user_id=owner_user.id,
                full_name="المالك العام",
                position="owner",
                hire_date=date.today(),
                is_active=True
            )
            db.session.add(owner_employee)

            db.session.commit()
            print("✅ تم إنشاء البيانات الافتراضية بنجاح")
            print("   👤 مستخدم: owner / admin123")
            print("   🏢 شركة: شركة النظافة العامة")
        else:
            print(f"✅ توجد بيانات بالفعل: {user_count} مستخدم، {company_count} شركة")

        return True

    except Exception as e:
        db.session.rollback()
        print(f"❌ خطأ في إنشاء البيانات الافتراضية: {e}")
        import traceback
        traceback.print_exc()
        return False


__all__ = ['db', 'User', 'Employee', 'Company', 'Area', 'Location', 'Place', 'CleaningEvaluation', 'Attendance',
           'SupervisorEvaluation', 'create_tables', 'initialize_default_data']


class Payroll(db.Model):
    """نموذج كشوف المرتبات الشهرية - مستقل تماماً"""
    __tablename__ = 'payrolls'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)

    # الشهر والسنة
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)

    # ✅ بيانات الراتب الأساسية (تُحسب من بيانات الموظف وقت الإنشاء)
    base_salary = db.Column(db.Float, default=0.0)  # الراتب الشهري الأساسي (من الموظف)
    daily_rate = db.Column(db.Float, default=0.0)  # الأجر اليومي (محسوب)

    # ✅ بيانات الحضور
    working_days = db.Column(db.Integer, default=0)  # أيام العمل في الشهر
    present_days = db.Column(db.Integer, default=0)  # أيام الحضور الفعلية
    absent_days = db.Column(db.Integer, default=0)  # أيام الغياب
    late_days = db.Column(db.Integer, default=0)  # أيام التأخير
    overtime_hours = db.Column(db.Float, default=0)  # ساعات العمل الإضافية

    # ✅ الحسابات المالية
    base_pay = db.Column(db.Float, default=0.0)  # الراتب الأساسي للأيام الفعلية (daily_rate * present_days)
    overtime_rate = db.Column(db.Float, default=0.0)  # أجر الساعة الإضافية
    overtime_pay = db.Column(db.Float, default=0.0)  # أجر الساعات الإضافية (overtime_rate * overtime_hours)

    # ✅ البدلات (يمكن أن تكون مختلفة كل شهر)
    transportation_allowance = db.Column(db.Float, default=0.0)  # بدل مواصلات
    housing_allowance = db.Column(db.Float, default=0.0)  # بدل سكن
    food_allowance = db.Column(db.Float, default=0.0)  # بدل طعام
    other_allowances = db.Column(db.Float, default=0.0)  # بدلات أخرى

    # ✅ الخصومات
    deductions = db.Column(db.Float, default=0.0)  # خصومات عامة
    insurance_deduction = db.Column(db.Float, default=0.0)  # خصم التأمينات
    tax_deduction = db.Column(db.Float, default=0.0)  # خصم الضرائب
    loan_deduction = db.Column(db.Float, default=0.0)  # خصم سلف/قروض
    penalty_deduction = db.Column(db.Float, default=0.0)  # خصم جزاءات

    # ✅ الإجماليات
    total_allowances = db.Column(db.Float, default=0.0)
    total_deductions = db.Column(db.Float, default=0.0)
    net_salary = db.Column(db.Float, default=0.0)

    # ✅ معلومات الدفع
    status = db.Column(db.String(20), default='pending')  # pending, paid, cancelled
    payment_date = db.Column(db.Date, nullable=True)
    payment_method = db.Column(db.String(50))  # cash, bank_transfer, check
    payment_reference = db.Column(db.String(100))  # رقم التحويل/الشيك
    paid_by = db.Column(db.Integer, db.ForeignKey('clean_users.id'), nullable=True)  # المستخدم الذي قام بالدفع

    # ✅ ملاحظات
    notes = db.Column(db.Text)

    # ✅ الطوابع الزمنية
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ✅ العلاقات
    employee = db.relationship('Employee', backref=db.backref('payrolls', lazy='dynamic', cascade='all, delete-orphan'))
    payer = db.relationship('User', foreign_keys=[paid_by])

    def calculate_payroll(self):
        """حساب كشف المرتبات بالكامل مع التأكد من عدم وجود قيم None"""
        # تحويل جميع القيم إلى أرقام (التأكد من عدم وجود None)
        try:
            # 1. الراتب الأساسي للأيام الفعلية
            daily_rate = self.daily_rate or 0
            present_days = self.present_days or 0
            self.base_pay = round(daily_rate * present_days, 2)

            # 2. أجر الساعات الإضافية
            overtime_rate = self.overtime_rate or 0
            overtime_hours = self.overtime_hours or 0
            self.overtime_pay = round(overtime_rate * overtime_hours, 2)

            # 3. إجمالي البدلات (مع التأكد من عدم وجود None)
            transportation = self.transportation_allowance or 0
            housing = self.housing_allowance or 0
            food = self.food_allowance or 0
            other = self.other_allowances or 0
            self.total_allowances = round(
                transportation + housing + food + other, 2
            )

            # 4. إجمالي الخصومات (مع التأكد من عدم وجود None)
            deductions = self.deductions or 0
            insurance = self.insurance_deduction or 0
            tax = self.tax_deduction or 0
            loan = self.loan_deduction or 0
            penalty = self.penalty_deduction or 0
            self.total_deductions = round(
                deductions + insurance + tax + loan + penalty, 2
            )

            # 5. الراتب الصافي
            base_pay = self.base_pay or 0
            overtime_pay = self.overtime_pay or 0
            total_allowances = self.total_allowances or 0
            total_deductions = self.total_deductions or 0
            self.net_salary = round(
                base_pay + overtime_pay + total_allowances - total_deductions, 2
            )

            return self.net_salary

        except Exception as e:
            print(f"خطأ في حساب الراتب: {e}")
            # في حالة الخطأ، نعيد القيم الحالية
            return self.net_salary or 0

    def __repr__(self):
        month_names = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
                       'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
        month_name = month_names[self.month - 1] if 1 <= self.month <= 12 else str(self.month)
        return f'<Payroll {self.employee.full_name if self.employee else "موظف"} - {month_name} {self.year}>'


# ============================================
# ✅ جدول السلف والاقتراض (Employee Loans) - مصحح
# ============================================
class EmployeeLoan(db.Model):
    """نموذج السلف والاقتراض للموظفين"""
    __tablename__ = 'employee_loans'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)

    # تاريخ السلفة
    loan_date = db.Column(db.Date, nullable=False, default=date.today)

    # بيانات السلفة
    amount = db.Column(db.Float, nullable=False, default=0.0)  # إجمالي مبلغ السلفة
    installments = db.Column(db.Integer, nullable=False, default=1)  # عدد الأقساط
    monthly_installment = db.Column(db.Float, nullable=False, default=0.0)  # القسط الشهري (محسوب)
    paid_amount = db.Column(db.Float, nullable=False, default=0.0)  # المبلغ المسدد
    remaining = db.Column(db.Float, nullable=False, default=0.0)  # المبلغ المتبقي

    # تفاصيل إضافية
    reason = db.Column(db.String(200))  # سبب السلفة
    description = db.Column(db.Text)  # وصف تفصيلي

    # الحالة
    status = db.Column(db.String(20), default='active')  # active, paid, cancelled
    approved_by = db.Column(db.Integer, db.ForeignKey('clean_users.id'), nullable=True)  # من وافق على السلفة
    recorded_by = db.Column(db.Integer, db.ForeignKey('clean_users.id'), nullable=True)  # من سجل السلفة

    # الربط مع كشف الراتب
    is_deducted = db.Column(db.Boolean, default=False)  # هل تم خصم قسط هذا الشهر؟

    # الطوابع الزمنية
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات - ✅ تم التعديل هنا
    employee = db.relationship('Employee', backref=db.backref('loans', lazy='dynamic', cascade='all, delete-orphan'))
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_loans')
    recorder = db.relationship('User', foreign_keys=[recorded_by], backref='recorded_loans')

    # ✅ علاقة الأقساط - بدون backref
    loan_installments = db.relationship('LoanInstallment', back_populates='loan', lazy='dynamic',
                                        cascade='all, delete-orphan')

    def calculate_installment(self):
        """حساب القسط الشهري والمبلغ المتبقي"""
        if self.installments > 0:
            self.monthly_installment = round(self.amount / self.installments, 2)
        else:
            self.monthly_installment = self.amount

        self.remaining = self.amount - self.paid_amount

        # تحديث الحالة
        if self.remaining <= 0:
            self.status = 'paid'
        elif self.paid_amount > 0:
            self.status = 'active'
        else:
            self.status = 'active'

        return self.monthly_installment

    def pay_installment(self, amount=None):
        """تسديد قسط شهري"""
        if amount is None:
            amount = self.monthly_installment

        self.paid_amount += amount
        self.remaining = self.amount - self.paid_amount

        if self.remaining <= 0:
            self.status = 'paid'

        return self.remaining

    def __repr__(self):
        month_names = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
                       'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
        month_name = month_names[self.loan_date.month - 1] if 1 <= self.loan_date.month <= 12 else str(
            self.loan_date.month)
        return f'<EmployeeLoan {self.employee.full_name if self.employee else "موظف"} - {self.amount} - {month_name} {self.loan_date.year}>'


# ============================================
# ✅ جدول سجل أقساط السلف (Loan Installments History) - مصحح
# ============================================
class LoanInstallment(db.Model):
    """سجل أقساط السلف المدفوعة"""
    __tablename__ = 'loan_installments'

    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('employee_loans.id'), nullable=False)

    # تاريخ الدفع
    payment_date = db.Column(db.Date, nullable=False, default=date.today)

    # بيانات القسط
    amount = db.Column(db.Float, nullable=False, default=0.0)  # المبلغ المدفوع
    month = db.Column(db.Integer, nullable=False)  # الشهر
    year = db.Column(db.Integer, nullable=False)  # السنة

    # طريقة الدفع
    payment_method = db.Column(db.String(50), default='payroll')  # payroll, cash, bank_transfer
    payroll_id = db.Column(db.Integer, db.ForeignKey('payrolls.id'), nullable=True)  # إذا تم الخصم من الراتب

    # ملاحظات
    notes = db.Column(db.Text)

    # الطوابع الزمنية
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # العلاقات - ✅ تم التعديل هنا
    loan = db.relationship('EmployeeLoan', back_populates='loan_installments')
    payroll = db.relationship('Payroll', backref='loan_installments')

    def __repr__(self):
        month_names = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
                       'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
        month_name = month_names[self.month - 1] if 1 <= self.month <= 12 else str(self.month)
        return f'<LoanInstallment {self.amount} - {month_name} {self.year}>'


# ============================================
# ✅ جدول الساعات الإضافية (Overtime) - مصحح
# ============================================
class Overtime(db.Model):
    """نموذج الساعات الإضافية للموظفين"""
    __tablename__ = 'overtime'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)

    # تاريخ الساعات الإضافية
    overtime_date = db.Column(db.Date, nullable=False, default=date.today)

    # الشهر والسنة (للربط مع كشف الراتب)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)

    # بيانات الساعات الإضافية
    hours = db.Column(db.Float, nullable=False, default=0.0)  # عدد الساعات
    rate = db.Column(db.Float, nullable=False, default=25.0)  # أجر الساعة (افتراضي 25 ريال)
    cost = db.Column(db.Float, nullable=False, default=0.0)  # التكلفة الإجمالية (hours * rate)

    # تفاصيل إضافية
    reason = db.Column(db.String(200))  # سبب الساعات الإضافية
    notes = db.Column(db.Text)  # ملاحظات

    # حالة الساعات الإضافية
    is_transferred = db.Column(db.Boolean, default=False)  # هل تم ترحيلها إلى كشف الراتب؟
    transferred_to_payroll_id = db.Column(db.Integer, db.ForeignKey('payrolls.id'), nullable=True)  # كشف الراتب المرتبط

    # الطوابع الزمنية
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    employee = db.relationship('Employee', backref=db.backref('overtime_records', lazy='dynamic'))

    # ✅ تم التعديل هنا - استخدام اسم مختلف للعلاقة
    payroll = db.relationship('Payroll', backref=db.backref('overtime_entries', lazy='dynamic'))

    def calculate_cost(self):
        """حساب تكلفة الساعات الإضافية"""
        self.cost = round(self.hours * self.rate, 2)
        return self.cost

    def __repr__(self):
        return f'<Overtime {self.employee.full_name if self.employee else "موظف"} - {self.hours} ساعة - {self.overtime_date}>'
class PayrollSettings(db.Model):
    """إعدادات الرواتب العامة (اختياري)"""
    __tablename__ = 'payroll_settings'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('clean_companies.id'), nullable=True)

    # إعدادات عامة
    default_overtime_rate = db.Column(db.Float, default=25.0)  # أجر الساعة الإضافية الافتراضي
    insurance_percentage = db.Column(db.Float, default=0.0)  # نسبة التأمينات
    tax_percentage = db.Column(db.Float, default=0.0)  # نسبة الضرائب

    # تواريخ الدفع
    payroll_day = db.Column(db.Integer, default=1)  # يوم الدفع من الشهر

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = db.relationship('Company', backref='payroll_settings')


class PayrollItem(db.Model):
    """بنود إضافية في الراتب (بدلات أو خصومات متغيرة)"""
    __tablename__ = 'payroll_items'

    id = db.Column(db.Integer, primary_key=True)
    payroll_id = db.Column(db.Integer, db.ForeignKey('payrolls.id'), nullable=False)

    item_type = db.Column(db.String(20), nullable=False)  # allowance, deduction
    name = db.Column(db.String(100), nullable=False)  # اسم البند
    amount = db.Column(db.Float, default=0.0)  # المبلغ
    description = db.Column(db.Text)  # وصف

    payroll = db.relationship('Payroll', backref=db.backref('items', lazy='dynamic'))


class Penalty(db.Model):
    """نموذج الجزاءات والخصومات على الموظفين"""
    __tablename__ = 'penalties'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)

    # تاريخ الجزاء
    penalty_date = db.Column(db.Date, nullable=False, default=date.today)

    # الشهر والسنة (للربط مع كشف الراتب)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)

    # بيانات الجزاء
    amount = db.Column(db.Float, nullable=False, default=0.0)  # قيمة الجزاء
    reason = db.Column(db.String(200), nullable=False)  # سبب الجزاء

    # تفاصيل إضافية
    description = db.Column(db.Text)  # وصف تفصيلي
    recorded_by = db.Column(db.Integer, db.ForeignKey('clean_users.id'), nullable=True)  # المستخدم الذي سجل الجزاء

    # حالة الجزاء
    is_deducted = db.Column(db.Boolean, default=False)  # هل تم خصمه بالفعل من الراتب؟

    # الطوابع الزمنية
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    employee = db.relationship('Employee', backref=db.backref('penalties', lazy='dynamic'))
    recorder = db.relationship('User', foreign_keys=[recorded_by])

    def __repr__(self):
        return f'<Penalty {self.employee.full_name if self.employee else "موظف"} - {self.amount} - {self.penalty_date}>'


class CompanyInvoice(db.Model):
    """نموذج الفواتير الشهرية للشركات"""
    __tablename__ = 'company_invoices'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('clean_companies.id'), nullable=False)

    # الشهر والسنة
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)

    # مبالغ المستخلصات
    contract_amount = db.Column(db.Float, default=0.0)  # قيمة العقد الشهري
    additional_services = db.Column(db.Float, default=0.0)  # خدمات إضافية
    extra_work = db.Column(db.Float, default=0.0)  # أعمال إضافية
    materials_amount = db.Column(db.Float, default=0.0)  # قيمة المواد المستهلكة
    equipment_rent = db.Column(db.Float, default=0.0)  # تأجير معدات

    # خصومات على الشركة
    discount = db.Column(db.Float, default=0.0)  # خصم عام
    penalty_deduction = db.Column(db.Float, default=0.0)  # غرامات تأخير
    late_payment_penalty = db.Column(db.Float, default=0.0)  # غرامة تأخر السداد

    # الإجماليات
    total_amount = db.Column(db.Float, default=0.0)  # إجمالي المستحق
    paid_amount = db.Column(db.Float, default=0.0)  # المبلغ المدفوع
    remaining_amount = db.Column(db.Float, default=0.0)  # المبلغ المتبقي

    # حالة الفاتورة
    status = db.Column(db.String(20), default='pending')  # pending, paid, partial, overdue
    payment_date = db.Column(db.Date, nullable=True)
    payment_method = db.Column(db.String(50))  # cash, bank_transfer, check
    payment_reference = db.Column(db.String(100))

    # ملاحظات
    notes = db.Column(db.Text)

    # الطوابع الزمنية
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    company = db.relationship('Company', backref=db.backref('invoices', lazy='dynamic'))

    def calculate_totals(self):
        """حساب إجمالي الفاتورة"""
        self.total_amount = (
                self.contract_amount +
                self.additional_services +
                self.extra_work +
                self.materials_amount +
                self.equipment_rent -
                self.discount -
                self.penalty_deduction -
                self.late_payment_penalty
        )
        self.remaining_amount = self.total_amount - self.paid_amount

        # تحديث الحالة
        if self.paid_amount >= self.total_amount:
            self.status = 'paid'
        elif self.paid_amount > 0:
            self.status = 'partial'
        elif self.payment_date and self.payment_date < date.today():
            self.status = 'overdue'
        else:
            self.status = 'pending'

        return self.total_amount

    def __repr__(self):
        month_names = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
                       'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
        month_name = month_names[self.month - 1] if 1 <= self.month <= 12 else str(self.month)
        return f'<Invoice {self.company.name if self.company else "شركة"} - {month_name} {self.year}>'


class OtherIncome(db.Model):
    """نموذج الإيرادات الأخرى"""
    __tablename__ = 'other_income'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('clean_companies.id'), nullable=True)

    # التاريخ
    income_date = db.Column(db.Date, nullable=False, default=date.today)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)

    # نوع الإيراد
    income_type = db.Column(db.String(50), nullable=False)  # service, project, material, equipment, other
    income_type_ar = db.Column(db.String(100))  # الاسم بالعربية

    # التفاصيل المالية
    amount = db.Column(db.Float, nullable=False, default=0.0)
    description = db.Column(db.Text)
    reference = db.Column(db.String(100))  # مرجع الفاتورة/العقد

    # حالة الإيراد
    is_recurring = db.Column(db.Boolean, default=False)  # هل هو إيراد متكرر
    recurring_period = db.Column(db.String(20))  # monthly, quarterly, yearly

    # الطوابع الزمنية
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    company = db.relationship('Company', backref=db.backref('other_incomes', lazy='dynamic'))

    def __repr__(self):
        return f'<OtherIncome {self.income_type_ar or self.income_type} - {self.amount}>'


class MonthlyFinancialSummary(db.Model):
    """نموذج الملخص المالي الشهري (للتحليل السريع)"""
    __tablename__ = 'monthly_financial_summary'

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('clean_companies.id'), nullable=True)  # ✅ إضافة company_id

    # الإيرادات
    total_invoiced = db.Column(db.Float, default=0.0)  # إجمالي الفواتير
    total_collected = db.Column(db.Float, default=0.0)  # إجمالي المحصل
    other_income = db.Column(db.Float, default=0.0)  # إيرادات أخرى
    total_revenue = db.Column(db.Float, default=0.0)  # إجمالي الإيرادات

    # المصروفات
    total_base_salaries = db.Column(db.Float, default=0.0)  # إجمالي الرواتب الأساسية
    total_overtime = db.Column(db.Float, default=0.0)  # إجمالي الساعات الإضافية
    total_penalties = db.Column(db.Float, default=0.0)  # إجمالي الجزاءات
    total_loan_deductions = db.Column(db.Float, default=0.0)  # إجمالي خصومات السلف
    net_salaries = db.Column(db.Float, default=0.0)  # صافي الرواتب بعد الجزاءات

    operating_expenses = db.Column(db.Float, default=0.0)  # مصروفات تشغيلية
    total_expenses = db.Column(db.Float, default=0.0)  # إجمالي المصروفات

    # الأرباح
    gross_profit = db.Column(db.Float, default=0.0)  # إجمالي الربح
    net_profit = db.Column(db.Float, default=0.0)  # صافي الربح
    profit_margin = db.Column(db.Float, default=0.0)  # هامش الربح (%)

    # مؤشرات الأداء
    employee_count = db.Column(db.Integer, default=0)
    avg_salary = db.Column(db.Float, default=0.0)
    revenue_per_employee = db.Column(db.Float, default=0.0)

    # الطوابع الزمنية
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    company = db.relationship('Company', backref='monthly_summaries')

    def calculate(self):
        """حساب جميع المؤشرات"""
        # صافي الرواتب بعد الجزاءات
        self.net_salaries = self.total_base_salaries + self.total_overtime - self.total_penalties - self.total_loan_deductions

        # إجمالي الإيرادات
        self.total_revenue = self.total_collected + self.other_income

        # إجمالي المصروفات
        self.total_expenses = self.net_salaries + self.operating_expenses

        # الأرباح
        self.gross_profit = self.total_revenue - self.net_salaries
        self.net_profit = self.total_revenue - self.total_expenses

        # هامش الربح
        if self.total_revenue > 0:
            self.profit_margin = round((self.net_profit / self.total_revenue) * 100, 2)

        # متوسط الراتب والإيراد لكل موظف
        if self.employee_count > 0:
            self.avg_salary = round(self.total_base_salaries / self.employee_count, 2)
            self.revenue_per_employee = round(self.total_revenue / self.employee_count, 2)

        return self.net_profit

    def __repr__(self):
        month_names = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
                       'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
        month_name = month_names[self.month - 1] if 1 <= self.month <= 12 else str(self.month)
        company_name = f" - {self.company.name}" if self.company else " - إيرادات عامة"
        return f'<FinancialSummary {month_name} {self.year}{company_name}>'

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
    role = db.Column(db.String(20), nullable=False)  # owner, supervisor, monitor, worker
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقة مع Employee
    employee_profile = db.relationship('Employee', backref='user', uselist=False, foreign_keys='Employee.user_id')

    def set_password(self, password):
        """تعيين كلمة المرور للمستخدم"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """التحقق من كلمة المرور"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Employee(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    # ✅ user_id أصبح اختيارياً (nullable=True) لأن فقط المشرفين لديهم حسابات
    user_id = db.Column(db.Integer, db.ForeignKey('clean_users.id'), unique=True, nullable=True)

    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    position = db.Column(db.String(20), nullable=False)  # supervisor, monitor, worker
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
        return f'<Employee {self.full_name}>'


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
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
    __tablename__ = 'clean_users'  # ⬅️ غير من users إلى clean_users

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
    __tablename__ = 'employees'  # ⬅️ هذا جدول جديد، لا يحتاج تغيير

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('clean_users.id'), unique=True, nullable=False)  # ⬅️ عدل المرجع
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    position = db.Column(db.String(20), nullable=False)  # supervisor, monitor, worker
    salary = db.Column(db.Float, default=0.0)
    hire_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    supervised_areas = db.relationship('Area', backref='supervisor', foreign_keys='[Area.supervisor_id]')
    monitored_locations = db.relationship('Location', backref='monitor', foreign_keys='Location.monitor_id')
    assigned_places = db.relationship('Place', backref='worker', foreign_keys='Place.worker_id')

    def __repr__(self):
        return f'<Employee {self.full_name}>'


class Company(db.Model):
    __tablename__ = 'clean_companies'  # ⬅️ غير من companies إلى clean_companies

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
    __tablename__ = 'areas'  # ⬅️ هذا جدول جديد، لا يحتاج تغيير

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('clean_companies.id'), nullable=False)  # ⬅️ عدل المرجع
    supervisor_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    locations = db.relationship('Location', backref='area', lazy=True)

    def __repr__(self):
        return f'<Area {self.name}>'


class Location(db.Model):
    __tablename__ = 'clean_locations'  # ⬅️ غير من locations إلى clean_locations

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
    __tablename__ = 'clean_places'  # ⬅️ غير من places إلى clean_places

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('clean_locations.id'), nullable=False)  # ⬅️ عدل المرجع
    worker_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    evaluations = db.relationship('CleaningEvaluation', backref='place', lazy=True)

    def __repr__(self):
        return f'<Place {self.name}>'


class CleaningEvaluation(db.Model):
    __tablename__ = 'cleaning_evaluations'  # ⬅️ هذا جدول جديد، لا يحتاج تغيير

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    place_id = db.Column(db.Integer, db.ForeignKey('clean_places.id'), nullable=False)  # ⬅️ عدل المرجع
    evaluated_employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)

    # حقول التقييم
    cleanliness = db.Column(db.Integer, nullable=False)
    organization = db.Column(db.Integer, nullable=False)
    equipment_condition = db.Column(db.Integer, nullable=False)
    safety_measures = db.Column(db.Integer, nullable=False)
    overall_score = db.Column(db.Float, nullable=False)
    comments = db.Column(db.Text)

    # الطوابع الزمنية
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    evaluated_employee = db.relationship('Employee', foreign_keys=[evaluated_employee_id],
                                         backref='evaluations_received')
    evaluator = db.relationship('Employee', foreign_keys=[evaluator_id], backref='evaluations_given')

    def calculate_overall_score(self):
        """حساب النتيجة الإجمالية للتقييم"""
        total = self.cleanliness + self.organization + self.equipment_condition + self.safety_measures
        self.overall_score = (total / 20) * 5  # تحويل إلى مقياس 5 نقاط

    def __repr__(self):
        return f'<CleaningEvaluation {self.id} - {self.date}>'


class Attendance(db.Model):
    __tablename__ = 'attendance'  # ⬅️ هذا جدول جديد، لا يحتاج تغيير

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


# 🔧 أضف هذه الدوال في نهاية models.py - قبل السطر الأخير

def create_tables():
    """إنشاء جميع الجداول"""
    try:
        print("🔧 جاري إنشاء الجداول...")
        db.create_all()

        # التحقق من الجداول المنشأة
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

        # التحقق إذا كانت هناك بيانات موجودة
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
            db.session.flush()  # للحصول على ID

            # إنشاء مستخدم مالك
            owner_user = User(
                username="owner",
                email="owner@cleaning.com",
                role="owner",
                is_active=True
            )
            owner_user.set_password("123456")
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
            print("   👤 مستخدم: owner / 123456")
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


# تأكد من أن هذا السطر موجود في النهاية
__all__ = ['db', 'User', 'Employee', 'Company', 'Area', 'Location', 'Place', 'CleaningEvaluation', 'Attendance',
           'create_tables', 'initialize_default_data']
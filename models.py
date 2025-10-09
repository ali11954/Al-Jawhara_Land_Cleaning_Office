from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

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
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Employee(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
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
    supervised_areas = db.relationship('Area', backref='supervisor', foreign_keys='Area.supervisor_id')
    monitored_locations = db.relationship('Location', backref='monitor', foreign_keys='Location.monitor_id')
    assigned_places = db.relationship('Place', backref='worker', foreign_keys='Place.worker_id')

    def __repr__(self):
        return f'<Employee {self.full_name}>'


class Company(db.Model):
    __tablename__ = 'companies'

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
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    locations = db.relationship('Location', backref='area', lazy=True)

    def __repr__(self):
        return f'<Area {self.name}>'


class Location(db.Model):
    __tablename__ = 'locations'

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
    __tablename__ = 'places'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
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
    place_id = db.Column(db.Integer, db.ForeignKey('places.id'), nullable=False)
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
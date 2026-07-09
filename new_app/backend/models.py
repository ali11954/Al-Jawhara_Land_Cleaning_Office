from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'clean_users'
    __table_args__ = {'schema': None}
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120))
    password_hash = db.Column('password_hash', db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    employee_id = db.Column(db.Integer, nullable=True)
    company_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime)
    can_view_employees = db.Column(db.Boolean, default=False)
    can_edit_employees = db.Column(db.Boolean, default=False)
    can_add_employees = db.Column(db.Boolean, default=False)
    can_delete_employees = db.Column(db.Boolean, default=False)
    can_view_attendance = db.Column(db.Boolean, default=False)
    can_record_attendance = db.Column(db.Boolean, default=False)
    can_view_attendance_reports = db.Column(db.Boolean, default=False)
    can_view_overtime = db.Column(db.Boolean, default=False)
    can_view_absence_rates = db.Column(db.Boolean, default=False)
    can_view_evaluations = db.Column(db.Boolean, default=False)
    can_add_evaluations = db.Column(db.Boolean, default=False)
    can_view_evaluation_reports = db.Column(db.Boolean, default=False)
    can_view_detailed_evaluations = db.Column(db.Boolean, default=False)
    can_view_performance = db.Column(db.Boolean, default=False)
    can_view_top_employees = db.Column(db.Boolean, default=False)
    can_view_employee_efficiency = db.Column(db.Boolean, default=False)
    can_view_companies = db.Column(db.Boolean, default=False)
    can_view_company_stats = db.Column(db.Boolean, default=False)
    can_view_zones = db.Column(db.Boolean, default=False)
    can_view_salaries = db.Column(db.Boolean, default=False)
    can_view_salary_reports = db.Column(db.Boolean, default=False)
    can_view_financial = db.Column(db.Boolean, default=False)
    can_view_invoices = db.Column(db.Boolean, default=False)
    can_view_penalties = db.Column(db.Boolean, default=False)
    can_view_dashboard = db.Column(db.Boolean, default=False)
    can_view_kpis = db.Column(db.Boolean, default=False)
    can_view_heatmap = db.Column(db.Boolean, default=False)
    can_manage_users = db.Column(db.Boolean, default=False)
    can_manage_roles = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id, 'username': self.username, 'email': self.email,
            'role': self.role, 'is_active': self.is_active,
            'employee_id': self.employee_id, 'company_id': self.company_id,
            'full_name': self.username,
            'permissions': {
                'can_view_employees': self.can_view_employees,
                'can_edit_employees': self.can_edit_employees,
                'can_add_employees': self.can_add_employees,
                'can_delete_employees': self.can_delete_employees,
                'can_view_attendance': self.can_view_attendance,
                'can_record_attendance': self.can_record_attendance,
                'can_view_attendance_reports': self.can_view_attendance_reports,
                'can_view_overtime': self.can_view_overtime,
                'can_view_absence_rates': self.can_view_absence_rates,
                'can_view_evaluations': self.can_view_evaluations,
                'can_add_evaluations': self.can_add_evaluations,
                'can_view_evaluation_reports': self.can_view_evaluation_reports,
                'can_view_detailed_evaluations': self.can_view_detailed_evaluations,
                'can_view_performance': self.can_view_performance,
                'can_view_top_employees': self.can_view_top_employees,
                'can_view_employee_efficiency': self.can_view_employee_efficiency,
                'can_view_companies': self.can_view_companies,
                'can_view_company_stats': self.can_view_company_stats,
                'can_view_zones': self.can_view_zones,
                'can_view_salaries': self.can_view_salaries,
                'can_view_salary_reports': self.can_view_salary_reports,
                'can_view_financial': self.can_view_financial,
                'can_view_invoices': self.can_view_invoices,
                'can_view_penalties': self.can_view_penalties,
                'can_view_dashboard': self.can_view_dashboard,
                'can_view_kpis': self.can_view_kpis,
                'can_view_heatmap': self.can_view_heatmap,
                'can_manage_users': self.can_manage_users,
                'can_manage_roles': self.can_manage_roles,
            },
        }


class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    position = db.Column(db.String(200))
    salary = db.Column(db.Float, default=60000)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime)
    is_resident = db.Column(db.Boolean, default=False)
    base_salary = db.Column(db.Float, default=2000)
    daily_allowance = db.Column(db.Float, default=0)
    clothing_allowance = db.Column(db.Float, default=0)
    health_card_allowance = db.Column(db.Float, default=0)
    company_id = db.Column(db.Integer)
    supervisor_id = db.Column(db.Integer)
    qualification = db.Column(db.String(100))
    specialization = db.Column(db.String(100))
    hire_date = db.Column(db.Date)
    user_id = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        company_name = None
        supervisor_name = None
        try:
            if self.company_id:
                from db import fetch_one, get_db
                with get_db() as conn:
                    row = fetch_one(conn, "SELECT name FROM companies WHERE id=%s", (self.company_id,))
                    if row: company_name = row['name']
            if self.supervisor_id:
                from db import fetch_one, get_db
                with get_db() as conn:
                    row = fetch_one(conn, "SELECT full_name FROM employees WHERE id=%s", (self.supervisor_id,))
                    if row: supervisor_name = row['full_name']
        except Exception:
            pass
        return {
            'id': self.id, 'code': self.code, 'full_name': self.full_name,
            'name': self.full_name,
            'phone': self.phone, 'address': self.address, 'position': self.position,
            'job_title': self.position,
            'salary': self.salary, 'is_active': self.is_active,
            'is_resident': self.is_resident,
            'company_id': self.company_id,
            'company_name': company_name,
            'supervisor_id': self.supervisor_id,
            'supervisor_name': supervisor_name,
            'user_id': self.user_id,
            'qualification': self.qualification, 'specialization': self.specialization,
            'hire_date': self.hire_date.strftime('%Y-%m-%d') if self.hire_date else None,
            'base_salary': self.base_salary,
            'basic_salary': self.base_salary,
            'total_salary': self.salary,
            'daily_allowance': self.daily_allowance,
            'clothing_allowance': self.clothing_allowance,
            'health_card_allowance': self.health_card_allowance,
        }


class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)
    shift_type = db.Column(db.String(20), default='morning')
    status = db.Column(db.String(20), default='present')
    check_in = db.Column(db.Time)
    check_out = db.Column(db.Time)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id, 'employee_id': self.employee_id,
            'employee_name': '',
            'employee_code': '',
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'attendance_status': self.status,
            'status': self.status,
            'late_minutes': 0,
            'sick_leave': False,
            'sick_leave_days': 0,
            'annual_leave_days': 0,
            'check_in_time': self.check_in.strftime('%H:%M') if self.check_in else None,
            'check_out_time': self.check_out.strftime('%H:%M') if self.check_out else None,
            'notes': self.notes,
        }


class Evaluation(db.Model):
    __tablename__ = 'evaluations'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, nullable=False)
    evaluator_id = db.Column(db.Integer)
    evaluation_type = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    criteria_scores = db.Column(db.Text)
    region_id = db.Column(db.Integer)
    location_id = db.Column(db.Integer)

    def to_dict(self):
        return {
            'id': self.id, 'employee_id': self.employee_id,
            'employee_name': '',
            'evaluation_type': self.evaluation_type, 'score': self.score,
            'comments': self.comments,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'criteria_scores': [],
            'region_id': self.region_id, 'location_id': self.location_id,
        }


class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    receivable_account_id = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name,
            'contact_person': self.contact_person,
            'phone': self.phone, 'email': self.email,
        }


class Region(db.Model):
    __tablename__ = 'regions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    company_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name,
            'company_id': self.company_id,
        }


class Location(db.Model):
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    region_id = db.Column(db.Integer)
    address = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name,
            'region_id': self.region_id, 'address': self.address,
        }


class Contract(db.Model):
    __tablename__ = 'contracts'
    id = db.Column(db.Integer, primary_key=True)
    contract_number = db.Column(db.String(50))
    company_id = db.Column(db.Integer)
    contract_type = db.Column(db.String(20))
    contract_value = db.Column(db.Float, nullable=False)
    monthly_value = db.Column(db.Float)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    amount_received = db.Column(db.Float, default=0)
    remaining_amount = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='active')
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        company_name = None
        try:
            if self.company_id:
                from db import fetch_one, get_db
                with get_db() as conn:
                    row = fetch_one(conn, "SELECT name FROM companies WHERE id=%s", (self.company_id,))
                    if row: company_name = row['name']
        except Exception:
            pass
        return {
            'id': self.id, 'contract_number': self.contract_number,
            'company_id': self.company_id,
            'company_name': company_name or '',
            'contract_type': self.contract_type,
            'contract_value': self.contract_value,
            'monthly_value': self.monthly_value,
            'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else None,
            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else None,
            'amount_received': self.amount_received,
            'remaining_amount': self.remaining_amount,
            'status': self.status, 'is_active': self.is_active,
            'total_amount': self.contract_value,
        }


class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer)
    invoice_number = db.Column(db.String(50))
    amount = db.Column(db.Float, nullable=False)
    invoice_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date)
    is_paid = db.Column(db.Boolean, default=False)
    paid_date = db.Column(db.Date)
    paid_amount = db.Column(db.Float, default=0)
    payment_method = db.Column(db.String(50))
    description = db.Column(db.Text)
    payment_reference = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    journal_entry_id = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        company_name = None
        try:
            if self.contract_id:
                from db import fetch_one, get_db
                with get_db() as conn:
                    row = fetch_one(conn, "SELECT c.name as company_name FROM contracts ct JOIN companies c ON ct.company_id=c.id WHERE ct.id=%s", (self.contract_id,))
                    if row: company_name = row['company_name']
        except Exception:
            pass
        return {
            'id': self.id, 'contract_id': self.contract_id,
            'invoice_number': self.invoice_number, 'amount': self.amount,
            'invoice_date': self.invoice_date.strftime('%Y-%m-%d') if self.invoice_date else None,
            'date': self.invoice_date.strftime('%Y-%m-%d') if self.invoice_date else None,
            'due_date': self.due_date.strftime('%Y-%m-%d') if self.due_date else None,
            'is_paid': self.is_paid,
            'paid_date': self.paid_date.strftime('%Y-%m-%d') if self.paid_date else None,
            'paid_amount': self.paid_amount,
            'remaining_amount': (self.amount or 0) - (self.paid_amount or 0),
            'description': self.description,
            'company_name': company_name,
        }


class FinancialTransaction(db.Model):
    __tablename__ = 'financial_transactions'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(200))
    is_settled = db.Column(db.Boolean, default=False)
    settled_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer)

    def to_dict(self):
        return {
            'id': self.id, 'employee_id': self.employee_id,
            'employee_name': '',
            'transaction_type': self.transaction_type, 'amount': self.amount,
            'description': self.description,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'payment_method': 'cash',
            'is_settled': self.is_settled,
        }


class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    name_ar = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.String(20), nullable=False)
    nature = db.Column(db.String(10), nullable=False)
    parent_id = db.Column(db.Integer, nullable=True)
    opening_balance = db.Column(db.Float, default=0)
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'code': self.code, 'name': self.name,
            'name_ar': self.name_ar, 'account_type': self.account_type,
            'nature': self.nature, 'parent_id': self.parent_id,
            'is_active': self.is_active, 'opening_balance': self.opening_balance,
            'balance': self.opening_balance,
        }


class Supplier(db.Model):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_ar = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    tax_number = db.Column(db.String(50))
    bank_name = db.Column(db.String(100))
    bank_account = db.Column(db.String(100))
    supplier_type = db.Column(db.String(50), default='general')
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    payable_account_id = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'name_ar': self.name_ar,
            'phone': self.phone, 'supplier_type': self.supplier_type,
            'is_active': self.is_active,
        }


class JournalEntry(db.Model):
    __tablename__ = 'journal_entries'
    id = db.Column(db.Integer, primary_key=True)
    entry_number = db.Column(db.String(50), unique=True, nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    reference_type = db.Column(db.String(50), nullable=True)
    reference_id = db.Column(db.Integer, nullable=True)
    created_by = db.Column(db.Integer)
    is_posted = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'entry_number': self.entry_number,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'description': self.description,
            'total_debit': 0,
            'total_credit': 0,
        }


class JournalEntryDetail(db.Model):
    __tablename__ = 'journal_entry_details'
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, nullable=False)
    account_id = db.Column(db.Integer, nullable=False)
    debit = db.Column(db.Float, default=0)
    credit = db.Column(db.Float, default=0)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'account_id': self.account_id,
            'debit': self.debit, 'credit': self.credit,
            'description': self.description,
        }


class Salary(db.Model):
    __tablename__ = 'salaries'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, nullable=False)
    month_year = db.Column(db.String(20), nullable=False)
    base_salary = db.Column(db.Float, default=0)
    attendance_days = db.Column(db.Integer, default=0)
    attendance_amount = db.Column(db.Float, default=0)
    daily_allowance_amount = db.Column(db.Float, default=0)
    overtime_amount = db.Column(db.Float, default=0)
    advance_amount = db.Column(db.Float, default=0)
    deduction_amount = db.Column(db.Float, default=0)
    penalty_amount = db.Column(db.Float, default=0)
    total_salary = db.Column(db.Float, default=0)
    is_paid = db.Column(db.Boolean, default=False)
    paid_date = db.Column(db.Date)
    payment_method = db.Column(db.String(50))
    payment_reference = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    cafeteria_deduction = db.Column(db.Float, default=0)
    restaurant_deduction = db.Column(db.Float, default=0)
    meal_deduction_amount = db.Column(db.Float, default=0)
    basic_salary_amount = db.Column(db.Float, default=0)
    resident_allowance_amount = db.Column(db.Float, default=0)
    clothing_allowance_amount = db.Column(db.Float, default=0)
    health_card_amount = db.Column(db.Float, default=0)
    insurance_amount = db.Column(db.Float, default=0)
    contractor_profit = db.Column(db.Float, default=0)

    def to_dict(self):
        return {
            'id': self.id, 'employee_id': self.employee_id,
            'employee_name': '',
            'month_year': self.month_year,
            'attendance_days': self.attendance_days,
            'total_salary': self.total_salary or 0,
            'is_paid': self.is_paid,
        }

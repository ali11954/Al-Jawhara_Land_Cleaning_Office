from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    allowed_pages = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        import json
        return {
            'id': self.id, 'username': self.username, 'full_name': self.full_name,
            'role': self.role, 'is_active': self.is_active,
            'employee_id': self.employee_id,
            'allowed_pages': json.loads(self.allowed_pages) if self.allowed_pages else [],
        }


class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    position = db.Column(db.String(20))
    salary = db.Column(db.Float, default=60000)
    total_salary = db.Column(db.Float, default=60000)
    daily_allowance = db.Column(db.Float, default=500)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime)
    is_resident = db.Column(db.Boolean, default=False)
    basic_salary = db.Column(db.Float, default=2000)
    clothing_allowance = db.Column(db.Float, default=24480)
    health_card_allowance = db.Column(db.Float, default=15000)
    monthly_insurance = db.Column(db.Float, default=10800)
    contractor_tax = db.Column(db.Float, default=500000)
    contractor_zakat = db.Column(db.Float, default=75000)
    worker_type = db.Column(db.String(20), default='permanent')
    region_id = db.Column(db.Integer, db.ForeignKey('regions.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    supervisor_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    qualification = db.Column(db.String(100))
    specialization = db.Column(db.String(100))
    hire_date = db.Column(db.Date)
    allowances_updated_at = db.Column(db.DateTime)

    company = db.relationship('Company', foreign_keys=[company_id], backref='employees')
    region_rel = db.relationship('Region', foreign_keys=[region_id], backref='region_employees')

    def to_dict(self):
        return {
            'id': self.id, 'code': self.code, 'full_name': self.full_name,
            'phone': self.phone, 'address': self.address, 'position': self.position,
            'salary': self.salary, 'total_salary': self.total_salary,
            'daily_allowance': self.daily_allowance, 'is_active': self.is_active,
            'is_resident': self.is_resident, 'worker_type': self.worker_type,
            'company_id': self.company_id,
            'company_name': self.company.name if self.company else None,
            'region_id': self.region_id,
            'region_name': self.region_rel.name if self.region_rel else None,
            'supervisor_id': self.supervisor_id, 'user_id': self.user_id,
            'qualification': self.qualification, 'specialization': self.specialization,
            'hire_date': self.hire_date.strftime('%Y-%m-%d') if self.hire_date else None,
        }


class Attendance(db.Model):
    __tablename__ = 'attendances'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    attendance_type = db.Column(db.String(20), default='individual')
    attendance_status = db.Column(db.String(20), default='present')
    late_minutes = db.Column(db.Integer, default=0)
    sick_leave = db.Column(db.Boolean, default=False)
    sick_leave_days = db.Column(db.Integer, default=0)
    annual_leave_days = db.Column(db.Integer, default=0)
    check_in_time = db.Column(db.Time)
    check_out_time = db.Column(db.Time)
    notes = db.Column(db.String(500))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship('Employee', backref='attendances')
    creator = db.relationship('User', backref='created_attendances')

    __table_args__ = (
        db.UniqueConstraint('employee_id', 'date', name='unique_employee_date'),
    )

    def to_dict(self):
        return {
            'id': self.id, 'employee_id': self.employee_id,
            'employee_name': self.employee.full_name if self.employee else '',
            'employee_code': self.employee.code if self.employee else '',
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'attendance_status': self.attendance_status,
            'late_minutes': self.late_minutes,
            'sick_leave': self.sick_leave,
            'sick_leave_days': self.sick_leave_days,
            'annual_leave_days': self.annual_leave_days,
            'check_in_time': self.check_in_time.strftime('%H:%M') if self.check_in_time else None,
            'check_out_time': self.check_out_time.strftime('%H:%M') if self.check_out_time else None,
            'notes': self.notes,
        }


class Evaluation(db.Model):
    __tablename__ = 'evaluations'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    evaluation_type = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    criteria_scores = db.Column(db.Text)
    region_id = db.Column(db.Integer, db.ForeignKey('regions.id'), nullable=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True)

    employee = db.relationship('Employee', backref='evaluations')
    evaluator = db.relationship('User', backref='evaluations')
    region = db.relationship('Region', foreign_keys=[region_id], backref='region_evaluations')
    location = db.relationship('Location', foreign_keys=[location_id], backref='location_evaluations')

    def to_dict(self):
        import json
        return {
            'id': self.id, 'employee_id': self.employee_id,
            'employee_name': self.employee.full_name if self.employee else '',
            'evaluation_type': self.evaluation_type, 'score': self.score,
            'comments': self.comments,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'criteria_scores': json.loads(self.criteria_scores) if self.criteria_scores else [],
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
    receivable_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)

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
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    company = db.relationship('Company', backref='company_regions')

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name,
            'company_id': self.company_id,
            'company_name': self.company.name if self.company else None,
        }


class Location(db.Model):
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    region_id = db.Column(db.Integer, db.ForeignKey('regions.id'), nullable=False)
    address = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    region = db.relationship('Region', backref='region_locations')

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name,
            'region_id': self.region_id, 'address': self.address,
        }


class Contract(db.Model):
    __tablename__ = 'contracts'
    id = db.Column(db.Integer, primary_key=True)
    contract_number = db.Column(db.String(50))
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
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

    company = db.relationship('Company', backref='contracts')

    def to_dict(self):
        return {
            'id': self.id, 'contract_number': self.contract_number,
            'company_id': self.company_id,
            'company_name': self.company.name if self.company else '',
            'contract_type': self.contract_type,
            'contract_value': self.contract_value,
            'monthly_value': self.monthly_value,
            'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else None,
            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else None,
            'amount_received': self.amount_received,
            'remaining_amount': self.remaining_amount,
            'status': self.status, 'is_active': self.is_active,
        }


class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id'))
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
    journal_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entries.id'), nullable=True)

    contract = db.relationship('Contract', backref='invoices')

    def to_dict(self):
        return {
            'id': self.id, 'contract_id': self.contract_id,
            'invoice_number': self.invoice_number, 'amount': self.amount,
            'invoice_date': self.invoice_date.strftime('%Y-%m-%d') if self.invoice_date else None,
            'due_date': self.due_date.strftime('%Y-%m-%d') if self.due_date else None,
            'is_paid': self.is_paid,
            'paid_date': self.paid_date.strftime('%Y-%m-%d') if self.paid_date else None,
            'paid_amount': self.paid_amount,
            'remaining_amount': (self.amount or 0) - (self.paid_amount or 0),
            'description': self.description,
        }


class FinancialTransaction(db.Model):
    __tablename__ = 'financial_transactions'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(200))
    is_settled = db.Column(db.Boolean, default=False)
    settled_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    payment_method = db.Column(db.String(20), default='cash')
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    monthly_installment = db.Column(db.Float, default=0)
    settled_amount = db.Column(db.Float, default=0)
    journal_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entries.id'), nullable=True)

    employee = db.relationship('Employee', backref='transactions')
    supplier = db.relationship('Supplier', backref='transactions')
    creator = db.relationship('User', backref='created_transactions')

    def to_dict(self):
        return {
            'id': self.id, 'employee_id': self.employee_id,
            'employee_name': self.employee.full_name if self.employee else '',
            'transaction_type': self.transaction_type, 'amount': self.amount,
            'description': self.description,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'payment_method': self.payment_method or 'cash',
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
    parent_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)
    opening_balance = db.Column(db.Float, default=0)
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parent = db.relationship('Account', remote_side=[id], backref='children')

    def to_dict(self):
        return {
            'id': self.id, 'code': self.code, 'name': self.name,
            'name_ar': self.name_ar, 'account_type': self.account_type,
            'nature': self.nature, 'parent_id': self.parent_id,
            'is_active': self.is_active, 'opening_balance': self.opening_balance,
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
    payable_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)

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
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_posted = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    details = db.relationship('JournalEntryDetail', backref='entry', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id, 'entry_number': self.entry_number,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'description': self.description,
            'total_debit': sum(d.debit for d in self.details),
            'total_credit': sum(d.credit for d in self.details),
        }


class JournalEntryDetail(db.Model):
    __tablename__ = 'journal_entry_details'
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('journal_entries.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    debit = db.Column(db.Float, default=0)
    credit = db.Column(db.Float, default=0)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    account = db.relationship('Account', backref='journal_entries')

    def to_dict(self):
        return {
            'id': self.id, 'account_id': self.account_id,
            'debit': self.debit, 'credit': self.credit,
            'description': self.description,
        }


class Salary(db.Model):
    __tablename__ = 'salaries'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
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
    cafeteria_supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    restaurant_supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    cafeteria_paid_to_supplier = db.Column(db.Boolean, default=False)
    restaurant_paid_to_supplier = db.Column(db.Boolean, default=False)
    is_calculated = db.Column(db.Boolean, default=False)
    calculated_at = db.Column(db.DateTime)
    journal_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entries.id'), nullable=True)

    employee = db.relationship('Employee', backref='salaries')

    __table_args__ = (
        db.UniqueConstraint('employee_id', 'month_year', name='uq_employee_period_salary'),
    )

    def to_dict(self):
        emp = self.employee
        return {
            'id': self.id, 'employee_id': self.employee_id,
            'employee_name': emp.full_name if emp else '',
            'month_year': self.month_year,
            'attendance_days': self.attendance_days,
            'total_salary': self.total_salary or 0,
            'is_paid': self.is_paid,
        }

"""
Complete API Endpoints for Cleaning Company Management System
Covers ALL routes from the old app.py
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import date, datetime, timedelta
from models import (
    db, User, Employee, Company, Area, Location, Place,
    Attendance, CleaningEvaluation, SupervisorEvaluation,
    Salary, Contract, Invoice, Supplier, SupplierInvoice,
    FinancialTransaction, EmployeeTransaction
)

api = Blueprint('api', __name__, url_prefix='/api/v1')


def ok(data=None, msg='success'):
    return jsonify({'status': 'ok', 'message': msg, 'data': data})


def fail(msg='error', code=400):
    return jsonify({'status': 'fail', 'message': msg}), code


# ═══════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════
@api.route('/dashboard')
@login_required
def dashboard():
    today = date.today()
    week_ago = today - timedelta(days=7)

    total_emp = Employee.query.count()
    active_emp = Employee.query.filter_by(is_active=True).count()
    total_co = Company.query.filter_by(is_active=True).count()
    total_areas = Area.query.filter_by(is_active=True).count()
    evals_today = CleaningEvaluation.query.filter_by(date=today).count()
    avg = db.session.query(db.func.avg(CleaningEvaluation.overall_score)) \
        .filter(CleaningEvaluation.date == today).scalar() or 0
    att = Attendance.query.filter_by(date=today).all()
    present = sum(1 for a in att if a.status == 'present')

    labels, eval_d, att_p, att_a = [], [], [], []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        labels.append(d.strftime('%m-%d'))
        a = db.session.query(db.func.avg(CleaningEvaluation.overall_score)) \
            .filter(CleaningEvaluation.date == d).scalar() or 0
        eval_d.append(round(float(a) * 20, 1))
        recs = Attendance.query.filter_by(date=d).all()
        att_p.append(sum(1 for r in recs if r.status == 'present'))
        att_a.append(sum(1 for r in recs if r.status == 'absent'))

    recent = CleaningEvaluation.query \
        .order_by(CleaningEvaluation.created_at.desc()).limit(5).all()

    return ok({
        'stats': {
            'total_employees': total_emp, 'active_employees': active_emp,
            'total_companies': total_co, 'total_areas': total_areas,
            'evaluations_today': evals_today, 'avg_score': round(float(avg) * 20, 1),
            'present_today': present,
        },
        'charts': {
            'evaluation': {'labels': labels, 'data': eval_d},
            'attendance': {'labels': labels, 'present': att_p, 'absent': att_a},
        },
        'recent_evaluations': [{
            'id': e.id, 'score': round(float(e.overall_score or 0) * 20),
            'date': e.date.isoformat() if e.date else None,
            'evaluator': e.evaluator.full_name if e.evaluator else None,
            'evaluated': e.evaluated_employee.full_name if e.evaluated_employee else None,
        } for e in recent],
    })


# ═══════════════════════════════════════════════════
# USERS
# ═══════════════════════════════════════════════════
@api.route('/users')
@login_required
def users_list():
    if current_user.role != 'owner':
        return fail('غير مصرح', 403)
    users = User.query.all()
    return ok([{
        'id': u.id, 'username': u.username, 'email': u.email,
        'role': u.role, 'is_active': u.is_active,
    } for u in users])


@api.route('/users', methods=['POST'])
@login_required
def users_add():
    if current_user.role != 'owner':
        return fail('غير مصرح', 403)
    d = request.json
    if User.query.filter_by(username=d.get('username')).first():
        return fail('اسم المستخدم موجود مسبقاً')
    u = User(username=d['username'], email=d['email'], role=d.get('role', 'worker'))
    u.set_password(d['password'])
    db.session.add(u)
    db.session.commit()
    return ok({'id': u.id}, 'تم الإضافة')


@api.route('/users/<int:id>', methods=['PUT'])
@login_required
def users_update(id):
    if current_user.role != 'owner':
        return fail('غير مصرح', 403)
    u = User.query.get_or_404(id)
    d = request.json
    u.email = d.get('email', u.email)
    u.role = d.get('role', u.role)
    u.is_active = d.get('is_active', u.is_active)
    if d.get('password'):
        u.set_password(d['password'])
    db.session.commit()
    return ok(msg='تم التحديث')


@api.route('/users/<int:id>', methods=['DELETE'])
@login_required
def users_delete(id):
    if current_user.role != 'owner':
        return fail('غير مصرح', 403)
    u = User.query.get_or_404(id)
    if u.id == current_user.id:
        return fail('لا يمكن حذف نفسك')
    db.session.delete(u)
    db.session.commit()
    return ok(msg='تم الحذف')


@api.route('/users/<int:id>/toggle', methods=['POST'])
@login_required
def users_toggle(id):
    if current_user.role != 'owner':
        return fail('غير مصرح', 403)
    u = User.query.get_or_404(id)
    u.is_active = not u.is_active
    db.session.commit()
    return ok({'is_active': u.is_active})


# ═══════════════════════════════════════════════════
# EMPLOYEES
# ═══════════════════════════════════════════════════
@api.route('/employees')
@login_required
def employees_list():
    emps = Employee.query.order_by(Employee.id.desc()).all()
    return ok([emp_to_dict(e) for e in emps])


@api.route('/employees/<int:id>')
@login_required
def employee_detail(id):
    e = Employee.query.get_or_404(id)
    stats = db.session.query(
        db.func.count(Attendance.id),
        db.func.sum(db.case((Attendance.status == 'present', 1), else_=0)),
        db.func.sum(db.case((Attendance.status == 'absent', 1), else_=0)),
        db.func.sum(db.case((Attendance.status == 'late', 1), else_=0))
    ).filter(Attendance.employee_id == id).first()
    recent = Attendance.query.filter_by(employee_id=id) \
        .order_by(Attendance.date.desc()).limit(10).all()
    return ok({
        **emp_to_dict(e),
        'attendance_stats': {
            'total': stats[0] or 0, 'present': stats[1] or 0,
            'absent': stats[2] or 0, 'late': stats[3] or 0,
        },
        'recent_attendance': [att_to_dict(r) for r in recent],
    })


@api.route('/employees', methods=['POST'])
@login_required
def employees_add():
    d = request.json
    e = Employee(
        full_name=d['full_name'], code=d.get('code', f"EMP{Employee.query.count()+1:03d}"),
        phone=d.get('phone'), position=d.get('position', 'worker'),
        salary=d.get('salary', 60000), base_salary=d.get('base_salary', 50000),
        hire_date=date.fromisoformat(d['hire_date']) if d.get('hire_date') else date.today(),
        company_id=d.get('company_id'), is_active=True,
    )
    db.session.add(e)
    db.session.commit()
    return ok({'id': e.id}, 'تم الإضافة')


@api.route('/employees/<int:id>', methods=['PUT'])
@login_required
def employees_update(id):
    e = Employee.query.get_or_404(id)
    d = request.json
    for f in ['full_name', 'phone', 'position', 'salary', 'base_salary', 'is_active', 'company_id']:
        if f in d: setattr(e, f, d[f])
    if 'hire_date' in d: e.hire_date = date.fromisoformat(d['hire_date'])
    db.session.commit()
    return ok(msg='تم التحديث')


@api.route('/employees/<int:id>', methods=['DELETE'])
@login_required
def employees_delete(id):
    e = Employee.query.get_or_404(id)
    e.is_active = False
    db.session.commit()
    return ok(msg='تم التعطيل')


def emp_to_dict(e):
    return {
        'id': e.id, 'code': e.code, 'full_name': e.full_name,
        'phone': e.phone, 'position': e.position,
        'salary': e.salary, 'base_salary': e.base_salary,
        'is_active': e.is_active, 'is_resident': getattr(e, 'is_resident', False),
        'hire_date': e.hire_date.isoformat() if e.hire_date else None,
        'company': e.company.name if e.company else None,
        'company_id': e.company_id,
    }


# ═══════════════════════════════════════════════════
# ATTENDANCE
# ═══════════════════════════════════════════════════
@api.route('/attendance')
@login_required
def attendance_list():
    q = Attendance.query
    df = request.args.get('date_from')
    dt = request.args.get('date_to')
    eid = request.args.get('employee_id', type=int)
    if df: q = q.filter(Attendance.date >= df)
    if dt: q = q.filter(Attendance.date <= dt)
    if eid: q = q.filter(Attendance.employee_id == eid)
    records = q.order_by(Attendance.date.desc()).limit(300).all()
    return ok([att_to_dict(r) for r in records])


@api.route('/attendance', methods=['POST'])
@login_required
def attendance_add():
    d = request.json
    a = Attendance(
        employee_id=d['employee_id'], date=date.fromisoformat(d['date']),
        shift_type=d.get('shift_type', 'morning'), status=d.get('status', 'present'),
    )
    if d.get('check_in'): a.check_in = datetime.strptime(d['check_in'], '%H:%M').time()
    if d.get('check_out'): a.check_out = datetime.strptime(d['check_out'], '%H:%M').time()
    db.session.add(a)
    db.session.commit()
    return ok({'id': a.id}, 'تم التسجيل')


@api.route('/attendance/<int:id>', methods=['PUT'])
@login_required
def attendance_update(id):
    a = Attendance.query.get_or_404(id)
    d = request.json
    if 'status' in d: a.status = d['status']
    if 'shift_type' in d: a.shift_type = d['shift_type']
    if 'check_in' in d and d['check_in']: a.check_in = datetime.strptime(d['check_in'], '%H:%M').time()
    if 'check_out' in d and d['check_out']: a.check_out = datetime.strptime(d['check_out'], '%H:%M').time()
    db.session.commit()
    return ok(msg='تم التحديث')


@api.route('/attendance/<int:id>', methods=['DELETE'])
@login_required
def attendance_delete(id):
    a = Attendance.query.get_or_404(id)
    db.session.delete(a)
    db.session.commit()
    return ok(msg='تم الحذف')


def att_to_dict(r):
    return {
        'id': r.id, 'employee': r.employee.full_name if r.employee else None,
        'employee_id': r.employee_id,
        'date': r.date.isoformat() if r.date else None,
        'status': r.status, 'shift': r.shift_type,
        'check_in': r.check_in.strftime('%H:%M') if r.check_in else None,
        'check_out': r.check_out.strftime('%H:%M') if r.check_out else None,
        'notes': r.notes,
    }


# ═══════════════════════════════════════════════════
# EVALUATIONS
# ═══════════════════════════════════════════════════
@api.route('/evaluations')
@login_required
def evaluations_list():
    evals = CleaningEvaluation.query \
        .order_by(CleaningEvaluation.created_at.desc()).limit(300).all()
    return ok([eval_to_dict(e) for e in evals])


@api.route('/evaluations', methods=['POST'])
@login_required
def evaluations_add():
    d = request.json
    e = CleaningEvaluation(
        place_id=d['place_id'], evaluator_id=d['evaluator_id'],
        evaluated_employee_id=d['evaluated_employee_id'],
        date=date.fromisoformat(d['date']) if d.get('date') else date.today(),
        cleanliness=d.get('cleanliness', 3), organization=d.get('organization', 3),
        equipment_condition=d.get('equipment_condition', 3),
        time=d.get('time', 3), safety_measures=d.get('safety_measures', 3),
        comments=d.get('comments'),
    )
    e.calculate_overall_score()
    db.session.add(e)
    db.session.commit()
    return ok({'id': e.id}, 'تم الإضافة')


def eval_to_dict(e):
    return {
        'id': e.id, 'score': round(float(e.overall_score or 0) * 20),
        'date': e.date.isoformat() if e.date else None,
        'evaluator': e.evaluator.full_name if e.evaluator else None,
        'evaluated': e.evaluated_employee.full_name if e.evaluated_employee else None,
        'place': e.place.name if hasattr(e, 'place') and e.place else None,
        'cleanliness': e.cleanliness, 'organization': e.organization,
        'equipment_condition': e.equipment_condition,
        'time': e.time, 'safety_measures': e.safety_measures,
        'comments': e.comments,
    }


# ═══════════════════════════════════════════════════
# COMPANIES
# ═══════════════════════════════════════════════════
@api.route('/companies')
@login_required
def companies_list():
    cos = Company.query.order_by(Company.id.desc()).all()
    return ok([company_to_dict(c) for c in cos])


@api.route('/companies/<int:id>')
@login_required
def company_detail(id):
    c = Company.query.get_or_404(id)
    areas = Area.query.filter_by(company_id=id, is_active=True).all()
    return ok({
        **company_to_dict(c),
        'areas': [{'id': a.id, 'name': a.name, 'supervisor': a.supervisor.full_name if a.supervisor else None} for a in areas],
    })


@api.route('/companies', methods=['POST'])
@login_required
def companies_add():
    if current_user.role != 'owner':
        return fail('غير مصرح', 403)
    d = request.json
    c = Company(name=d['name'], phone=d.get('phone'), email=d.get('email'), is_active=True)
    db.session.add(c)
    db.session.commit()
    return ok({'id': c.id}, 'تم الإضافة')


@api.route('/companies/<int:id>', methods=['PUT'])
@login_required
def companies_update(id):
    c = Company.query.get_or_404(id)
    d = request.json
    for f in ['name', 'phone', 'email', 'address', 'is_active']:
        if f in d: setattr(c, f, d[f])
    db.session.commit()
    return ok(msg='تم التحديث')


@api.route('/companies/<int:id>', methods=['DELETE'])
@login_required
def companies_delete(id):
    c = Company.query.get_or_404(id)
    c.is_active = False
    db.session.commit()
    return ok(msg='تم التعطيل')


def company_to_dict(c):
    return {
        'id': c.id, 'name': c.name, 'phone': c.phone,
        'email': c.email, 'address': getattr(c, 'address', None),
        'is_active': c.is_active,
        'areas_count': len(c.areas) if c.areas else 0,
    }


# ═══════════════════════════════════════════════════
# AREAS / LOCATIONS / PLACES
# ═══════════════════════════════════════════════════
@api.route('/areas/<int:company_id>')
@login_required
def areas_list(company_id):
    areas = Area.query.filter_by(company_id=company_id, is_active=True).all()
    return ok([{'id': a.id, 'name': a.name, 'supervisor_id': a.supervisor_id,
               'supervisor': a.supervisor.full_name if a.supervisor else None} for a in areas])


@api.route('/areas', methods=['POST'])
@login_required
def areas_add():
    d = request.json
    a = Area(name=d['name'], company_id=d['company_id'], supervisor_id=d.get('supervisor_id'))
    db.session.add(a)
    db.session.commit()
    return ok({'id': a.id}, 'تم الإضافة')


@api.route('/areas/<int:id>', methods=['PUT'])
@login_required
def areas_update(id):
    a = Area.query.get_or_404(id)
    d = request.json
    if 'name' in d: a.name = d['name']
    if 'supervisor_id' in d: a.supervisor_id = d['supervisor_id']
    db.session.commit()
    return ok(msg='تم التحديث')


@api.route('/areas/<int:id>', methods=['DELETE'])
@login_required
def areas_delete(id):
    a = Area.query.get_or_404(id)
    a.is_active = False
    db.session.commit()
    return ok(msg='تم الحذف')


@api.route('/locations/<int:area_id>')
@login_required
def locations_list(area_id):
    locs = Location.query.filter_by(area_id=area_id, is_active=True).all()
    return ok([{'id': l.id, 'name': l.name, 'area_id': l.area_id} for l in locs])


@api.route('/locations', methods=['POST'])
@login_required
def locations_add():
    d = request.json
    l = Location(name=d['name'], area_id=d['area_id'])
    db.session.add(l)
    db.session.commit()
    return ok({'id': l.id}, 'تم الإضافة')


@api.route('/places/<int:location_id>')
@login_required
def places_list(location_id):
    places = Place.query.filter_by(location_id=location_id, is_active=True).all()
    return ok([{'id': p.id, 'name': p.name, 'worker_id': p.worker_id,
               'worker': p.worker.full_name if p.worker else None} for p in places])


@api.route('/places', methods=['POST'])
@login_required
def places_add():
    d = request.json
    p = Place(name=d['name'], location_id=d['location_id'], worker_id=d.get('worker_id'))
    db.session.add(p)
    db.session.commit()
    return ok({'id': p.id}, 'تم الإضافة')


# ═══════════════════════════════════════════════════
# CONTRACTS
# ═══════════════════════════════════════════════════
@api.route('/contracts')
@login_required
def contracts_list():
    try:
        from models import Contract
        contracts = Contract.query.order_by(Contract.id.desc()).all()
        return ok([{
            'id': c.id, 'contract_number': c.contract_number,
            'company': c.company.name if c.company else None,
            'start_date': c.start_date.isoformat() if c.start_date else None,
            'end_date': c.end_date.isoformat() if c.end_date else None,
            'total_amount': c.total_amount,
            'status': c.status,
        } for c in contracts])
    except:
        return ok([])


@api.route('/contracts', methods=['POST'])
@login_required
def contracts_add():
    try:
        from models import Contract
        d = request.json
        c = Contract(
            contract_number=d['contract_number'], company_id=d['company_id'],
            start_date=date.fromisoformat(d['start_date']),
            end_date=date.fromisoformat(d['end_date']),
            total_amount=d.get('total_amount', 0), status='active',
        )
        db.session.add(c)
        db.session.commit()
        return ok({'id': c.id}, 'تم الإضافة')
    except Exception as e:
        return fail(str(e))


# ═══════════════════════════════════════════════════
# INVOICES
# ═══════════════════════════════════════════════════
@api.route('/invoices')
@login_required
def invoices_list():
    try:
        from models import Invoice
        invoices = Invoice.query.order_by(Invoice.id.desc()).all()
        return ok([{
            'id': i.id, 'invoice_number': i.invoice_number,
            'company': i.company.name if i.company else None,
            'amount': i.amount, 'paid_amount': i.paid_amount,
            'status': i.status, 'date': i.date.isoformat() if i.date else None,
        } for i in invoices])
    except:
        return ok([])


# ═══════════════════════════════════════════════════
# SUPPLIERS
# ═══════════════════════════════════════════════════
@api.route('/suppliers')
@login_required
def suppliers_list():
    try:
        from models import Supplier
        suppliers = Supplier.query.filter_by(is_active=True).all()
        return ok([{'id': s.id, 'name': s.name, 'phone': s.phone,
                    'email': s.email, 'address': s.address} for s in suppliers])
    except:
        return ok([])


@api.route('/suppliers', methods=['POST'])
@login_required
def suppliers_add():
    try:
        from models import Supplier
        d = request.json
        s = Supplier(name=d['name'], phone=d.get('phone'), email=d.get('email'), is_active=True)
        db.session.add(s)
        db.session.commit()
        return ok({'id': s.id}, 'تم الإضافة')
    except Exception as e:
        return fail(str(e))


@api.route('/supplier-invoices')
@login_required
def supplier_invoices_list():
    try:
        from models import SupplierInvoice
        invoices = SupplierInvoice.query.order_by(SupplierInvoice.id.desc()).all()
        return ok([{
            'id': i.id, 'invoice_number': i.invoice_number,
            'supplier': i.supplier.name if i.supplier else None,
            'amount': i.amount, 'paid_amount': i.paid_amount,
            'remaining_amount': i.remaining_amount,
            'date': i.invoice_date.isoformat() if i.invoice_date else None,
        } for i in invoices])
    except:
        return ok([])


# ═══════════════════════════════════════════════════
# FINANCIAL - SALARIES
# ═══════════════════════════════════════════════════
@api.route('/salaries')
@login_required
def salaries_list():
    try:
        from models import Salary
        salaries = Salary.query.order_by(Salary.id.desc()).limit(200).all()
        return ok([{
            'id': s.id, 'employee': s.employee.full_name if s.employee else None,
            'employee_id': s.employee_id,
            'base_salary': s.base_salary, 'allowances': s.allowances,
            'deductions': s.deductions, 'total_salary': s.total_salary,
            'is_paid': s.is_paid, 'period': s.period_display if hasattr(s, 'period_display') else None,
        } for s in salaries])
    except:
        return ok([])


@api.route('/salaries/calculate', methods=['POST'])
@login_required
def salaries_calculate():
    try:
        from models import Salary
        d = request.json
        employees = Employee.query.filter_by(is_active=True).all()
        count = 0
        for emp in employees:
            existing = Salary.query.filter_by(employee_id=emp.id, period_display=d.get('period')).first()
            if not existing:
                s = Salary(
                    employee_id=emp.id, base_salary=emp.base_salary or emp.salary,
                    allowances=0, deductions=0,
                    total_salary=emp.base_salary or emp.salary,
                    is_paid=False, period_display=d.get('period', datetime.now().strftime('%Y-%m')),
                )
                db.session.add(s)
                count += 1
        db.session.commit()
        return ok({'count': count}, f'تم حساب {count} راتب')
    except Exception as e:
        return fail(str(e))


# ═══════════════════════════════════════════════════
# FINANCIAL - DEDUCTIONS / PENALTIES / LOANS / OVERTIME
# ═══════════════════════════════════════════════════
@api.route('/deductions')
@login_required
def deductions_list():
    try:
        from models import FinancialTransaction
        items = FinancialTransaction.query.filter_by(transaction_type='deduction').order_by(FinancialTransaction.date.desc()).limit(200).all()
        return ok([{
            'id': t.id, 'employee_id': t.employee_id,
            'amount': t.amount, 'date': t.date.isoformat() if t.date else None,
            'description': t.description, 'is_settled': t.is_settled,
        } for t in items])
    except:
        return ok([])


@api.route('/penalties')
@login_required
def penalties_list():
    try:
        from models import FinancialTransaction
        items = FinancialTransaction.query.filter_by(transaction_type='penalty').order_by(FinancialTransaction.date.desc()).limit(200).all()
        return ok([{
            'id': t.id, 'employee_id': t.employee_id,
            'amount': t.amount, 'date': t.date.isoformat() if t.date else None,
            'description': t.description, 'is_settled': t.is_settled,
        } for t in items])
    except:
        return ok([])


@api.route('/loans')
@login_required
def loans_list():
    try:
        from models import FinancialTransaction
        items = FinancialTransaction.query.filter_by(transaction_type='advance').order_by(FinancialTransaction.date.desc()).limit(200).all()
        return ok([{
            'id': t.id, 'employee_id': t.employee_id,
            'amount': t.amount, 'date': t.date.isoformat() if t.date else None,
            'description': t.description, 'is_settled': t.is_settled,
        } for t in items])
    except:
        return ok([])


@api.route('/overtime')
@login_required
def overtime_list():
    try:
        from models import FinancialTransaction
        items = FinancialTransaction.query.filter_by(transaction_type='overtime').order_by(FinancialTransaction.date.desc()).limit(200).all()
        return ok([{
            'id': t.id, 'employee_id': t.employee_id,
            'amount': t.amount, 'date': t.date.isoformat() if t.date else None,
            'description': t.description,
        } for t in items])
    except:
        return ok([])


# ═══════════════════════════════════════════════════
# REPORTS
# ═══════════════════════════════════════════════════
@api.route('/reports')
@login_required
def reports_index():
    return ok({
        'total_employees': Employee.query.count(),
        'active_employees': Employee.query.filter_by(is_active=True).count(),
        'total_companies': Company.query.filter_by(is_active=True).count(),
        'total_areas': Area.query.filter_by(is_active=True).count(),
        'total_evaluations': CleaningEvaluation.query.count(),
        'avg_score': round(float(
            db.session.query(db.func.avg(CleaningEvaluation.overall_score)).scalar() or 0
        ) * 20, 1),
    })


@api.route('/reports/attendance-record')
@login_required
def reports_attendance():
    today = date.today()
    month_start = today.replace(day=1)
    records = Attendance.query.filter(Attendance.date >= month_start).all()
    present = sum(1 for r in records if r.status == 'present')
    absent = sum(1 for r in records if r.status == 'absent')
    late = sum(1 for r in records if r.status == 'late')
    return ok({
        'total': len(records), 'present': present,
        'absent': absent, 'late': late,
        'rate': round(present / len(records) * 100, 1) if records else 0,
    })


@api.route('/reports/daily-evaluations')
@login_required
def reports_daily_evals():
    today = date.today()
    evals = CleaningEvaluation.query.filter_by(date=today).all()
    avg = sum(e.overall_score for e in evals) / len(evals) if evals else 0
    return ok({
        'total': len(evals), 'avg_score': round(float(avg) * 20, 1),
    })


@api.route('/reports/salary-report')
@login_required
def reports_salary():
    emps = Employee.query.filter_by(is_active=True).all()
    total = sum(e.salary or 0 for e in emps)
    return ok({
        'total_employees': len(emps), 'total_salaries': total,
        'avg_salary': round(total / len(emps)) if emps else 0,
    })


@api.route('/reports/top-employees')
@login_required
def reports_top_employees():
    top = db.session.query(
        Employee.full_name,
        db.func.avg(CleaningEvaluation.overall_score).label('avg'),
    ).join(CleaningEvaluation, CleaningEvaluation.evaluator_id == Employee.id) \
        .group_by(Employee.id).order_by(db.desc('avg')).limit(10).all()
    return ok([{'name': n, 'avg_score': round(float(a) * 20, 1)} for n, a in top])


# ═══════════════════════════════════════════════════
# ACCOUNTS
# ═══════════════════════════════════════════════════
@api.route('/accounts')
@login_required
def accounts_index():
    try:
        from models import Account
        accounts = Account.query.filter_by(is_active=True).order_by(Account.code).all()
        total_assets = sum(a.get_balance() for a in accounts if a.account_type == 'asset')
        total_expenses = sum(a.get_balance() for a in accounts if a.account_type == 'expense')
        total_revenue = sum(a.get_balance() for a in accounts if a.account_type == 'revenue')
        return ok({
            'accounts': [{'id': a.id, 'code': a.code, 'name': a.name,
                          'type': a.account_type, 'balance': a.get_balance()} for a in accounts],
            'total_assets': total_assets, 'total_expenses': total_expenses,
            'total_revenue': total_revenue, 'net_income': total_revenue - total_expenses,
        })
    except:
        return ok({'accounts': [], 'total_assets': 0, 'total_expenses': 0, 'total_revenue': 0, 'net_income': 0})


@api.route('/accounts/journal')
@login_required
def accounts_journal():
    try:
        from models import JournalEntry
        entries = JournalEntry.query.order_by(JournalEntry.date.desc()).limit(200).all()
        return ok([{
            'id': e.id, 'entry_number': e.entry_number,
            'date': e.date.isoformat() if e.date else None,
            'description': e.description,
            'total_debit': e.total_debit, 'total_credit': e.total_credit,
        } for e in entries])
    except:
        return ok([])


# ═══════════════════════════════════════════════════
# SETTINGS
# ═══════════════════════════════════════════════════
@api.route('/profile')
@login_required
def profile():
    return ok({
        'id': current_user.id, 'username': current_user.username,
        'email': current_user.email, 'role': current_user.role,
    })


@api.route('/settings', methods=['GET'])
@login_required
def settings_get():
    return ok({'app_name': 'الجوهرة للنظافة', 'version': '2.0'})


# ═══════════════════════════════════════════════════
# EXPENSE CATEGORIES
# ═══════════════════════════════════════════════════
@api.route('/expense-categories')
@login_required
def expense_categories_list():
    try:
        from models import ExpenseCategory
        cats = ExpenseCategory.query.all()
        return ok([{'id': c.id, 'name': c.name} for c in cats])
    except:
        return ok([])

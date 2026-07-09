from flask import Blueprint, request, jsonify
from auth import token_required
from models import db, Employee
from db import get_db, fetch_all, execute

employees_bp = Blueprint('employees', __name__)


@employees_bp.route('/api/employees', methods=['GET'])
@token_required
def list_employees(current_user):
    page = request.args.get('page', type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    company_id = request.args.get('company_id', type=int)
    query = Employee.query

    # Supervisor can only see employees in their company and linked to them
    if current_user.role == 'supervisor':
        if current_user.company_id:
            query = query.filter(Employee.company_id == current_user.company_id)
        if current_user.employee_id:
            query = query.filter(Employee.supervisor_id == current_user.employee_id)
    elif current_user.role == 'owner':
        pass  # Owner sees everything
    elif current_user.role not in ('admin', 'owner'):
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    if search:
        query = query.filter(db.or_(Employee.full_name.contains(search), Employee.code.contains(search)))
    if company_id and current_user.role in ('admin', 'owner'):
        query = query.filter_by(company_id=company_id)
    if page:
        pagination = query.order_by(Employee.full_name).paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({'success': True, 'data': {'items': [e.to_dict() for e in pagination.items], 'total': pagination.total, 'page': page, 'pages': pagination.pages}})
    else:
        employees = query.order_by(Employee.full_name).all()
        return jsonify({'success': True, 'data': [e.to_dict() for e in employees]})


@employees_bp.route('/api/employees/<int:emp_id>', methods=['GET'])
@token_required
def get_employee(current_user, emp_id):
    emp = Employee.query.get_or_404(emp_id)
    return jsonify({'success': True, 'data': emp.to_dict()})


@employees_bp.route('/api/employees', methods=['POST'])
@token_required
def create_employee(current_user):
    data = request.get_json()
    emp_name = data.get('full_name') or data.get('name', '')
    if not data or not emp_name:
        return jsonify({'success': False, 'message': 'full_name is required'}), 400
    emp = Employee(full_name=emp_name, code=data.get('code', ''), position=data.get('position') or data.get('job_title', ''),
                   is_resident=data.get('is_resident', False), phone=data.get('phone', ''), address=data.get('address', ''),
                   salary=data.get('salary', 60000), is_active=data.get('is_active', True),
                   company_id=data.get('company_id'), supervisor_id=data.get('supervisor_id'),
                   qualification=data.get('qualification', ''),
                   specialization=data.get('specialization', ''))
    db.session.add(emp)
    db.session.commit()
    return jsonify({'success': True, 'data': emp.to_dict(), 'message': 'Employee created'}), 201


@employees_bp.route('/api/employees/<int:emp_id>', methods=['PUT'])
@token_required
def update_employee(current_user, emp_id):
    emp = Employee.query.get_or_404(emp_id)
    data = request.get_json()
    if 'name' in data and 'full_name' not in data:
        data['full_name'] = data['name']
    if 'job_title' in data and 'position' not in data:
        data['position'] = data['job_title']
    for field in ['full_name', 'code', 'position', 'is_resident', 'phone', 'address',
                  'salary', 'is_active', 'company_id', 'supervisor_id', 'qualification',
                  'specialization', 'base_salary', 'hire_date']:
        if field in data:
            setattr(emp, field, data[field])
    db.session.commit()
    return jsonify({'success': True, 'data': emp.to_dict(), 'message': 'Employee updated'})


@employees_bp.route('/api/employees/<int:emp_id>', methods=['DELETE'])
@token_required
def delete_employee(current_user, emp_id):
    emp = Employee.query.get_or_404(emp_id)
    db.session.delete(emp)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Employee deleted'})


@employees_bp.route('/api/employees/<int:emp_id>/bank-info', methods=['GET'])
@token_required
def get_bank_info(current_user, emp_id):
    with get_db() as conn:
        rows = fetch_all(conn, "SELECT * FROM bank_info WHERE employee_id=%s", (emp_id,))
    return jsonify({'success': True, 'data': rows})


@employees_bp.route('/api/employees/<int:emp_id>/bank-info', methods=['POST'])
@token_required
def add_bank_info(current_user, emp_id):
    data = request.get_json()
    with get_db() as conn:
        bid = execute(conn, "INSERT INTO bank_info (employee_id, bank_name, account_number, iban, is_primary) VALUES (%s,%s,%s,%s,%s) RETURNING id",
                      (emp_id, data.get('bank_name', ''), data.get('account_number', ''), data.get('iban', ''), data.get('is_primary', False)))
    return jsonify({'success': True, 'data': {'id': bid}, 'message': 'Bank info added'}), 201


@employees_bp.route('/api/bank-info/<int:info_id>', methods=['PUT'])
@token_required
def update_bank_info(current_user, info_id):
    data = request.get_json()
    with get_db() as conn:
        fields = []
        vals = []
        for f in ['bank_name', 'account_number', 'iban', 'is_primary']:
            if f in data:
                fields.append(f'{f}=%s')
                vals.append(data[f])
        if fields:
            vals.append(info_id)
            execute(conn, f"UPDATE bank_info SET {','.join(fields)} WHERE id=%s", vals)
    return jsonify({'success': True, 'message': 'Bank info updated'})


@employees_bp.route('/api/bank-info/<int:info_id>', methods=['DELETE'])
@token_required
def delete_bank_info(current_user, info_id):
    with get_db() as conn:
        execute(conn, "DELETE FROM bank_info WHERE id=%s", (info_id,))
    return jsonify({'success': True, 'message': 'Bank info deleted'})

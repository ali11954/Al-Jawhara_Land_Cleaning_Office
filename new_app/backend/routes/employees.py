from flask import Blueprint, request, jsonify
from auth import token_required
from db import get_db, fetch_all, fetch_one, execute

employees_bp = Blueprint('employees', __name__)

EMPLOYEE_COLUMNS = """id, code, full_name, phone, address, card_number, position, salary, is_active,
    created_at, updated_at, is_resident, base_salary, daily_allowance, clothing_allowance,
    health_card_allowance, company_id, supervisor_id, qualification, specialization,
    hire_date, user_id"""


def _emp_to_dict(row):
    company_name = None
    supervisor_name = None
    try:
        if row.get('company_id'):
            with get_db() as conn:
                r = fetch_one(conn, "SELECT name FROM clean_companies WHERE id=%s", (row['company_id'],))
                if r:
                    company_name = r['name']
        if row.get('supervisor_id'):
            with get_db() as conn:
                r = fetch_one(conn, "SELECT full_name FROM employees WHERE id=%s", (row['supervisor_id'],))
                if r:
                    supervisor_name = r['full_name']
    except Exception:
        pass
    return {
        'id': row.get('id'),
        'code': row.get('code'),
        'full_name': row.get('full_name'),
        'name': row.get('full_name'),
        'card_number': row.get('card_number'),
        'phone': row.get('phone'),
        'address': row.get('address'),
        'position': row.get('position'),
        'job_title': row.get('position'),
        'salary': row.get('salary'),
        'is_active': row.get('is_active'),
        'is_resident': row.get('is_resident'),
        'company_id': row.get('company_id'),
        'company_name': company_name,
        'supervisor_id': row.get('supervisor_id'),
        'supervisor_name': supervisor_name,
        'user_id': row.get('user_id'),
        'qualification': row.get('qualification'),
        'specialization': row.get('specialization'),
        'hire_date': row.get('hire_date').strftime('%Y-%m-%d') if row.get('hire_date') and hasattr(row['hire_date'], 'strftime') else str(row['hire_date']) if row.get('hire_date') else None,
        'base_salary': row.get('base_salary'),
        'basic_salary': row.get('base_salary'),
        'total_salary': row.get('salary'),
        'daily_allowance': row.get('daily_allowance'),
        'clothing_allowance': row.get('clothing_allowance'),
        'health_card_allowance': row.get('health_card_allowance'),
    }


@employees_bp.route('/api/employees', methods=['GET'])
@token_required
def list_employees(current_user):
    page = request.args.get('page', type=int)
    per_page = request.args.get('per_page', 100, type=int)
    search = request.args.get('search', '')
    company_id = request.args.get('company_id', type=int)

    q = f"SELECT {EMPLOYEE_COLUMNS} FROM employees WHERE 1=1"
    params = []

    if current_user.role == 'supervisor':
        if current_user.company_id:
            q += " AND company_id = %s"
            params.append(current_user.company_id)
        if current_user.employee_id:
            q += " AND supervisor_id = %s"
            params.append(current_user.employee_id)
    elif current_user.role not in ('admin', 'owner'):
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    if search:
        q += " AND (full_name ILIKE %s OR code ILIKE %s)"
        params.extend([f'%{search}%', f'%{search}%'])

    if company_id and current_user.role in ('admin', 'owner'):
        q += " AND company_id = %s"
        params.append(company_id)

    q += " ORDER BY full_name"

    with get_db() as conn:
        if page:
            count_q = q.replace(f"SELECT {EMPLOYEE_COLUMNS}", "SELECT COUNT(*)")
            cur = conn.cursor()
            cur.execute(count_q, tuple(params))
            total = cur.fetchone()[0]
            offset = (page - 1) * per_page
            q += f" LIMIT {per_page} OFFSET {offset}"
            rows = fetch_all(conn, q, tuple(params))
            pages = (total + per_page - 1) // per_page
            return jsonify({'success': True, 'data': {
                'items': [_emp_to_dict(r) for r in rows],
                'total': total, 'page': page, 'pages': pages
            }})
        else:
            rows = fetch_all(conn, q, tuple(params))
            return jsonify({'success': True, 'data': [_emp_to_dict(r) for r in rows]})


@employees_bp.route('/api/employees/<int:emp_id>', methods=['GET'])
@token_required
def get_employee(current_user, emp_id):
    with get_db() as conn:
        row = fetch_one(conn, f"SELECT {EMPLOYEE_COLUMNS} FROM employees WHERE id=%s", (emp_id,))
    if not row:
        return jsonify({'success': False, 'message': 'Employee not found'}), 404
    return jsonify({'success': True, 'data': _emp_to_dict(row)})


@employees_bp.route('/api/employees', methods=['POST'])
@token_required
def create_employee(current_user):
    try:
        data = request.get_json()
        emp_name = data.get('full_name') or data.get('name', '')
        if not data or not emp_name:
            return jsonify({'success': False, 'message': 'الاسم مطلوب'}), 400

        code = data.get('code', '') or ''
        card_number = data.get('card_number', '') or ''
        position = data.get('position') or data.get('job_title', '') or ''
        phone = data.get('phone', '') or ''
        address = data.get('address', '') or ''
        salary = data.get('salary') or data.get('total_salary') or 60000
        base_salary = data.get('base_salary') or data.get('basic_salary') or 60000
        is_active = data.get('is_active', True)
        is_resident = data.get('is_resident', False)
        company_id = data.get('company_id') if data.get('company_id') else None
        supervisor_id = data.get('supervisor_id') if data.get('supervisor_id') else None
        qualification = data.get('qualification', '') or ''
        specialization = data.get('specialization', '') or ''
        daily_allowance = data.get('daily_allowance') or 0
        clothing_allowance = data.get('clothing_allowance') or 0
        health_card_allowance = data.get('health_card_allowance') or 0

        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO employees (code, full_name, phone, address, card_number, position, salary, base_salary,
                   is_active, is_resident, company_id, supervisor_id, qualification, specialization,
                   daily_allowance, clothing_allowance, health_card_allowance, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                   RETURNING id""",
                (code, emp_name, phone, address, card_number, position, salary, base_salary,
                 is_active, is_resident, company_id, supervisor_id, qualification, specialization,
                 daily_allowance, clothing_allowance, health_card_allowance))
            emp_id = cur.fetchone()[0]
            conn.commit()

        with get_db() as conn:
            row = fetch_one(conn, f"SELECT {EMPLOYEE_COLUMNS} FROM employees WHERE id=%s", (emp_id,))

        return jsonify({'success': True, 'data': _emp_to_dict(row), 'message': 'تم إضافة الموظف بنجاح'}), 201
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@employees_bp.route('/api/employees/<int:emp_id>', methods=['PUT'])
@token_required
def update_employee(current_user, emp_id):
    data = request.get_json()
    if 'name' in data and 'full_name' not in data:
        data['full_name'] = data['name']
    if 'job_title' in data and 'position' not in data:
        data['position'] = data['job_title']
    if 'basic_salary' in data and 'base_salary' not in data:
        data['base_salary'] = data['basic_salary']
    if 'total_salary' in data and 'salary' not in data:
        data['salary'] = data['total_salary']

    field_map = {
        'full_name': 'full_name', 'code': 'code', 'card_number': 'card_number',
        'position': 'position',
        'phone': 'phone', 'address': 'address', 'salary': 'salary',
        'base_salary': 'base_salary', 'is_active': 'is_active',
        'is_resident': 'is_resident', 'company_id': 'company_id',
        'supervisor_id': 'supervisor_id', 'qualification': 'qualification',
        'specialization': 'specialization', 'hire_date': 'hire_date',
        'daily_allowance': 'daily_allowance', 'clothing_allowance': 'clothing_allowance',
        'health_card_allowance': 'health_card_allowance',
    }

    sets = []
    vals = []
    for js_field, db_field in field_map.items():
        if js_field in data:
            val = data[js_field]
            if js_field == 'company_id' and val == '':
                val = None
            if js_field == 'supervisor_id' and val == '':
                val = None
            sets.append(f'{db_field}=%s')
            vals.append(val)

    if not sets:
        return jsonify({'success': False, 'message': 'No fields to update'}), 400

    sets.append('updated_at=NOW()')
    vals.append(emp_id)

    with get_db() as conn:
        execute(conn, f"UPDATE employees SET {','.join(sets)} WHERE id=%s", vals)

    with get_db() as conn:
        row = fetch_one(conn, f"SELECT {EMPLOYEE_COLUMNS} FROM employees WHERE id=%s", (emp_id,))
    if not row:
        return jsonify({'success': False, 'message': 'Employee not found'}), 404
    return jsonify({'success': True, 'data': _emp_to_dict(row), 'message': 'تم تعديل الموظف بنجاح'})


@employees_bp.route('/api/employees/<int:emp_id>', methods=['DELETE'])
@token_required
def delete_employee(current_user, emp_id):
    with get_db() as conn:
        execute(conn, "DELETE FROM employees WHERE id=%s", (emp_id,))
    return jsonify({'success': True, 'message': 'تم حذف الموظف بنجاح'})


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
        bid = execute(conn, "INSERT INTO bank_info (employee_id, bank_name, account_number, iban, swift_code, branch_name, account_type, currency, is_primary, notes) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
                      (emp_id, data.get('bank_name', ''), data.get('account_number', ''), data.get('iban', ''), data.get('swift_code', ''), data.get('branch_name', ''), data.get('account_type', 'current'), data.get('currency', 'YER'), data.get('is_primary', False), data.get('notes', '')))
    return jsonify({'success': True, 'data': {'id': bid}, 'message': 'Bank info added'}), 201


@employees_bp.route('/api/bank-info/<int:info_id>', methods=['PUT'])
@token_required
def update_bank_info(current_user, info_id):
    data = request.get_json()
    with get_db() as conn:
        fields = []
        vals = []
        for f in ['bank_name', 'account_number', 'iban', 'swift_code', 'branch_name', 'account_type', 'currency', 'is_primary', 'notes']:
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

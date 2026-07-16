from flask import Blueprint, request, jsonify
from auth import token_required
from db import get_db, fetch_all, fetch_one, execute
from datetime import datetime

employees_bp = Blueprint('employees', __name__)

EMPLOYEE_COLUMNS = """id, code, full_name, phone, address, card_number, position, salary, is_active,
    created_at, updated_at, is_resident, base_salary, daily_allowance, clothing_allowance,
    health_card_allowance, company_id, supervisor_id, qualification, specialization,
    hire_date, user_id, region"""


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
        'region': row.get('region'),
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
        emp_name = (data.get('full_name') or data.get('name', '')).strip()
        if not data or not emp_name:
            return jsonify({'success': False, 'message': 'الاسم مطلوب'}), 400

        code = str(data.get('code', '') or '')
        card_number = str(data.get('card_number', '') or '')
        position = str(data.get('position') or data.get('job_title', '') or '').strip() or 'غير محدد'
        phone = str(data.get('phone', '') or '')
        address = str(data.get('address', '') or '')
        try:
            salary = float(data.get('salary') or data.get('total_salary') or 0)
        except (TypeError, ValueError):
            salary = 0
        try:
            base_salary = float(data.get('base_salary') or data.get('basic_salary') or 0)
        except (TypeError, ValueError):
            base_salary = 0
        is_active = bool(data.get('is_active', True))
        is_resident = bool(data.get('is_resident', False))
        company_id = int(data['company_id']) if data.get('company_id') else None
        supervisor_id = int(data['supervisor_id']) if data.get('supervisor_id') else None
        qualification = str(data.get('qualification', '') or '')
        specialization = str(data.get('specialization', '') or '')
        try:
            daily_allowance = float(data.get('daily_allowance') or 0)
        except (TypeError, ValueError):
            daily_allowance = 0
        try:
            clothing_allowance = float(data.get('clothing_allowance') or 0)
        except (TypeError, ValueError):
            clothing_allowance = 0
        try:
            health_card_allowance = float(data.get('health_card_allowance') or 0)
        except (TypeError, ValueError):
            health_card_allowance = 0
        hire_date = data.get('hire_date') or datetime.utcnow().strftime('%Y-%m-%d')
        region = str(data.get('region', '') or '')

        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO employees (code, full_name, phone, address, card_number, position, salary, base_salary,
                   is_active, is_resident, company_id, supervisor_id, qualification, specialization,
                   daily_allowance, clothing_allowance, health_card_allowance, hire_date, region, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                   RETURNING id""",
                (code, emp_name, phone, address, card_number, position, salary, base_salary,
                 is_active, is_resident, company_id, supervisor_id, qualification, specialization,
                 daily_allowance, clothing_allowance, health_card_allowance, hire_date, region))
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
        cur = conn.cursor()
        cur.execute("SELECT id FROM employees WHERE id=%s", (emp_id,))
        if not cur.fetchone():
            return jsonify({'success': False, 'message': 'الموظف غير موجود'}), 404

        tables_to_clean = [
            ("attendance", "employee_id"),
            ("evaluations", "employee_id"),
            ("salaries", "employee_id"),
            ("financial_transactions", "employee_id"),
            ("leave_requests", "employee_id"),
            ("penalties", "employee_id"),
            ("overtime", "employee_id"),
            ("payrolls", "employee_id"),
            ("employee_loans", "employee_id"),
            ("meal_deductions", "employee_id"),
            ("labor_monthly_costs", "employee_id"),
            ("bank_info", "employee_id"),
            ("clean_users", "employee_id"),
        ]
        for table, col in tables_to_clean:
            try:
                cur.execute(f"DELETE FROM {table} WHERE {col}=%s", (emp_id,))
            except Exception:
                pass

        try:
            cur.execute("DELETE FROM cleaning_evaluations WHERE evaluated_employee_id=%s OR evaluator_id=%s", (emp_id, emp_id))
        except Exception:
            pass
        try:
            cur.execute("DELETE FROM supervisor_evaluations WHERE supervisor_id=%s OR evaluator_id=%s", (emp_id, emp_id))
        except Exception:
            pass
        try:
            cur.execute("UPDATE employees SET supervisor_id=NULL WHERE supervisor_id=%s", (emp_id,))
        except Exception:
            pass

        cur.execute("DELETE FROM employees WHERE id=%s", (emp_id,))
        conn.commit()
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

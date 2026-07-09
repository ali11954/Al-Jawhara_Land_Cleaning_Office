from flask import Blueprint, request, jsonify
from auth import token_required
from models import db, FinancialTransaction, Employee, Salary
from datetime import datetime
from db import get_db, fetch_all, fetch_one, execute

financial_bp = Blueprint('financial', __name__)


@financial_bp.route('/api/financial/dashboard', methods=['GET'])
@token_required
def financial_dashboard(current_user):
    company_filter = ""
    company_val = None
    supervisor_filter = ""
    supervisor_val = None

    if current_user.role == 'supervisor':
        if current_user.company_id:
            company_filter = " AND e.company_id = %s"
            company_val = current_user.company_id
        if current_user.employee_id:
            supervisor_filter = " AND e.supervisor_id = %s"
            supervisor_val = current_user.employee_id

    def build_params():
        p = []
        if company_val is not None:
            p.append(company_val)
        if supervisor_val is not None:
            p.append(supervisor_val)
        return tuple(p)

    with get_db() as conn:
        cur = conn.cursor()

        cur.execute(f"SELECT COUNT(*) FROM employees e WHERE e.is_active = true{company_filter}{supervisor_filter}", build_params())
        active_employees = cur.fetchone()[0]

        results = {}
        for tx_type in ['advance', 'overtime', 'deduction', 'penalty']:
            cur.execute(f"SELECT COALESCE(SUM(ft.amount), 0) FROM financial_transactions ft JOIN employees e ON ft.employee_id = e.id WHERE ft.transaction_type = '{tx_type}' AND ft.is_settled = false{company_filter}{supervisor_filter}", build_params())
            results[f'total_{tx_type}s'] = cur.fetchone()[0]

    return jsonify({'success': True, 'data': {
        'active_employees': active_employees,
        'total_advances': float(results['total_advances']),
        'total_overtime': float(results['total_overtimes']),
        'total_deductions': float(results['total_deductions']),
        'total_penalties': float(results['total_penaltys'])}})


@financial_bp.route('/api/financial/transactions', methods=['GET'])
@token_required
def list_transactions(current_user):
    page = request.args.get('page', type=int)
    per_page = request.args.get('per_page', 50, type=int)
    employee_id = request.args.get('employee_id', type=int)
    tx_type = request.args.get('type')

    with get_db() as conn:
        q = "SELECT ft.* FROM financial_transactions ft JOIN employees e ON ft.employee_id = e.id WHERE 1=1"
        params = []

        if current_user.role == 'supervisor':
            if current_user.company_id:
                q += " AND e.company_id = %s"
                params.append(current_user.company_id)
            if current_user.employee_id:
                q += " AND e.supervisor_id = %s"
                params.append(current_user.employee_id)
        elif current_user.role not in ('admin', 'owner'):
            return jsonify({'success': False, 'message': 'Access denied'}), 403

        if employee_id:
            q += " AND ft.employee_id = %s"
            params.append(employee_id)
        if tx_type:
            q += " AND ft.transaction_type = %s"
            params.append(tx_type)

        q += " ORDER BY ft.date DESC"

        if page:
            count_q = q.replace("SELECT ft.*", "SELECT COUNT(*)")
            cur = conn.cursor()
            cur.execute(count_q, tuple(params))
            total = cur.fetchone()[0]
            offset = (page - 1) * per_page
            q += f" LIMIT {per_page} OFFSET {offset}"
            rows = fetch_all(conn, q, tuple(params))
            pages = (total + per_page - 1) // per_page
            return jsonify({'success': True, 'data': {'items': rows, 'total': total, 'page': page, 'pages': pages}})
        else:
            rows = fetch_all(conn, q, tuple(params))
            return jsonify({'success': True, 'data': rows})


@financial_bp.route('/api/financial/transactions', methods=['POST'])
@token_required
def create_transaction(current_user):
    data = request.get_json()
    if not data or not data.get('employee_id') or not data.get('amount') or not data.get('transaction_type'):
        return jsonify({'success': False, 'message': 'employee_id, amount, and transaction_type are required'}), 400
    with get_db() as conn:
        execute(conn,
            "INSERT INTO financial_transactions (employee_id, transaction_type, amount, description, date, created_by) VALUES (%s,%s,%s,%s,%s,%s)",
            (data['employee_id'], data['transaction_type'], data['amount'], data.get('description', ''),
             data.get('date', datetime.utcnow().strftime('%Y-%m-%d')), current_user.id))
    return jsonify({'success': True, 'message': 'Transaction created'}), 201


@financial_bp.route('/api/financial/salaries', methods=['GET'])
@token_required
def list_salaries(current_user):
    month_year = request.args.get('month_year')
    employee_id = request.args.get('employee_id', type=int)
    with get_db() as conn:
        q = "SELECT s.*, e.full_name as employee_name, e.code as employee_code FROM salaries s LEFT JOIN employees e ON s.employee_id=e.id WHERE 1=1"
        params = []
        if current_user.role == 'supervisor':
            if current_user.company_id:
                q += " AND e.company_id = %s"
                params.append(current_user.company_id)
            if current_user.employee_id:
                q += " AND e.supervisor_id = %s"
                params.append(current_user.employee_id)
        if month_year:
            q += " AND s.month_year=%s"
            params.append(month_year)
        if employee_id:
            q += " AND s.employee_id=%s"
            params.append(employee_id)
        q += " ORDER BY s.created_at DESC"
        rows = fetch_all(conn, q, tuple(params))
    return jsonify({'success': True, 'data': rows})


@financial_bp.route('/api/financial/salaries/<int:salary_id>', methods=['DELETE'])
@token_required
def delete_salary(current_user, salary_id):
    with get_db() as conn:
        execute(conn, "DELETE FROM salaries WHERE id=%s", (salary_id,))
    return jsonify({'success': True, 'message': 'Salary deleted'})


@financial_bp.route('/api/financial/salaries/<int:salary_id>/pay', methods=['POST'])
@token_required
def pay_salary(current_user, salary_id):
    with get_db() as conn:
        execute(conn, "UPDATE salaries SET is_paid=true, paid_date=%s WHERE id=%s", (datetime.utcnow().strftime('%Y-%m-%d'), salary_id))
    return jsonify({'success': True, 'message': 'Salary marked as paid'})


@financial_bp.route('/api/financial/salaries/<int:salary_id>/voucher', methods=['GET'])
@token_required
def salary_voucher(current_user, salary_id):
    with get_db() as conn:
        row = fetch_one(conn, "SELECT s.*, e.full_name as employee_name, e.code as employee_code FROM salaries s LEFT JOIN employees e ON s.employee_id=e.id WHERE s.id=%s", (salary_id,))
    return jsonify({'success': True, 'data': row})


@financial_bp.route('/api/financial/salary-calculation', methods=['POST'])
@token_required
def calculate_salaries(current_user):
    data = request.get_json() or {}
    month_year = data.get('month_year', datetime.utcnow().strftime('%Y-%m'))

    with get_db() as conn:
        cur = conn.cursor()
        q = "SELECT id, full_name, salary FROM employees WHERE is_active = true"
        params = []
        if current_user.role == 'supervisor':
            if current_user.company_id:
                q += " AND company_id = %s"
                params.append(current_user.company_id)
            if current_user.employee_id:
                q += " AND supervisor_id = %s"
                params.append(current_user.employee_id)
        cur.execute(q, tuple(params))
        employees = cur.fetchall()

    created = []
    for emp in employees:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM salaries WHERE employee_id=%s AND month_year=%s", (emp[0], month_year))
            if cur.fetchone():
                continue
            base = emp[2] or 0
            execute(conn, "INSERT INTO salaries (employee_id, month_year, base_salary, attendance_days, total_salary) VALUES (%s,%s,%s,%s,%s)",
                    (emp[0], month_year, base, 22, base))
            created.append(emp[1])
    return jsonify({'success': True, 'data': {'created': len(created)}, 'message': f'{len(created)} salaries calculated'})


@financial_bp.route('/api/financial/advances/unsettled', methods=['GET'])
@token_required
def unsettled_advances(current_user):
    with get_db() as conn:
        q = "SELECT ft.*, e.full_name as employee_name FROM financial_transactions ft LEFT JOIN employees e ON ft.employee_id=e.id WHERE ft.transaction_type='advance' AND ft.is_settled=false"
        params = []
        if current_user.role == 'supervisor':
            if current_user.company_id:
                q += " AND e.company_id = %s"
                params.append(current_user.company_id)
            if current_user.employee_id:
                q += " AND e.supervisor_id = %s"
                params.append(current_user.employee_id)
        q += " ORDER BY ft.date DESC"
        rows = fetch_all(conn, q, tuple(params))
    return jsonify({'success': True, 'data': rows})


@financial_bp.route('/api/financial/advances/settle', methods=['POST'])
@token_required
def settle_advance(current_user):
    data = request.get_json() or {}
    tx_id = data.get('transaction_id')
    if not tx_id:
        return jsonify({'success': False, 'message': 'transaction_id required'}), 400
    with get_db() as conn:
        execute(conn, "UPDATE financial_transactions SET is_settled=true, settled_date=%s WHERE id=%s",
                (datetime.utcnow().strftime('%Y-%m-%d'), tx_id))
    return jsonify({'success': True, 'message': 'Advance settled'})

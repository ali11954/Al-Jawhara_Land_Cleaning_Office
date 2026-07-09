from flask import Blueprint, request, jsonify
from auth import token_required
from models import db, FinancialTransaction, Employee, Salary
from datetime import datetime
from sqlalchemy import func
from db import get_db, fetch_all, fetch_one, execute

financial_bp = Blueprint('financial', __name__)


@financial_bp.route('/api/financial/dashboard', methods=['GET'])
@token_required
def financial_dashboard(current_user):
    total_advances = db.session.query(func.coalesce(func.sum(FinancialTransaction.amount), 0)).filter(
        FinancialTransaction.transaction_type == 'advance', FinancialTransaction.is_settled == False).scalar()
    total_overtime = db.session.query(func.coalesce(func.sum(FinancialTransaction.amount), 0)).filter(
        FinancialTransaction.transaction_type == 'overtime', FinancialTransaction.is_settled == False).scalar()
    total_deductions = db.session.query(func.coalesce(func.sum(FinancialTransaction.amount), 0)).filter(
        FinancialTransaction.transaction_type == 'deduction', FinancialTransaction.is_settled == False).scalar()
    total_penalties = db.session.query(func.coalesce(func.sum(FinancialTransaction.amount), 0)).filter(
        FinancialTransaction.transaction_type == 'penalty', FinancialTransaction.is_settled == False).scalar()
    active_employees = Employee.query.filter_by(is_active=True).count()
    return jsonify({'success': True, 'data': {
        'active_employees': active_employees, 'total_advances': float(total_advances),
        'total_overtime': float(total_overtime), 'total_deductions': float(total_deductions),
        'total_penalties': float(total_penalties)}})


@financial_bp.route('/api/financial/transactions', methods=['GET'])
@token_required
def list_transactions(current_user):
    page = request.args.get('page', type=int)
    per_page = request.args.get('per_page', 50, type=int)
    employee_id = request.args.get('employee_id', type=int)
    tx_type = request.args.get('type')
    query = FinancialTransaction.query
    if employee_id:
        query = query.filter_by(employee_id=employee_id)
    if tx_type:
        query = query.filter_by(transaction_type=tx_type)
    if page:
        pagination = query.order_by(FinancialTransaction.date.desc()).paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({'success': True, 'data': {'items': [t.to_dict() for t in pagination.items], 'total': pagination.total, 'page': page, 'pages': pagination.pages}})
    else:
        transactions = query.order_by(FinancialTransaction.date.desc()).all()
        return jsonify({'success': True, 'data': [t.to_dict() for t in transactions]})


@financial_bp.route('/api/financial/transactions', methods=['POST'])
@token_required
def create_transaction(current_user):
    data = request.get_json()
    if not data or not data.get('employee_id') or not data.get('amount') or not data.get('transaction_type'):
        return jsonify({'success': False, 'message': 'employee_id, amount, and transaction_type are required'}), 400
    tx = FinancialTransaction(employee_id=data['employee_id'], transaction_type=data['transaction_type'],
                              amount=data['amount'], description=data.get('description', ''),
                              date=datetime.strptime(data['date'], '%Y-%m-%d').date() if data.get('date') else datetime.utcnow().date(),
                              payment_method=data.get('payment_method', 'cash'), created_by=current_user.id)
    db.session.add(tx)
    db.session.commit()
    return jsonify({'success': True, 'data': tx.to_dict(), 'message': 'Transaction created'}), 201


@financial_bp.route('/api/financial/salaries', methods=['GET'])
@token_required
def list_salaries(current_user):
    month_year = request.args.get('month_year')
    employee_id = request.args.get('employee_id', type=int)
    with get_db() as conn:
        q = "SELECT s.*, e.full_name as employee_name, e.code as employee_code FROM salaries s LEFT JOIN employees e ON s.employee_id=e.id WHERE 1=1"
        params = []
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
    employees = Employee.query.filter_by(is_active=True).all()
    created = []
    for emp in employees:
        with get_db() as conn:
            existing = fetch_one(conn, "SELECT id FROM salaries WHERE employee_id=%s AND month_year=%s", (emp.id, month_year))
            if existing:
                continue
            base = emp.salary or 0
            execute(conn, "INSERT INTO salaries (employee_id, month_year, base_salary, attendance_days, total_salary, is_calculated, calculated_at) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (emp.id, month_year, base, 22, base, True, datetime.utcnow().isoformat()))
            created.append(emp.full_name)
    return jsonify({'success': True, 'data': {'created': len(created)}, 'message': f'{len(created)} salaries calculated'})


@financial_bp.route('/api/financial/advances/unsettled', methods=['GET'])
@token_required
def unsettled_advances(current_user):
    with get_db() as conn:
        rows = fetch_all(conn,
            "SELECT ft.*, e.full_name as employee_name FROM financial_transactions ft "
            "LEFT JOIN employees e ON ft.employee_id=e.id "
            "WHERE ft.transaction_type='advance' AND ft.is_settled=false ORDER BY ft.date DESC")
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

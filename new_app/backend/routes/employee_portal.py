from flask import Blueprint, request, jsonify
from auth import token_required
from db import get_db, fetch_all

employee_portal_bp = Blueprint('employee_portal', __name__)


@employee_portal_bp.route('/api/employee/my-profile', methods=['GET'])
@token_required
def my_profile(current_user):
    if not current_user.employee_id:
        return jsonify({'success': False, 'message': 'No employee linked'}), 404
    from models import Employee
    emp = Employee.query.get(current_user.employee_id)
    if not emp:
        return jsonify({'success': False, 'message': 'Employee not found'}), 404
    return jsonify({'success': True, 'data': emp.to_dict()})


@employee_portal_bp.route('/api/employee/my-attendance', methods=['GET'])
@token_required
def my_attendance(current_user):
    if not current_user.employee_id:
        return jsonify({'success': False, 'message': 'No employee linked'}), 404
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    with get_db() as conn:
        q = "SELECT * FROM attendances WHERE employee_id=%s"
        params = [current_user.employee_id]
        if month and year:
            q += " AND EXTRACT(MONTH FROM date)=%s AND EXTRACT(YEAR FROM date)=%s"
            params.extend([month, year])
        q += " ORDER BY date DESC"
        rows = fetch_all(conn, q, tuple(params))
    return jsonify({'success': True, 'data': rows})


@employee_portal_bp.route('/api/employee/my-salaries', methods=['GET'])
@token_required
def my_salaries(current_user):
    if not current_user.employee_id:
        return jsonify({'success': False, 'message': 'No employee linked'}), 404
    with get_db() as conn:
        rows = fetch_all(conn, "SELECT * FROM salaries WHERE employee_id=%s ORDER BY month_year DESC", (current_user.employee_id,))
    return jsonify({'success': True, 'data': rows})


@employee_portal_bp.route('/api/employee/my-leaves', methods=['GET'])
@token_required
def my_leaves(current_user):
    if not current_user.employee_id:
        return jsonify({'success': False, 'message': 'No employee linked'}), 404
    with get_db() as conn:
        rows = fetch_all(conn,
            "SELECT lr.*, lt.name as leave_type_name FROM leave_requests lr "
            "LEFT JOIN leave_types lt ON lr.leave_type_id=lt.id "
            "WHERE lr.employee_id=%s ORDER BY lr.created_at DESC", (current_user.employee_id,))
    return jsonify({'success': True, 'data': rows})


@employee_portal_bp.route('/api/employee/my-transactions', methods=['GET'])
@token_required
def my_transactions(current_user):
    if not current_user.employee_id:
        return jsonify({'success': False, 'message': 'No employee linked'}), 404
    from models import FinancialTransaction
    txs = FinancialTransaction.query.filter_by(employee_id=current_user.employee_id).order_by(FinancialTransaction.date.desc()).all()
    return jsonify({'success': True, 'data': [t.to_dict() for t in txs]})


@employee_portal_bp.route('/api/employee/my-evaluations', methods=['GET'])
@token_required
def my_evaluations(current_user):
    if not current_user.employee_id:
        return jsonify({'success': False, 'message': 'No employee linked'}), 404
    from models import Evaluation
    evals = Evaluation.query.filter_by(employee_id=current_user.employee_id).order_by(Evaluation.date.desc()).all()
    return jsonify({'success': True, 'data': [e.to_dict() for e in evals]})


@employee_portal_bp.route('/api/employee/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    data = request.get_json() or {}
    if not data.get('new_password'):
        return jsonify({'success': False, 'message': 'new_password required'}), 400
    from werkzeug.security import generate_password_hash
    with get_db() as conn:
        from db import execute
        execute(conn, "UPDATE users SET password=%s WHERE id=%s", (generate_password_hash(data['new_password']), current_user.id))
    return jsonify({'success': True, 'message': 'Password changed'})

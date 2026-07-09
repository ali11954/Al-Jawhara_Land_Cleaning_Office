from flask import Blueprint, request, jsonify
from auth import token_required
from db import get_db, fetch_all, execute
from datetime import datetime

leaves_bp = Blueprint('leaves', __name__)


@leaves_bp.route('/api/leave-types', methods=['GET'])
@token_required
def list_leave_types(current_user):
    with get_db() as conn:
        rows = fetch_all(conn, "SELECT * FROM leave_types ORDER BY id")
    return jsonify({'success': True, 'data': rows})


@leaves_bp.route('/api/leave-requests', methods=['GET'])
@token_required
def list_leave_requests(current_user):
    status = request.args.get('status')
    employee_id = request.args.get('employee_id', type=int)
    with get_db() as conn:
        q = ("SELECT lr.*, e.full_name as employee_name, e.code as employee_code, lt.name as leave_type_name, "
             "lr.days as total_days, lr.status as status_name "
             "FROM leave_requests lr LEFT JOIN employees e ON lr.employee_id=e.id "
             "LEFT JOIN leave_types lt ON lr.leave_type_id=lt.id WHERE 1=1")
        params = []
        if status:
            q += " AND lr.status=%s"
            params.append(status)
        if employee_id:
            q += " AND lr.employee_id=%s"
            params.append(employee_id)
        q += " ORDER BY lr.created_at DESC"
        rows = fetch_all(conn, q, tuple(params))
    return jsonify({'success': True, 'data': rows})


@leaves_bp.route('/api/leave-requests', methods=['POST'])
@token_required
def create_leave_request(current_user):
    data = request.get_json()
    if not data or not data.get('employee_id') or not data.get('leave_type_id'):
        return jsonify({'success': False, 'message': 'employee_id and leave_type_id required'}), 400
    with get_db() as conn:
        rid = execute(conn,
            "INSERT INTO leave_requests (employee_id, leave_type_id, start_date, end_date, days, reason, status, created_by) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (data['employee_id'], data['leave_type_id'],
             data.get('start_date', datetime.utcnow().strftime('%Y-%m-%d')),
             data.get('end_date', data.get('start_date', datetime.utcnow().strftime('%Y-%m-%d'))),
             data.get('days', 1), data.get('reason', ''), 'pending', current_user.id))
    return jsonify({'success': True, 'data': {'id': rid}, 'message': 'Leave request created'}), 201


@leaves_bp.route('/api/leave-requests/<int:req_id>/approve', methods=['POST'])
@token_required
def approve_leave(current_user, req_id):
    with get_db() as conn:
        execute(conn, "UPDATE leave_requests SET status='approved', approved_by=%s, approved_at=%s WHERE id=%s",
                (current_user.id, datetime.utcnow().isoformat(), req_id))
    return jsonify({'success': True, 'message': 'Leave request approved'})


@leaves_bp.route('/api/leave-requests/<int:req_id>/reject', methods=['POST'])
@token_required
def reject_leave(current_user, req_id):
    data = request.get_json() or {}
    with get_db() as conn:
        execute(conn, "UPDATE leave_requests SET status='rejected', rejection_reason=%s WHERE id=%s",
                (data.get('rejection_reason', ''), req_id))
    return jsonify({'success': True, 'message': 'Leave request rejected'})


@leaves_bp.route('/api/leave-balances', methods=['GET'])
@token_required
def leave_balances(current_user):
    year = request.args.get('year', datetime.utcnow().year, type=int)
    with get_db() as conn:
        rows = fetch_all(conn, "SELECT * FROM leave_balances WHERE year=%s", (year,))
    return jsonify({'success': True, 'data': rows})

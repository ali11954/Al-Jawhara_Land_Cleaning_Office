from flask import Blueprint, request, jsonify
from auth import token_required
from models import db, Attendance, Employee
from datetime import datetime
from db import get_db, fetch_all, execute

attendance_bp = Blueprint('attendance', __name__)


@attendance_bp.route('/api/attendance', methods=['GET'])
@token_required
def list_attendance(current_user):
    page = request.args.get('page', type=int)
    per_page = request.args.get('per_page', 50, type=int)
    employee_id = request.args.get('employee_id', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    date = request.args.get('date')

    with get_db() as conn:
        q = "SELECT a.* FROM attendance a JOIN employees e ON a.employee_id = e.id WHERE 1=1"
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
            q += " AND a.employee_id = %s"
            params.append(employee_id)
        if date:
            q += " AND a.date = %s"
            params.append(date)
        if date_from:
            q += " AND a.date >= %s"
            params.append(date_from)
        if date_to:
            q += " AND a.date <= %s"
            params.append(date_to)

        q += " ORDER BY a.date DESC"

        if page:
            count_q = q.replace("SELECT a.*", "SELECT COUNT(*)")
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


@attendance_bp.route('/api/attendance', methods=['POST'])
@token_required
def create_attendance(current_user):
    data = request.get_json()
    if not data or not data.get('employee_id') or not data.get('date'):
        return jsonify({'success': False, 'message': 'employee_id and date are required'}), 400

    if current_user.role == 'supervisor':
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT company_id, supervisor_id FROM employees WHERE id = %s", (data['employee_id'],))
            emp = cur.fetchone()
            if not emp:
                return jsonify({'success': False, 'message': 'Employee not found'}), 404
            if current_user.company_id and emp[0] != current_user.company_id:
                return jsonify({'success': False, 'message': 'Access denied'}), 403
            if current_user.employee_id and emp[1] != current_user.employee_id:
                return jsonify({'success': False, 'message': 'Access denied'}), 403

    with get_db() as conn:
        execute(conn,
            "INSERT INTO attendance (employee_id, date, status, notes) VALUES (%s, %s, %s, %s)",
            (data['employee_id'], data['date'], data.get('status', 'present'), data.get('notes', '')))
    return jsonify({'success': True, 'message': 'Attendance recorded'}), 201


@attendance_bp.route('/api/attendance/bulk', methods=['POST'])
@token_required
def bulk_attendance(current_user):
    data = request.get_json()
    if not data or not data.get('records'):
        return jsonify({'success': False, 'message': 'records array required'}), 400
    created = 0
    for rec in data['records']:
        if not rec.get('employee_id') or not rec.get('date'):
            continue
        if current_user.role == 'supervisor':
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("SELECT company_id, supervisor_id FROM employees WHERE id = %s", (rec['employee_id'],))
                emp = cur.fetchone()
                if not emp:
                    continue
                if current_user.company_id and emp[0] != current_user.company_id:
                    continue
                if current_user.employee_id and emp[1] != current_user.employee_id:
                    continue
        with get_db() as conn:
            execute(conn,
                "INSERT INTO attendance (employee_id, date, status, notes) VALUES (%s, %s, %s, %s)",
                (rec['employee_id'], rec['date'], rec.get('status', 'present'), rec.get('notes', '')))
        created += 1
    return jsonify({'success': True, 'data': {'created': created}, 'message': f'{created} records created'}), 201

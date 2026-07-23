from flask import Blueprint, request, jsonify
from auth import token_required
from models import db, Attendance, Employee
from datetime import datetime
from db import get_db, fetch_all, execute

attendance_bp = Blueprint('attendance', __name__)


@attendance_bp.route('/api/attendance', methods=['GET'])
@token_required
def list_attendance(current_user):
    try:
        page = request.args.get('page', type=int)
        per_page = request.args.get('per_page', 50, type=int)
        employee_id = request.args.get('employee_id', type=int)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        date = request.args.get('date')

        with get_db() as conn:
            q = """SELECT a.id, a.employee_id, a.date, a.shift_type, a.status, a.check_in, a.check_out, a.notes, a.created_at, a.updated_at,
                   e.full_name as employee_name, e.code as employee_code,
                   a.status as attendance_status, a.check_in as check_in_time, a.check_out as check_out_time
                   FROM attendance a JOIN employees e ON a.employee_id = e.id WHERE 1=1"""
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
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM attendance a JOIN employees e ON a.employee_id = e.id WHERE 1=1" + q.split("WHERE 1=1")[1].split("ORDER BY")[0], tuple(params))
                total = cur.fetchone()[0]
                offset = (page - 1) * per_page
                q += f" LIMIT {per_page} OFFSET {offset}"
                rows = fetch_all(conn, q, tuple(params))
                pages = (total + per_page - 1) // per_page
                return jsonify({'success': True, 'data': {'items': rows, 'total': total, 'page': page, 'pages': pages}})
            else:
                rows = fetch_all(conn, q, tuple(params))
                return jsonify({'success': True, 'data': rows})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


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
        status = data.get('attendance_status') or data.get('status', 'present')
        execute(conn,
            "INSERT INTO attendance (employee_id, date, shift_type, status, check_in, check_out, notes) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (data['employee_id'], data['date'], data.get('shift_type', 'morning'), status, data.get('time_in') or data.get('check_in'), data.get('time_out') or data.get('check_out'), data.get('notes', '')))
    return jsonify({'success': True, 'message': 'Attendance recorded'}), 201


@attendance_bp.route('/api/attendance/<int:att_id>', methods=['PUT'])
@token_required
def update_attendance(current_user, att_id):
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400

    if current_user.role not in ('admin', 'owner'):
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM attendance WHERE id = %s", (att_id,))
        if not cur.fetchone():
            return jsonify({'success': False, 'message': 'Record not found'}), 404

        fields = []
        params = []
        if 'status' in data or 'attendance_status' in data:
            fields.append("status = %s")
            params.append(data.get('status') or data.get('attendance_status'))
        if 'check_in' in data or 'check_in_time' in data or 'time_in' in data:
            fields.append("check_in = %s")
            params.append(data.get('check_in') or data.get('check_in_time') or data.get('time_in'))
        if 'check_out' in data or 'check_out_time' in data or 'time_out' in data:
            fields.append("check_out = %s")
            params.append(data.get('check_out') or data.get('check_out_time') or data.get('time_out'))
        if 'notes' in data:
            fields.append("notes = %s")
            params.append(data.get('notes', ''))
        if 'shift_type' in data:
            fields.append("shift_type = %s")
            params.append(data.get('shift_type'))

        if not fields:
            return jsonify({'success': False, 'message': 'No fields to update'}), 400

        fields.append("updated_at = NOW()")
        params.append(att_id)
        execute(conn, f"UPDATE attendance SET {', '.join(fields)} WHERE id = %s", tuple(params))

    return jsonify({'success': True, 'message': 'Attendance updated'}), 200


@attendance_bp.route('/api/attendance/bulk', methods=['POST'])
@token_required
def bulk_attendance(current_user):
    data = request.get_json()
    if not data or not data.get('records'):
        return jsonify({'success': False, 'message': 'records array required'}), 400
    created = 0
    bulk_date = data.get('date')
    for rec in data['records']:
        if not rec.get('employee_id'):
            continue
        rec_date = rec.get('date') or bulk_date
        if not rec_date:
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
            status = rec.get('attendance_status') or rec.get('status', 'present')
            execute(conn,
                "INSERT INTO attendance (employee_id, date, shift_type, status, check_in, check_out, notes) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (rec['employee_id'], rec_date, rec.get('shift_type', 'morning'), status, rec.get('time_in') or rec.get('check_in'), rec.get('time_out') or rec.get('check_out'), rec.get('notes', '')))
        created += 1
    return jsonify({'success': True, 'data': {'created': created}, 'message': f'{created} records created'}), 201

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
    query = Attendance.query
    if employee_id:
        query = query.filter_by(employee_id=employee_id)
    if date:
        query = query.filter_by(date=datetime.strptime(date, '%Y-%m-%d').date())
    if date_from:
        query = query.filter(Attendance.date >= date_from)
    if date_to:
        query = query.filter(Attendance.date <= date_to)
    if page:
        pagination = query.order_by(Attendance.date.desc()).paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({'success': True, 'data': {'items': [a.to_dict() for a in pagination.items], 'total': pagination.total, 'page': page, 'pages': pagination.pages}})
    else:
        records = query.order_by(Attendance.date.desc()).all()
        return jsonify({'success': True, 'data': [a.to_dict() for a in records]})


@attendance_bp.route('/api/attendance', methods=['POST'])
@token_required
def create_attendance(current_user):
    data = request.get_json()
    if not data or not data.get('employee_id') or not data.get('date'):
        return jsonify({'success': False, 'message': 'employee_id and date are required'}), 400
    att = Attendance(employee_id=data['employee_id'], date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
                     attendance_type=data.get('attendance_type', 'individual'),
                     attendance_status=data.get('attendance_status', 'present'),
                     late_minutes=data.get('late_minutes', 0), sick_leave=data.get('sick_leave', False),
                     sick_leave_days=data.get('sick_leave_days', 0), annual_leave_days=data.get('annual_leave_days', 0),
                     notes=data.get('notes', ''), created_by=current_user.id)
    db.session.add(att)
    db.session.commit()
    return jsonify({'success': True, 'data': att.to_dict(), 'message': 'Attendance recorded'}), 201


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
        att = Attendance(employee_id=rec['employee_id'], date=datetime.strptime(rec['date'], '%Y-%m-%d').date(),
                         attendance_status=rec.get('attendance_status', 'present'), late_minutes=rec.get('late_minutes', 0),
                         sick_leave=rec.get('sick_leave', False), sick_leave_days=rec.get('sick_leave_days', 0),
                         annual_leave_days=rec.get('annual_leave_days', 0), notes=rec.get('notes', ''),
                         created_by=current_user.id)
        db.session.add(att)
        created += 1
    db.session.commit()
    return jsonify({'success': True, 'data': {'created': created}, 'message': f'{created} records created'}), 201

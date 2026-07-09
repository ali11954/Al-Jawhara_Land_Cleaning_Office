from flask import Blueprint, request, jsonify
from auth import token_required
from models import db, User, Employee, Attendance, Evaluation, Salary
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

profile_bp = Blueprint('profile', __name__)

ROLE_DISPLAY_NAMES = {
    'admin': 'مدير النظام',
    'supervisor': 'مشرف',
    'accountant': 'محاسب',
    'viewer': 'مشاهد',
    'employee': 'موظف',
}


@profile_bp.route('/api/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    user_data = current_user.to_dict()
    user_data['created_at'] = current_user.created_at.strftime('%Y-%m-%d %H:%M') if current_user.created_at else None
    user_data['role_display'] = ROLE_DISPLAY_NAMES.get(current_user.role, current_user.role)

    employee_data = None
    if current_user.employee_id:
        employee = Employee.query.get(current_user.employee_id)
        if employee:
            employee_data = {
                'id': employee.id,
                'code': employee.code,
                'full_name': employee.full_name,
                'phone': employee.phone,
                'address': employee.address,
                'position': employee.position,
                'salary': employee.salary,
                'total_salary': employee.total_salary,
                'daily_allowance': employee.daily_allowance,
                'is_resident': employee.is_resident,
                'worker_type': employee.worker_type,
                'company_name': employee.company.name if employee.company else None,
                'region_name': employee.region_rel.name if employee.region_rel else None,
                'qualification': employee.qualification,
                'specialization': employee.specialization,
                'hire_date': employee.hire_date.strftime('%Y-%m-%d') if employee.hire_date else None,
            }

    return jsonify({
        'success': True,
        'data': {
            **user_data,
            'employee': employee_data,
        }
    })


@profile_bp.route('/api/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400

    for field in ['full_name', 'phone']:
        if field in data:
            setattr(current_user, field, data[field])

    if 'email' in data:
        if data['email'] and data['email'] != '':
            if current_user.employee_id:
                employee = Employee.query.get(current_user.employee_id)
                if employee:
                    employee.email = data['email']

    db.session.commit()
    return jsonify({'success': True, 'message': 'Profile updated', 'data': current_user.to_dict()})


@profile_bp.route('/api/profile/password', methods=['PUT'])
@token_required
def change_password(current_user):
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400

    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    if not old_password or not new_password:
        return jsonify({'success': False, 'message': 'Old and new password required'}), 400

    if len(new_password) < 6:
        return jsonify({'success': False, 'message': 'New password must be at least 6 characters'}), 400

    valid = False
    try:
        valid = check_password_hash(current_user.password, old_password)
    except Exception:
        valid = False

    if not valid:
        return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400

    current_user.password = generate_password_hash(new_password, method='scrypt')
    db.session.commit()
    return jsonify({'success': True, 'message': 'Password changed successfully'})


@profile_bp.route('/api/profile/stats', methods=['GET'])
@token_required
def get_stats(current_user):
    stats = {
        'created_at': current_user.created_at.strftime('%Y-%m-%d %H:%M') if current_user.created_at else None,
        'total_logins': 0,
        'last_login': None,
        'employee': None,
        'attendance': None,
        'evaluations': None,
        'salary': None,
    }

    if current_user.employee_id:
        employee = Employee.query.get(current_user.employee_id)
        if employee:
            stats['employee'] = {
                'position': employee.position,
                'company_name': employee.company.name if employee.company else None,
                'salary': employee.salary,
                'total_salary': employee.total_salary,
                'daily_allowance': employee.daily_allowance,
                'worker_type': employee.worker_type,
                'is_resident': employee.is_resident,
                'hire_date': employee.hire_date.strftime('%Y-%m-%d') if employee.hire_date else None,
                'qualification': employee.qualification,
                'specialization': employee.specialization,
            }

            attendances = Attendance.query.filter_by(employee_id=employee.id).order_by(Attendance.date.desc()).all()
            present_days = sum(1 for a in attendances if a.attendance_status == 'present')
            late_days = sum(1 for a in attendances if a.late_minutes > 0)
            absent_days = sum(1 for a in attendances if a.attendance_status == 'absent')
            sick_days = sum(1 for a in attendances if a.sick_leave)
            leave_days = sum(a.annual_leave_days for a in attendances)

            stats['attendance'] = {
                'total_days': len(attendances),
                'present_days': present_days,
                'late_days': late_days,
                'absent_days': absent_days,
                'sick_days': sick_days,
                'leave_days': leave_days,
            }

            latest_eval = Evaluation.query.filter_by(employee_id=employee.id).order_by(Evaluation.date.desc()).first()
            avg_score = 0
            eval_count = Evaluation.query.filter_by(employee_id=employee.id).count()
            if eval_count > 0:
                scores = [e.score for e in Evaluation.query.filter_by(employee_id=employee.id).all()]
                avg_score = round(sum(scores) / len(scores), 1) if scores else 0

            stats['evaluations'] = {
                'latest_score': latest_eval.score if latest_eval else None,
                'latest_date': latest_eval.date.strftime('%Y-%m-%d') if latest_eval else None,
                'average_score': avg_score,
                'total_evaluations': eval_count,
            }

            total_paid = db.session.query(db.func.sum(Salary.total_salary)).filter_by(
                employee_id=employee.id, is_paid=True
            ).scalar() or 0

            stats['salary'] = {
                'total_paid': total_paid,
                'base_salary': employee.salary,
                'total_salary': employee.total_salary,
            }

    return jsonify({'success': True, 'data': stats})

from flask import Blueprint, request, jsonify
from auth import token_required
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from db import get_db, fetch_all, fetch_one

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
        with get_db() as conn:
            emp = fetch_one(conn, "SELECT * FROM employees WHERE id=%s", (current_user.employee_id,))
        if emp:
            company_name = None
            if emp.get('company_id'):
                with get_db() as conn:
                    co = fetch_one(conn, "SELECT name FROM companies WHERE id=%s", (emp['company_id'],))
                company_name = co['name'] if co else None
            employee_data = {
                'id': emp['id'],
                'code': emp.get('code'),
                'full_name': emp.get('full_name'),
                'phone': emp.get('phone'),
                'address': emp.get('address'),
                'position': emp.get('position'),
                'salary': emp.get('salary'),
                'is_resident': emp.get('is_resident'),
                'company_name': company_name,
                'qualification': emp.get('qualification'),
                'specialization': emp.get('specialization'),
                'hire_date': str(emp['hire_date']) if emp.get('hire_date') else None,
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
        valid = check_password_hash(current_user.password_hash, old_password)
    except Exception:
        valid = False

    if not valid:
        return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400

    current_user.password_hash = generate_password_hash(new_password)
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
        with get_db() as conn:
            emp = fetch_one(conn, "SELECT * FROM employees WHERE id=%s", (current_user.employee_id,))
            if emp:
                company_name = None
                if emp.get('company_id'):
                    co = fetch_one(conn, "SELECT name FROM companies WHERE id=%s", (emp['company_id'],))
                    company_name = co['name'] if co else None

                stats['employee'] = {
                    'position': emp.get('position'),
                    'company_name': company_name,
                    'salary': emp.get('salary'),
                    'is_resident': emp.get('is_resident'),
                    'hire_date': str(emp['hire_date']) if emp.get('hire_date') else None,
                    'qualification': emp.get('qualification'),
                    'specialization': emp.get('specialization'),
                }

                att_rows = fetch_all(conn,
                    "SELECT status FROM attendance WHERE employee_id=%s ORDER BY date DESC",
                    (current_user.employee_id,))
                present_days = sum(1 for a in att_rows if a.get('status') == 'present')
                late_days = sum(1 for a in att_rows if a.get('status') == 'late')
                absent_days = sum(1 for a in att_rows if a.get('status') == 'absent')
                sick_days = sum(1 for a in att_rows if a.get('status') == 'sick')
                leave_days = sum(1 for a in att_rows if a.get('status') in ('annual_leave', 'leave'))

                stats['attendance'] = {
                    'total_days': len(att_rows),
                    'present_days': present_days,
                    'late_days': late_days,
                    'absent_days': absent_days,
                    'sick_days': sick_days,
                    'leave_days': leave_days,
                }

                eval_rows = fetch_all(conn,
                    "SELECT score FROM evaluations WHERE employee_id=%s ORDER BY date DESC",
                    (current_user.employee_id,))
                eval_count = len(eval_rows)
                avg_score = 0
                if eval_count > 0:
                    scores = [e['score'] for e in eval_rows if e.get('score')]
                    avg_score = round(sum(scores) / len(scores), 1) if scores else 0

                latest_eval = eval_rows[0] if eval_rows else None

                stats['evaluations'] = {
                    'latest_score': latest_eval.get('score') if latest_eval else None,
                    'latest_date': None,
                    'average_score': avg_score,
                    'total_evaluations': eval_count,
                }

                sal_row = fetch_one(conn,
                    "SELECT COALESCE(SUM(total_salary), 0) as total_paid FROM salaries WHERE employee_id=%s AND is_paid=true",
                    (current_user.employee_id,))
                total_paid = sal_row['total_paid'] if sal_row else 0

                stats['salary'] = {
                    'total_paid': float(total_paid),
                    'base_salary': emp.get('salary'),
                }

    return jsonify({'success': True, 'data': stats})

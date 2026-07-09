from flask import Blueprint, request, jsonify
from auth import token_required
from models import db, Employee, Attendance, FinancialTransaction, Company, Salary, Evaluation
from sqlalchemy import func
from datetime import datetime, timedelta
from db import get_db, fetch_all

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/api/reports/dashboard', methods=['GET'])
@token_required
def reports_dashboard(current_user):
    with get_db() as conn:
        cur = conn.cursor()

        q = "SELECT COUNT(*) FROM employees WHERE 1=1"
        params = []
        if current_user.role == 'supervisor':
            if current_user.company_id:
                q += " AND company_id = %s"
                params.append(current_user.company_id)
            if current_user.employee_id:
                q += " AND supervisor_id = %s"
                params.append(current_user.employee_id)
        cur.execute(q, tuple(params))
        total_employees = cur.fetchone()[0]

        q2 = q.replace("COUNT(*)", "COUNT(*) FILTER (WHERE is_active = true)")
        cur.execute(q2, tuple(params))
        active_employees = cur.fetchone()[0]

        total_companies = Company.query.count() if current_user.role in ('admin', 'owner') else 1

        q3 = "SELECT COALESCE(SUM(s.total_salary), 0) FROM salaries s JOIN employees e ON s.employee_id = e.id WHERE 1=1"
        params3 = []
        if current_user.role == 'supervisor':
            if current_user.company_id:
                q3 += " AND e.company_id = %s"
                params3.append(current_user.company_id)
            if current_user.employee_id:
                q3 += " AND e.supervisor_id = %s"
                params3.append(current_user.employee_id)
        cur.execute(q3, tuple(params3))
        total_salaries = cur.fetchone()[0]

        today = datetime.utcnow().date()
        q4 = "SELECT COUNT(*) FROM attendance a JOIN employees e ON a.employee_id = e.id WHERE a.date = %s"
        params4 = [today]
        if current_user.role == 'supervisor':
            if current_user.company_id:
                q4 += " AND e.company_id = %s"
                params4.append(current_user.company_id)
            if current_user.employee_id:
                q4 += " AND e.supervisor_id = %s"
                params4.append(current_user.employee_id)
        cur.execute(q4, tuple(params4))
        today_attendance = cur.fetchone()[0]

    return jsonify({
        'success': True,
        'data': {
            'total_employees': total_employees,
            'active_employees': active_employees,
            'total_companies': total_companies,
            'total_salaries': float(total_salaries),
            'today_attendance': today_attendance,
        }
    })


@reports_bp.route('/api/reports/employees', methods=['GET'])
@token_required
def reports_employees(current_user):
    with get_db() as conn:
        cur = conn.cursor()
        q = "SELECT e.id, e.code, e.full_name, e.company_id, c.name as company_name FROM employees e LEFT JOIN companies c ON e.company_id = c.id WHERE e.is_active = true"
        params = []
        if current_user.role == 'supervisor':
            if current_user.company_id:
                q += " AND e.company_id = %s"
                params.append(current_user.company_id)
            if current_user.employee_id:
                q += " AND e.supervisor_id = %s"
                params.append(current_user.employee_id)
        cur.execute(q, tuple(params))
        employees = cur.fetchall()

    by_company = {}
    for emp in employees:
        name = emp[4] or 'بدون شركة'
        if name not in by_company:
            by_company[name] = 0
        by_company[name] += 1

    by_company_list = [{'name': k, 'count': v} for k, v in by_company.items()]

    return jsonify({
        'success': True,
        'data': {
            'total': len(employees),
            'by_company': by_company_list,
        }
    })


@reports_bp.route('/api/reports/attendance', methods=['GET'])
@token_required
def reports_attendance(current_user):
    today = datetime.utcnow().date()
    with get_db() as conn:
        cur = conn.cursor()
        today_str = today.strftime('%Y-%m-%d')
        q = "SELECT a.status FROM attendance a JOIN employees e ON a.employee_id = e.id WHERE a.date = %s"
        params = [today_str]
        if current_user.role == 'supervisor':
            if current_user.company_id:
                q += " AND e.company_id = %s"
                params.append(current_user.company_id)
            if current_user.employee_id:
                q += " AND e.supervisor_id = %s"
                params.append(current_user.employee_id)
        cur.execute(q, tuple(params))
        statuses = [r[0] for r in cur.fetchall()]

        q2 = "SELECT COUNT(*) FROM employees WHERE is_active = true"
        params2 = []
        if current_user.role == 'supervisor':
            if current_user.company_id:
                q2 += " AND company_id = %s"
                params2.append(current_user.company_id)
            if current_user.employee_id:
                q2 += " AND supervisor_id = %s"
                params2.append(current_user.employee_id)
        cur.execute(q2, tuple(params2))
        total_employees = cur.fetchone()[0]

    present = sum(1 for s in statuses if s == 'present')
    late = sum(1 for s in statuses if s == 'late')
    sick = sum(1 for s in statuses if s == 'sick')
    annual_leave = sum(1 for s in statuses if s == 'annual_leave')
    absent = total_employees - len(statuses)

    return jsonify({
        'success': True,
        'data': {
            'summary': {
                'present': present,
                'late': late,
                'absent': absent,
                'sick': sick,
                'annual_leave': annual_leave,
            }
        }
    })


@reports_bp.route('/api/reports/financial', methods=['GET'])
@token_required
def reports_financial(current_user):
    with get_db() as conn:
        cur = conn.cursor()
        q_income = "SELECT COALESCE(SUM(amount), 0) FROM financial_transactions WHERE transaction_type='income'"
        q_expense = "SELECT COALESCE(SUM(amount), 0) FROM financial_transactions WHERE transaction_type='expense'"
        cur.execute(q_income)
        total_income = cur.fetchone()[0]
        cur.execute(q_expense)
        total_expense = cur.fetchone()[0]
    return jsonify({
        'success': True,
        'data': {
            'total_income': float(total_income),
            'total_expense': float(total_expense),
            'net': float(total_income) - float(total_expense),
        }
    })


@reports_bp.route('/api/reports/evaluations', methods=['GET'])
@token_required
def reports_evaluations(current_user):
    with get_db() as conn:
        cur = conn.cursor()
        q = "SELECT ev.score, ev.employee_id, e.full_name FROM evaluations ev JOIN employees e ON ev.employee_id = e.id WHERE 1=1"
        params = []
        if current_user.role == 'supervisor':
            if current_user.company_id:
                q += " AND e.company_id = %s"
                params.append(current_user.company_id)
            if current_user.employee_id:
                q += " AND e.supervisor_id = %s"
                params.append(current_user.employee_id)
        cur.execute(q, tuple(params))
        rows = cur.fetchall()

    if not rows:
        return jsonify({
            'success': True,
            'data': {
                'total_evaluations': 0,
                'avg_score': 0,
                'avg_rating': 'لا توجد تقييمات',
                'top_employees': [],
                'rating_distribution': [],
            }
        })

    total = len(rows)
    avg_score = round(sum(r[0] for r in rows) / total, 1)

    if avg_score >= 9:
        avg_rating = 'ممتاز'
    elif avg_score >= 7:
        avg_rating = 'جيد جداً'
    elif avg_score >= 5:
        avg_rating = 'جيد'
    else:
        avg_rating = 'يحتاج تحسين'

    emp_scores = {}
    for r in rows:
        eid = r[1]
        if eid not in emp_scores:
            emp_scores[eid] = {'scores': [], 'name': r[2]}
        emp_scores[eid]['scores'].append(r[0])

    top_employees = []
    for eid, data in emp_scores.items():
        avg = sum(data['scores']) / len(data['scores'])
        top_employees.append({
            'employee_id': eid,
            'employee_name': data['name'],
            'avg_score': round(avg, 1),
            'evaluation_count': len(data['scores']),
        })
    top_employees.sort(key=lambda x: x['avg_score'], reverse=True)

    excellent = sum(1 for r in rows if r[0] >= 9)
    very_good = sum(1 for r in rows if 7 <= r[0] < 9)
    good = sum(1 for r in rows if 5 <= r[0] < 7)
    needs_improvement = sum(1 for r in rows if r[0] < 5)

    return jsonify({
        'success': True,
        'data': {
            'total_evaluations': total,
            'avg_score': avg_score,
            'avg_rating': avg_rating,
            'top_employees': top_employees[:10],
            'rating_distribution': [
                {'name': 'ممتاز', 'value': excellent},
                {'name': 'جيد جداً', 'value': very_good},
                {'name': 'جيد', 'value': good},
                {'name': 'يحتاج تحسين', 'value': needs_improvement},
            ],
        }
    })

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


@reports_bp.route('/api/reports/attendance-grid', methods=['GET'])
@token_required
def reports_attendance_grid(current_user):
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    company_id = request.args.get('company_id', type=int)

    if not year or not month:
        today = datetime.utcnow().date()
        year = today.year
        month = today.month

    import calendar
    days_in_month = calendar.monthrange(year, month)[1]

    with get_db() as conn:
        cur = conn.cursor()

        q_emp = """SELECT e.id, e.full_name, e.code, e.company_id, COALESCE(c.name, 'بدون شركة') as company_name
                   FROM employees e LEFT JOIN clean_companies c ON e.company_id = c.id
                   WHERE e.is_active = true"""
        params_emp = []
        if current_user.role == 'supervisor':
            if current_user.company_id:
                q_emp += " AND e.company_id = %s"
                params_emp.append(current_user.company_id)
            if current_user.employee_id:
                q_emp += " AND e.supervisor_id = %s"
                params_emp.append(current_user.employee_id)
        if company_id and current_user.role in ('admin', 'owner'):
            q_emp += " AND e.company_id = %s"
            params_emp.append(company_id)
        q_emp += " ORDER BY e.company_id, e.full_name"
        cur.execute(q_emp, tuple(params_emp))
        employees = cur.fetchall()

        date_from = f"{year}-{month:02d}-01"
        date_to = f"{year}-{month:02d}-{days_in_month:02d}"
        cur.execute(
            """SELECT employee_id, EXTRACT(DAY FROM date)::int as day, status
               FROM attendance WHERE date >= %s AND date <= %s""",
            (date_from, date_to))
        att_rows = cur.fetchall()

    att_map = {}
    for emp_id, day, status in att_rows:
        if emp_id not in att_map:
            att_map[emp_id] = {}
        att_map[emp_id][day] = status

    result = []
    for emp in employees:
        emp_id, full_name, code, emp_company_id, company_name = emp
        days = {}
        present_count = 0
        absent_count = 0
        late_count = 0
        leave_count = 0
        for d in range(1, days_in_month + 1):
            status = att_map.get(emp_id, {}).get(d)
            if status:
                days[d] = status
                if status == 'present':
                    present_count += 1
                elif status == 'late':
                    late_count += 1
                elif status in ('annual_leave', 'sick', 'unpaid_leave'):
                    leave_count += 1
            else:
                days[d] = None
                absent_count += 1

        result.append({
            'employee_id': emp_id,
            'employee_name': full_name,
            'employee_code': code,
            'company_id': emp_company_id,
            'company_name': company_name,
            'days': days,
            'present_count': present_count,
            'absent_count': absent_count,
            'late_count': late_count,
            'leave_count': leave_count,
        })

    return jsonify({
        'success': True,
        'data': {
            'year': year,
            'month': month,
            'days_in_month': days_in_month,
            'employees': result,
        }
    })

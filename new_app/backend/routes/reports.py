from flask import Blueprint, request, jsonify
from auth import token_required
from datetime import datetime, timedelta
from db import get_db, fetch_all
import calendar

reports_bp = Blueprint('reports', __name__)


def safe_count(cur, query, params=None):
    try:
        cur.execute(query, params or ())
        return cur.fetchone()[0]
    except Exception:
        return 0


def safe_query(cur, query, params=None):
    try:
        cur.execute(query, params or ())
        return cur.fetchall()
    except Exception:
        return []


@reports_bp.route('/api/reports/dashboard', methods=['GET'])
@token_required
def reports_dashboard(current_user):
    try:
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

            total_companies = safe_count(cur, "SELECT COUNT(*) FROM clean_companies")

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
            total_salaries = cur.fetchone()[0] or 0

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

            work_plans_total = safe_count(cur, "SELECT COUNT(*) FROM work_plans")
            work_plans_pending = safe_count(cur, "SELECT COUNT(*) FROM work_plans WHERE status='pending'")
            work_plans_in_progress = safe_count(cur, "SELECT COUNT(*) FROM work_plans WHERE status='in_progress'")
            work_plans_completed = safe_count(cur, "SELECT COUNT(*) FROM work_plans WHERE status='completed'")
            wp_tasks_total = safe_count(cur, "SELECT COUNT(*) FROM work_plan_tasks")
            wp_tasks_completed = safe_count(cur, "SELECT COUNT(*) FROM work_plan_tasks WHERE status='completed'")

        return jsonify({
            'success': True,
            'data': {
                'total_employees': total_employees,
                'active_employees': active_employees,
                'total_companies': total_companies,
                'total_salaries': float(total_salaries),
                'today_attendance': today_attendance,
                'pending_salaries': 0,
                'work_plans_total': work_plans_total,
                'work_plans_pending': work_plans_pending,
                'work_plans_in_progress': work_plans_in_progress,
                'work_plans_completed': work_plans_completed,
                'work_plan_tasks_total': wp_tasks_total,
                'work_plan_tasks_completed': wp_tasks_completed,
                'active_contracts': 0,
                'pending_transactions': 0,
                'total_income': 0,
                'total_expense': 0,
                'top_employees': [],
                'recent_attendance': [],
                'recent_evaluations': [],
                'recent_transactions': [],
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e), 'data': {
            'total_employees': 0, 'active_employees': 0, 'total_companies': 0,
            'total_salaries': 0, 'today_attendance': 0, 'pending_salaries': 0,
            'work_plans_total': 0, 'work_plans_pending': 0, 'work_plans_in_progress': 0,
            'work_plans_completed': 0, 'work_plan_tasks_total': 0, 'work_plan_tasks_completed': 0,
            'active_contracts': 0, 'pending_transactions': 0, 'total_income': 0, 'total_expense': 0,
            'top_employees': [], 'recent_attendance': [], 'recent_evaluations': [], 'recent_transactions': [],
        }})


@reports_bp.route('/api/reports/employees', methods=['GET'])
@token_required
def reports_employees(current_user):
    try:
        with get_db() as conn:
            cur = conn.cursor()
            q = """SELECT e.id, e.full_name, e.code, e.position, e.salary, e.company_id,
                   COALESCE(c.name, 'بدون شركة') as company_name
                   FROM employees e LEFT JOIN clean_companies c ON e.company_id = c.id
                   WHERE e.is_active = true"""
            params = []
            if current_user.role == 'supervisor':
                if current_user.company_id:
                    q += " AND e.company_id = %s"
                    params.append(current_user.company_id)
                if current_user.employee_id:
                    q += " AND e.supervisor_id = %s"
                    params.append(current_user.employee_id)
            q += " ORDER BY e.company_id, e.full_name"
            cur.execute(q, tuple(params))
            emp_rows = cur.fetchall()

        employees = []
        by_company = {}
        companies_map = {}
        total_salary = 0

        for r in emp_rows:
            eid, name, code, position, salary, cid, cname = r
            salary = float(salary or 0)
            total_salary += salary
            emp_dict = {'id': eid, 'name': name, 'code': code, 'job_title': position, 'salary': salary, 'company_name': cname}
            employees.append(emp_dict)

            if cname not in by_company:
                by_company[cname] = 0
            by_company[cname] += 1

            if cname not in companies_map:
                companies_map[cname] = {'company_name': cname, 'count': 0, 'total_salary': 0, 'employees': []}
            companies_map[cname]['count'] += 1
            companies_map[cname]['total_salary'] += salary
            companies_map[cname]['employees'].append(emp_dict)

        return jsonify({
            'success': True,
            'data': {
                'total': len(employees),
                'total_salary': total_salary,
                'by_company': [{'name': k, 'count': v} for k, v in by_company.items()],
                'employees': employees,
                'companies': list(companies_map.values()),
            }
        })
    except Exception as e:
        return jsonify({'success': True, 'data': {
            'total': 0, 'total_salary': 0, 'by_company': [], 'employees': [], 'companies': [],
        }})


@reports_bp.route('/api/reports/attendance', methods=['GET'])
@token_required
def reports_attendance(current_user):
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    today = datetime.utcnow().date()
    if not date_from:
        date_from = today.strftime('%Y-%m-01')
    if not date_to:
        date_to = today.strftime('%Y-%m-%d')

    with get_db() as conn:
        cur = conn.cursor()

        q = """SELECT a.date, a.status, e.id as emp_id, e.company_id
               FROM attendance a JOIN employees e ON a.employee_id = e.id
               WHERE a.date >= %s AND a.date <= %s"""
        params = [date_from, date_to]
        if current_user.role == 'supervisor':
            if current_user.company_id:
                q += " AND e.company_id = %s"
                params.append(current_user.company_id)
            if current_user.employee_id:
                q += " AND e.supervisor_id = %s"
                params.append(current_user.employee_id)
        q += " ORDER BY a.date"
        cur.execute(q, tuple(params))
        att_rows = cur.fetchall()

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

    daily = {}
    all_statuses = []
    for row in att_rows:
        dt, status, emp_id, comp_id = row
        dt_str = dt.strftime('%Y-%m-%d') if hasattr(dt, 'strftime') else str(dt)
        all_statuses.append(status)
        if dt_str not in daily:
            daily[dt_str] = {'date': dt_str, 'present': 0, 'late': 0, 'absent': 0, 'sick': 0, 'annual_leave': 0, 'total': 0}
        daily[dt_str]['total'] += 1
        if status in daily[dt_str]:
            daily[dt_str][status] += 1

    daily_list = list(daily.values())

    present = sum(1 for s in all_statuses if s == 'present')
    late = sum(1 for s in all_statuses if s == 'late')
    sick = sum(1 for s in all_statuses if s == 'sick')
    annual_leave = sum(1 for s in all_statuses if s == 'annual_leave')
    absent = max(0, total_employees * len(daily_list) - len(all_statuses))

    total_records = len(all_statuses)
    rate = round((present + late) / total_records * 100, 1) if total_records > 0 else 0

    return jsonify({
        'success': True,
        'data': {
            'summary': {
                'present': present,
                'late': late,
                'absent': absent,
                'sick': sick,
                'annual_leave': annual_leave,
            },
            'daily': daily_list,
            'attendance_rate': rate,
            'period': f'{date_from} إلى {date_to}',
            'companies': [],
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

        by_type = safe_query(cur, """SELECT transaction_type, COALESCE(SUM(amount), 0) as total
                     FROM financial_transactions GROUP BY transaction_type""")
        by_type = [{'type': r[0], 'total': float(r[1])} for r in by_type]

        monthly_raw = safe_query(cur, """SELECT to_char(date_trunc('month', date), 'YYYY-MM') as month,
                       SUM(CASE WHEN transaction_type='income' THEN amount ELSE 0 END) as income,
                       SUM(CASE WHEN transaction_type='expense' THEN amount ELSE 0 END) as expense
                       FROM financial_transactions
                       GROUP BY 1 ORDER BY 1 DESC LIMIT 12""")
        month_names = ['يناير','فبراير','مارس','أبريل','مايو','يونيو','يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر']
        monthly = []
        for r in monthly_raw:
            y, m = r[0].split('-')
            month_label = f"{month_names[int(m)-1]} {y}"
            monthly.append({'month': month_label, 'income': float(r[1]), 'expense': float(r[2])})

    return jsonify({
        'success': True,
        'data': {
            'total_income': float(total_income),
            'total_expense': float(total_expense),
            'balance': float(total_income) - float(total_expense),
            'net': float(total_income) - float(total_expense),
            'by_type': by_type,
            'monthly': list(reversed(monthly)),
            'companies': [],
        }
    })


@reports_bp.route('/api/reports/evaluations', methods=['GET'])
@token_required
def reports_evaluations(current_user):
    month_year = request.args.get('month_year')

    try:
        with get_db() as conn:
            cur = conn.cursor()
            q = """SELECT ev.id, ev.score, ev.employee_id, ev.evaluation_type,
                   CAST(ev.date AS TEXT) as eval_date,
                   CAST(ev.created_at AS TEXT) as eval_created,
                   e.full_name, e.position, e.company_id,
                   COALESCE(c.name, '') as company_name
                   FROM evaluations ev JOIN employees e ON ev.employee_id = e.id
                   LEFT JOIN clean_companies c ON e.company_id = c.id
                   WHERE 1=1"""
            params = []
            if month_year:
                q += " AND CAST(ev.date AS TEXT) LIKE %s"
                params.append(f'{month_year}%')
            if current_user.role == 'supervisor':
                if current_user.company_id:
                    q += " AND e.company_id = %s"
                    params.append(current_user.company_id)
                if current_user.employee_id:
                    q += " AND e.supervisor_id = %s"
                    params.append(current_user.employee_id)
            q += " ORDER BY ev.date DESC"
            cur.execute(q, tuple(params))
            rows = cur.fetchall()
    except Exception as e:
        rows = []

    if not rows:
        return jsonify({
            'success': True,
            'data': {
                'total_evaluations': 0,
                'avg_score': 0,
                'avg_rating': 'لا توجد تقييمات',
                'top_employees': [],
                'rating_distribution': [],
                'type_distribution': [],
                'monthly_trend': [],
                'all_employees': [],
                'companies': [],
            }
        })

    total = len(rows)
    avg_score = round(sum(r[1] for r in rows) / total, 1)

    def get_rating(score):
        if score >= 90: return 'ممتاز'
        if score >= 70: return 'جيد جداً'
        if score >= 50: return 'جيد'
        if score >= 30: return 'مقبول'
        return 'ضعيف'

    avg_rating = get_rating(avg_score)

    emp_scores = {}
    for r in rows:
        eid, score, _, eval_type, eval_date, eval_created, name, position, cid, cname = r
        if eid not in emp_scores:
            emp_scores[eid] = {'scores': [], 'name': name, 'job_title': position, 'company_name': cname, 'eval_count': 0}
        emp_scores[eid]['scores'].append(score)
        emp_scores[eid]['eval_count'] += 1

    all_employees = []
    for eid, data in emp_scores.items():
        avg = round(sum(data['scores']) / len(data['scores']), 1)
        all_employees.append({
            'employee_id': eid,
            'name': data['name'],
            'job_title': data['job_title'],
            'company_name': data['company_name'],
            'avg_score': avg,
            'eval_count': data['eval_count'],
            'rating': get_rating(avg),
        })
    all_employees.sort(key=lambda x: x['avg_score'], reverse=True)

    top_employees = all_employees[:10]

    excellent = sum(1 for r in rows if r[1] >= 90)
    very_good = sum(1 for r in rows if 70 <= r[1] < 90)
    good = sum(1 for r in rows if 50 <= r[1] < 70)
    acceptable = sum(1 for r in rows if 30 <= r[1] < 50)
    weak = sum(1 for r in rows if r[1] < 30)

    type_supervisor = sum(1 for r in rows if r[3] == 'supervisor')
    type_contractor = sum(1 for r in rows if r[3] == 'contractor')

    monthly_trend = []
    month_data = {}
    for r in rows:
        eval_date = r[4]
        dt_str = str(eval_date)[:7] if eval_date else ''
        if dt_str not in month_data:
            month_data[dt_str] = {'scores': [], 'count': 0}
        month_data[dt_str]['scores'].append(r[1])
        month_data[dt_str]['count'] += 1
    month_names = ['يناير','فبراير','مارس','أبريل','مايو','يونيو','يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر']
    for ym in sorted(month_data.keys()):
        y, m = ym.split('-')
        month_label = f"{month_names[int(m)-1]} {y}"
        d = month_data[ym]
        monthly_trend.append({'month': month_label, 'avg': round(sum(d['scores'])/len(d['scores']), 1), 'count': d['count']})

    companies_data = {}
    for r in rows:
        cname = r[9] or 'بدون شركة' if len(r) > 9 else 'بدون شركة'
        if cname not in companies_data:
            companies_data[cname] = {'scores': [], 'count': 0}
        companies_data[cname]['scores'].append(r[1])
        companies_data[cname]['count'] += 1
    companies_list = []
    for cname, d in companies_data.items():
        avg = round(sum(d['scores']) / len(d['scores']), 1)
        companies_list.append({
            'company_name': cname,
            'total_evaluations': d['count'],
            'avg_score': avg,
            'avg_rating': get_rating(avg),
        })

    return jsonify({
        'success': True,
        'data': {
            'total_evaluations': total,
            'avg_score': avg_score,
            'avg_rating': avg_rating,
            'top_employees': top_employees,
            'all_employees': all_employees,
            'rating_distribution': [
                {'name': 'ممتاز', 'value': excellent},
                {'name': 'جيد جداً', 'value': very_good},
                {'name': 'جيد', 'value': good},
                {'name': 'مقبول', 'value': acceptable},
                {'name': 'ضعيف', 'value': weak},
            ],
            'type_distribution': [
                {'name': 'تقييم مشرف', 'value': type_supervisor},
                {'name': 'تقييم متعهد', 'value': type_contractor},
            ],
            'monthly_trend': monthly_trend,
            'companies': companies_list,
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


@reports_bp.route('/api/reports/attendance-detail', methods=['GET'])
@token_required
def reports_attendance_detail(current_user):
    company_id = request.args.get('company_id', type=int)
    employee_id = request.args.get('employee_id', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    today = datetime.utcnow().date()
    if not date_from:
        date_from = today.strftime('%Y-%m-01')
    if not date_to:
        date_to = today.strftime('%Y-%m-%d')

    with get_db() as conn:
        cur = conn.cursor()

        q = """SELECT a.id, a.employee_id, CAST(a.date AS TEXT) as att_date, a.status,
               a.shift_type, a.check_in, a.check_out, a.notes,
               e.full_name, e.code, e.position,
               e.company_id, COALESCE(c.name, 'بدون شركة') as company_name
               FROM attendance a JOIN employees e ON a.employee_id = e.id
               LEFT JOIN clean_companies c ON e.company_id = c.id
               WHERE a.date >= %s AND a.date <= %s AND e.is_active = true"""
        params = [date_from, date_to]

        if current_user.role == 'supervisor':
            if current_user.company_id:
                q += " AND e.company_id = %s"
                params.append(current_user.company_id)
            if current_user.employee_id:
                q += " AND e.supervisor_id = %s"
                params.append(current_user.employee_id)
        if company_id and current_user.role in ('admin', 'owner'):
            q += " AND e.company_id = %s"
            params.append(company_id)
        if employee_id:
            q += " AND a.employee_id = %s"
            params.append(employee_id)

        q += " ORDER BY a.date DESC, e.company_id, e.full_name"
        cur.execute(q, tuple(params))
        rows = cur.fetchall()

        emp_q = """SELECT e.id, e.full_name, e.code, e.company_id,
                   COALESCE(c.name, 'بدون شركة') as company_name
                   FROM employees e LEFT JOIN clean_companies c ON e.company_id = c.id
                   WHERE e.is_active = true"""
        emp_params = []
        if current_user.role == 'supervisor':
            if current_user.company_id:
                emp_q += " AND e.company_id = %s"
                emp_params.append(current_user.company_id)
        if company_id and current_user.role in ('admin', 'owner'):
            emp_q += " AND e.company_id = %s"
            emp_params.append(company_id)
        if employee_id:
            emp_q += " AND e.id = %s"
            emp_params.append(employee_id)
        emp_q += " ORDER BY e.full_name"
        cur.execute(emp_q, tuple(emp_params))
        all_emps = cur.fetchall()

    records = []
    for r in rows:
        records.append({
            'id': r[0],
            'employee_id': r[1],
            'date': r[2],
            'status': r[3],
            'shift_type': r[4],
            'check_in': str(r[5]) if r[5] else None,
            'check_out': str(r[6]) if r[6] else None,
            'notes': r[7] or '',
            'employee_name': r[8],
            'employee_code': r[9],
            'position': r[10],
            'company_id': r[11],
            'company_name': r[12],
        })

    status_map = {'present': 'حاضر', 'late': 'متأخر', 'absent': 'غائب', 'sick': 'مرضي',
                  'annual_leave': 'إجازة', 'unpaid_leave': 'إجازة بدون راتب'}

    employees_summary = {}
    for emp in all_emps:
        eid, name, code, cid, cname = emp
        employees_summary[eid] = {
            'employee_id': eid, 'employee_name': name, 'employee_code': code,
            'company_id': cid, 'company_name': cname,
            'total_days': 0, 'present': 0, 'late': 0, 'absent': 0, 'sick': 0, 'leave': 0,
        }

    for rec in records:
        eid = rec['employee_id']
        if eid in employees_summary:
            employees_summary[eid]['total_days'] += 1
            s = rec['status']
            if s == 'present':
                employees_summary[eid]['present'] += 1
            elif s == 'late':
                employees_summary[eid]['late'] += 1
            elif s in ('annual_leave', 'unpaid_leave'):
                employees_summary[eid]['leave'] += 1
            elif s == 'sick':
                employees_summary[eid]['sick'] += 1

    companies_summary = {}
    for emp in employees_summary.values():
        cn = emp['company_name']
        if cn not in companies_summary:
            companies_summary[cn] = {'company_name': cn, 'employee_count': 0, 'total_present': 0, 'total_late': 0, 'total_absent': 0, 'total_leave': 0}
        companies_summary[cn]['employee_count'] += 1
        companies_summary[cn]['total_present'] += emp['present']
        companies_summary[cn]['total_late'] += emp['late']
        companies_summary[cn]['total_leave'] += emp['leave']

    total_present = sum(e['present'] for e in employees_summary.values())
    total_late = sum(e['late'] for e in employees_summary.values())
    total_leave = sum(e['leave'] for e in employees_summary.values())
    total_records = len(records)

    return jsonify({
        'success': True,
        'data': {
            'date_from': date_from,
            'date_to': date_to,
            'total_records': total_records,
            'total_employees': len(all_emps),
            'summary': {
                'total_present': total_present,
                'total_late': total_late,
                'total_leave': total_leave,
                'attendance_rate': round((total_present + total_late) / total_records * 100, 1) if total_records > 0 else 0,
            },
            'employees_summary': list(employees_summary.values()),
            'companies_summary': list(companies_summary.values()),
            'records': records,
            'status_map': status_map,
        }
    })


@reports_bp.route('/api/reports/contractor-profit', methods=['GET'])
@token_required
def reports_contractor_profit(current_user):
    return jsonify({
        'success': True,
        'data': {
            'employees': [],
            'summary': {},
        }
    })

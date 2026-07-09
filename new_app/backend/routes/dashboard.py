from flask import Blueprint, jsonify
from auth import token_required
from db import get_db
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/api/dashboard/stats', methods=['GET'])
@token_required
def dashboard_stats(current_user):
    today = datetime.utcnow().date()
    today_str = today.strftime('%Y-%m-%d')

    with get_db() as conn:
        cur = conn.cursor()

        if current_user.role == 'supervisor':
            # Total employees
            if current_user.company_id and current_user.employee_id:
                cur.execute("SELECT COUNT(*) FROM employees WHERE is_active = true AND company_id = %s AND supervisor_id = %s",
                            (current_user.company_id, current_user.employee_id))
            elif current_user.company_id:
                cur.execute("SELECT COUNT(*) FROM employees WHERE is_active = true AND company_id = %s",
                            (current_user.company_id,))
            else:
                cur.execute("SELECT COUNT(*) FROM employees WHERE is_active = true")
            total_employees = cur.fetchone()[0]

            # Today's attendance
            att_params = [today_str]
            att_where = ""
            if current_user.company_id:
                att_where += " AND e.company_id = %s"
                att_params.append(current_user.company_id)
            if current_user.employee_id:
                att_where += " AND e.supervisor_id = %s"
                att_params.append(current_user.employee_id)

            cur.execute(f"SELECT a.status FROM attendance a JOIN employees e ON a.employee_id = e.id WHERE a.date = %s{att_where}", tuple(att_params))
            today_statuses = [r[0] for r in cur.fetchall()]

            # Companies & suppliers
            total_companies = 1
            cur.execute("SELECT COUNT(*) FROM suppliers")
            total_suppliers = cur.fetchone()[0]

            # Salaries
            sal_params = []
            sal_where = ""
            if current_user.company_id:
                sal_where += " AND e.company_id = %s"
                sal_params.append(current_user.company_id)
            if current_user.employee_id:
                sal_where += " AND e.supervisor_id = %s"
                sal_params.append(current_user.employee_id)

            cur.execute(f"SELECT COALESCE(SUM(s.total_salary), 0) FROM salaries s JOIN employees e ON s.employee_id = e.id WHERE s.is_paid = true{sal_where}", tuple(sal_params))
            total_salaries_paid = cur.fetchone()[0]

            cur.execute(f"SELECT COALESCE(SUM(s.total_salary), 0) FROM salaries s JOIN employees e ON s.employee_id = e.id WHERE s.is_paid = false{sal_where}", tuple(sal_params))
            total_salaries_unpaid = cur.fetchone()[0]

            cur.execute(f"SELECT COUNT(*) FROM salaries s JOIN employees e ON s.employee_id = e.id WHERE s.is_paid = false{sal_where}", tuple(sal_params))
            pending_salaries = cur.fetchone()[0]

            # Financial
            fin_params = []
            fin_where = ""
            if current_user.company_id:
                fin_where += " AND e.company_id = %s"
                fin_params.append(current_user.company_id)
            if current_user.employee_id:
                fin_where += " AND e.supervisor_id = %s"
                fin_params.append(current_user.employee_id)

            cur.execute(f"SELECT COALESCE(SUM(ft.amount), 0) FROM financial_transactions ft JOIN employees e ON ft.employee_id = e.id WHERE ft.transaction_type = 'income'{fin_where}", tuple(fin_params))
            total_income = cur.fetchone()[0]

            cur.execute(f"SELECT COALESCE(SUM(ft.amount), 0) FROM financial_transactions ft JOIN employees e ON ft.employee_id = e.id WHERE ft.transaction_type = 'expense'{fin_where}", tuple(fin_params))
            total_expense = cur.fetchone()[0]

            cur.execute(f"SELECT COUNT(*) FROM financial_transactions ft JOIN employees e ON ft.employee_id = e.id WHERE ft.is_settled = false{fin_where}", tuple(fin_params))
            pending_transactions = cur.fetchone()[0]

            today_attendance = sum(1 for s in today_statuses if s == 'present')
            late_count = sum(1 for s in today_statuses if s == 'late')
            absent_count = total_employees - len(today_statuses)

        else:
            # Owner/admin - no filters
            cur.execute("SELECT COUNT(*) FROM employees WHERE is_active = true")
            total_employees = cur.fetchone()[0]

            cur.execute("SELECT a.status FROM attendance a WHERE a.date = %s", (today_str,))
            today_statuses = [r[0] for r in cur.fetchall()]
            today_attendance = sum(1 for s in today_statuses if s == 'present')
            late_count = sum(1 for s in today_statuses if s == 'late')
            absent_count = total_employees - len(today_statuses)

            cur.execute("SELECT COUNT(*) FROM companies")
            total_companies = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM suppliers")
            total_suppliers = cur.fetchone()[0]

            cur.execute("SELECT COALESCE(SUM(total_salary), 0) FROM salaries WHERE is_paid = true")
            total_salaries_paid = cur.fetchone()[0]
            cur.execute("SELECT COALESCE(SUM(total_salary), 0) FROM salaries WHERE is_paid = false")
            total_salaries_unpaid = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM salaries WHERE is_paid = false")
            pending_salaries = cur.fetchone()[0]

            cur.execute("SELECT COALESCE(SUM(amount), 0) FROM financial_transactions WHERE transaction_type = 'income'")
            total_income = cur.fetchone()[0]
            cur.execute("SELECT COALESCE(SUM(amount), 0) FROM financial_transactions WHERE transaction_type = 'expense'")
            total_expense = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM financial_transactions WHERE is_settled = false")
            pending_transactions = cur.fetchone()[0]

    return jsonify({
        'success': True,
        'data': {
            'total_employees': total_employees,
            'today_attendance': today_attendance,
            'late_count': late_count,
            'absent_count': absent_count,
            'total_companies': total_companies,
            'total_suppliers': total_suppliers,
            'total_salaries_paid': float(total_salaries_paid),
            'total_salaries_unpaid': float(total_salaries_unpaid),
            'pending_salaries': pending_salaries,
            'pending_transactions': pending_transactions,
            'total_income': float(total_income),
            'total_expense': float(total_expense),
            'balance': float(total_income) - float(total_expense),
        }
    })

from flask import Blueprint, jsonify
from auth import token_required
from models import db, Employee, Attendance, FinancialTransaction, Company, Supplier, Salary, Evaluation, Account, Contract, Invoice
from sqlalchemy import func
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/api/dashboard/stats', methods=['GET'])
@token_required
def dashboard_stats(current_user):
    today = datetime.utcnow().date()

    # Employee counts
    total_employees = Employee.query.filter_by(is_active=True).count()

    # Today's attendance
    today_records = Attendance.query.filter_by(date=today).all()
    today_attendance = sum(1 for r in today_records if r.attendance_status == 'present')
    late_count = sum(1 for r in today_records if r.attendance_status == 'late')
    absent_count = Employee.query.filter_by(is_active=True).count() - len(today_records)
    sick_count = sum(1 for r in today_records if r.sick_leave)
    leave_count = sum(1 for r in today_records if r.attendance_status == 'annual_leave')

    # Companies & suppliers
    total_companies = Company.query.count()
    total_suppliers = Supplier.query.count()

    # Salaries
    total_salaries_paid = db.session.query(
        func.coalesce(func.sum(Salary.total_salary), 0)
    ).filter_by(is_paid=True).scalar()

    total_salaries_unpaid = db.session.query(
        func.coalesce(func.sum(Salary.total_salary), 0)
    ).filter_by(is_paid=False).scalar()

    pending_salaries = Salary.query.filter_by(is_paid=False).count()

    # Financial
    total_income = db.session.query(
        func.coalesce(func.sum(FinancialTransaction.amount), 0)
    ).filter(FinancialTransaction.transaction_type == 'income').scalar()

    total_expense = db.session.query(
        func.coalesce(func.sum(FinancialTransaction.amount), 0)
    ).filter(FinancialTransaction.transaction_type == 'expense').scalar()

    pending_transactions = FinancialTransaction.query.filter_by(is_settled=False).count()

    # Work plans (placeholder - set to 0 if no work_plans table)
    work_plans_total = 0
    work_plans_pending = 0
    work_plans_in_progress = 0
    work_plans_completed = 0
    work_plan_tasks_total = 0
    work_plan_tasks_completed = 0

    try:
        from models import WorkPlan
        work_plans_total = WorkPlan.query.count()
        work_plans_pending = WorkPlan.query.filter_by(status='pending').count()
        work_plans_in_progress = WorkPlan.query.filter_by(status='in_progress').count()
        work_plans_completed = WorkPlan.query.filter_by(status='completed').count()
    except ImportError:
        pass

    return jsonify({
        'success': True,
        'data': {
            'total_employees': total_employees,
            'today_attendance': today_attendance,
            'late_count': late_count,
            'absent_count': absent_count,
            'sick_count': sick_count,
            'leave_count': leave_count,
            'total_companies': total_companies,
            'total_suppliers': total_suppliers,
            'total_salaries_paid': float(total_salaries_paid),
            'total_salaries_unpaid': float(total_salaries_unpaid),
            'pending_salaries': pending_salaries,
            'pending_transactions': pending_transactions,
            'total_income': float(total_income),
            'total_expense': float(total_expense),
            'balance': float(total_income) - float(total_expense),
            'work_plans_total': work_plans_total,
            'work_plans_pending': work_plans_pending,
            'work_plans_in_progress': work_plans_in_progress,
            'work_plans_completed': work_plans_completed,
            'work_plan_tasks_total': work_plan_tasks_total,
            'work_plan_tasks_completed': work_plan_tasks_completed,
        }
    })

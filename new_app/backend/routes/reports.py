from flask import Blueprint, request, jsonify
from auth import token_required
from models import db, Employee, Attendance, FinancialTransaction, Company, Salary, Evaluation
from sqlalchemy import func
from datetime import datetime, timedelta

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/api/reports/dashboard', methods=['GET'])
@token_required
def reports_dashboard(current_user):
    total_employees = Employee.query.count()
    active_employees = Employee.query.filter_by(is_active=True).count()
    total_companies = Company.query.count()
    total_salaries = db.session.query(func.coalesce(func.sum(Salary.total_salary), 0)).scalar()

    today = datetime.utcnow().date()
    today_attendance = Attendance.query.filter_by(date=today).count()

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
    employees = Employee.query.filter_by(is_active=True).all()

    by_company = {}
    for emp in employees:
        name = emp.company.name if emp.company else 'بدون شركة'
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
    records = Attendance.query.filter_by(date=today).all()

    present = sum(1 for r in records if r.attendance_status == 'present')
    late = sum(1 for r in records if r.attendance_status == 'late')
    sick = sum(1 for r in records if r.sick_leave)
    annual_leave = sum(1 for r in records if r.attendance_status == 'annual_leave')
    absent = Employee.query.filter_by(is_active=True).count() - len(records)

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


@reports_bp.route('/api/reports/evaluations', methods=['GET'])
@token_required
def reports_evaluations(current_user):
    evaluations = Evaluation.query.all()

    if not evaluations:
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

    total = len(evaluations)
    avg_score = round(sum(e.score for e in evaluations) / total, 1)

    if avg_score >= 9:
        avg_rating = 'ممتاز'
    elif avg_score >= 7:
        avg_rating = 'جيد جداً'
    elif avg_score >= 5:
        avg_rating = 'جيد'
    else:
        avg_rating = 'يحتاج تحسين'

    # Top employees by average score
    emp_scores = {}
    for e in evaluations:
        eid = e.employee_id
        if eid not in emp_scores:
            emp_scores[eid] = {'scores': [], 'name': e.employee.full_name if e.employee else ''}
        emp_scores[eid]['scores'].append(e.score)

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

    # Rating distribution
    excellent = sum(1 for e in evaluations if e.score >= 9)
    very_good = sum(1 for e in evaluations if 7 <= e.score < 9)
    good = sum(1 for e in evaluations if 5 <= e.score < 7)
    needs_improvement = sum(1 for e in evaluations if e.score < 5)

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

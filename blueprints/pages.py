from flask import Blueprint, render_template
from flask_login import login_required, current_user
from utils import role_required

pages = Blueprint('pages', __name__)


@pages.route('/employees')
@login_required
def employees_list():
    return render_template('pages/employees.html')


@pages.route('/attendance')
@login_required
def attendance_list():
    return render_template('pages/attendance.html')


@pages.route('/evaluations')
@login_required
def evaluations_list():
    return render_template('pages/evaluations.html')


@pages.route('/companies')
@login_required
def companies_dashboard():
    return render_template('pages/companies.html')


@pages.route('/contracts')
@login_required
def contracts_list():
    return render_template('pages/contracts.html')


@pages.route('/invoices')
@login_required
def invoices_list():
    return render_template('pages/invoices.html')


@pages.route('/financial')
@login_required
def financial_dashboard():
    return render_template('pages/financial.html')


@pages.route('/accounts')
@login_required
def accounts_dashboard():
    return render_template('pages/accounts.html')


@pages.route('/suppliers')
@login_required
def suppliers_list():
    return render_template('pages/suppliers.html')


@pages.route('/reports')
@login_required
def reports_dashboard():
    return render_template('pages/reports.html')


@pages.route('/settings')
@login_required
@role_required('admin')
def system_settings_all():
    return render_template('pages/settings.html')

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from models import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}})

    db.init_app(app)

    from auth import auth_bp
    from routes.employees import employees_bp
    from routes.attendance import attendance_bp
    from routes.evaluations import evaluations_bp
    from routes.companies import companies_bp
    from routes.contracts import contracts_bp
    from routes.invoices import invoices_bp
    from routes.financial import financial_bp
    from routes.accounts import accounts_bp
    from routes.suppliers import suppliers_bp
    from routes.reports import reports_bp
    from routes.users import users_bp
    from routes.profile import profile_bp
    from routes.dashboard import dashboard_bp
    from routes.regions import regions_bp
    from routes.evaluation_criteria import eval_criteria_bp
    from routes.leaves import leaves_bp
    from routes.periods import periods_bp
    from routes.work_plans import work_plans_bp
    from routes.supplier_invoices import supplier_invoices_bp
    from routes.settings import settings_bp
    from routes.employee_portal import employee_portal_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(evaluations_bp)
    app.register_blueprint(companies_bp)
    app.register_blueprint(contracts_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(financial_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(suppliers_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(regions_bp)
    app.register_blueprint(eval_criteria_bp)
    app.register_blueprint(leaves_bp)
    app.register_blueprint(periods_bp)
    app.register_blueprint(work_plans_bp)
    app.register_blueprint(supplier_invoices_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(employee_portal_bp)

    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({'success': True, 'message': 'Al-Jawhara Land API is running'})

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'success': False, 'message': 'Resource not found'}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

    return app


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=False)

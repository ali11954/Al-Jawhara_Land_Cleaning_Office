"""
Cleaning Company Management System - New App
Backend API + Modern SPA Frontend
"""
import os
from datetime import datetime

from flask import Flask, send_from_directory, redirect, url_for, request, jsonify
from flask_login import LoginManager, current_user

from config import Config
from models import db, User

login_manager = LoginManager()


def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config.from_object(Config)

    # Init
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth_login'

    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import request as req
        if req.path.startswith('/api/'):
            return {'status': 'fail', 'message': 'Unauthorized'}, 401
        return redirect('/')

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ── Register API Blueprint ──
    from backend.endpoints import api as api_bp
    app.register_blueprint(api_bp)

    @app.route('/auth/login', methods=['GET', 'POST'])
    def auth_login():
        from flask_login import login_user

        if request.method == 'POST':
            if request.is_json:
                d = request.json
                username = d.get('username', '').strip()
                password = d.get('password', '')
            else:
                username = request.form.get('username', '').strip()
                password = request.form.get('password', '')

            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password) and user.is_active:
                login_user(user, remember=True)
                if request.is_json:
                    return jsonify({'status': 'ok', 'message': 'تم تسجيل الدخول'})
                return redirect('/')
            else:
                if request.is_json:
                    return jsonify({'status': 'fail', 'message': 'بيانات الدخول غير صحيحة'}), 401
                return redirect('/')
        return redirect('/')

    @app.route('/auth/logout')
    def auth_logout():
        logout_user()
        return redirect('/')

    # ── Serve Frontend ──
    @app.route('/')
    def index():
        return send_from_directory('frontend', 'index.html')

    @app.route('/login')
    def login_page():
        return send_from_directory('frontend', 'index.html')

    # ── Catch-all: serve SPA for any non-API route ──
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return {'status': 'fail', 'message': 'Not found'}, 404
        return send_from_directory('frontend', 'index.html')

    return app


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='owner').first():
            owner = User(username='owner', email='owner@cleaning.com', role='owner', is_active=True)
            owner.set_password('admin123')
            db.session.add(owner)
            db.session.commit()

    print("=" * 50)
    print("  Cleaning Company Management System")
    print("  Backend API: /api/v1/*")
    print("  Frontend:    http://127.0.0.1:9000")
    print("  Login:       owner / admin123")
    print("=" * 50)
    app.run(host='0.0.0.0', port=9000, debug=True)

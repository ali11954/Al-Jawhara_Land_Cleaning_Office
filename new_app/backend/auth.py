import jwt
import datetime
from functools import wraps
from flask import request, jsonify, Blueprint
from werkzeug.security import check_password_hash
from models import db, User

auth_bp = Blueprint('auth', __name__)

def get_jwt_secret():
    from flask import current_app
    return current_app.config['SECRET_KEY']

def create_token(user_id, role):
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        'iat': datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm='HS256')


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        if not token:
            return jsonify({'success': False, 'message': 'Token is missing'}), 401
        try:
            data = jwt.decode(token, get_jwt_secret(), algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user or not current_user.is_active:
                return jsonify({'success': False, 'message': 'Invalid or inactive user'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Invalid token'}), 401
        return f(current_user, *args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        if not token:
            return jsonify({'success': False, 'message': 'Token is missing'}), 401
        try:
            data = jwt.decode(token, get_jwt_secret(), algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user or not current_user.is_active:
                return jsonify({'success': False, 'message': 'Invalid or inactive user'}), 401
            if current_user.role != 'admin':
                return jsonify({'success': False, 'message': 'Admin access required'}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Invalid token'}), 401
        return f(current_user, *args, **kwargs)
    return decorated


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'success': False, 'message': 'Username and password required'}), 400

    user = User.query.filter_by(username=data['username']).first()
    if not user:
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

    if not user.is_active:
        return jsonify({'success': False, 'message': 'Account is deactivated'}), 401

    password_valid = False
    try:
        password_valid = check_password_hash(user.password, data['password'])
    except Exception:
        password_valid = False

    if not password_valid:
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

    token = create_token(user.id, user.role)
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'data': {
            'token': token,
            'user': user.to_dict()
        }
    })


@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    return jsonify({'success': True, 'message': 'Logged out successfully'})


@auth_bp.route('/api/auth/me', methods=['GET'])
@token_required
def get_me(current_user):
    return jsonify({
        'success': True,
        'data': current_user.to_dict()
    })

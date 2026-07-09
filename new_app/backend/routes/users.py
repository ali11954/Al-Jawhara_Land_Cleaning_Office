from flask import Blueprint, request, jsonify
from auth import token_required, admin_required
from models import db, User
from werkzeug.security import generate_password_hash

users_bp = Blueprint('users', __name__)


@users_bp.route('/api/users', methods=['GET'])
@token_required
def list_users(current_user):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    users = User.query.order_by(User.username).all()
    return jsonify({
        'success': True,
        'data': [u.to_dict() for u in users]
    })


@users_bp.route('/api/users', methods=['POST'])
@token_required
def create_user(current_user):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Admin access required'}), 403

    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'success': False, 'message': 'Username and password are required'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'success': False, 'message': 'Username already exists'}), 400

    u = User(
        username=data['username'],
        password=generate_password_hash(data['password'], method='scrypt'),
        full_name=data.get('full_name', ''),
        role=data.get('role', 'viewer'),
        is_active=data.get('is_active', True),
    )
    db.session.add(u)
    db.session.commit()
    return jsonify({'success': True, 'data': u.to_dict(), 'message': 'User created'}), 201


@users_bp.route('/api/users/<int:user_id>', methods=['PUT'])
@token_required
def update_user(current_user, user_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Admin access required'}), 403

    u = User.query.get_or_404(user_id)
    data = request.get_json()
    for field in ['full_name', 'role', 'is_active']:
        if field in data:
            setattr(u, field, data[field])
    if 'password' in data and data['password']:
        u.password = generate_password_hash(data['password'], method='scrypt')
    db.session.commit()
    return jsonify({'success': True, 'data': u.to_dict(), 'message': 'User updated'})


@users_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(current_user, user_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    u = User.query.get_or_404(user_id)
    db.session.delete(u)
    db.session.commit()
    return jsonify({'success': True, 'message': 'User deleted'})

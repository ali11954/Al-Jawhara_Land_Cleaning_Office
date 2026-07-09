from flask import Blueprint, request, jsonify
from auth import token_required
from db import get_db, fetch_all, execute

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/api/settings', methods=['PUT'])
@token_required
def update_settings(current_user):
    data = request.get_json() or {}
    with get_db() as conn:
        for key, value in data.items():
            execute(conn, "INSERT INTO system_settings (key, value) VALUES (%s,%s) ON CONFLICT (key) DO UPDATE SET value=%s",
                    (key, str(value), str(value)))
    return jsonify({'success': True, 'message': 'Settings updated'})


@settings_bp.route('/api/settings/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    data = request.get_json() or {}
    if not data.get('new_password'):
        return jsonify({'success': False, 'message': 'new_password required'}), 400
    from werkzeug.security import generate_password_hash
    with get_db() as conn:
        execute(conn, "UPDATE users SET password=%s WHERE id=%s", (generate_password_hash(data['new_password']), current_user.id))
    return jsonify({'success': True, 'message': 'Password changed'})

from flask import Blueprint, jsonify
from flask_login import login_required

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/health')
def health_check():
    return jsonify({'status': 'ok', 'message': 'API is running'})

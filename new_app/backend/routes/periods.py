from flask import Blueprint, request, jsonify
from auth import token_required
from db import get_db, fetch_all, execute
from datetime import datetime

periods_bp = Blueprint('periods', __name__)


@periods_bp.route('/api/periods', methods=['GET'])
@token_required
def list_periods(current_user):
    with get_db() as conn:
        rows = fetch_all(conn, "SELECT * FROM financial_periods ORDER BY start_date DESC")
    return jsonify({'success': True, 'data': rows})


@periods_bp.route('/api/periods', methods=['POST'])
@token_required
def create_period(current_user):
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'success': False, 'message': 'name is required'}), 400
    with get_db() as conn:
        pid = execute(conn, "INSERT INTO financial_periods (name, start_date, end_date, status) VALUES (%s,%s,%s,%s) RETURNING id",
                      (data['name'], data.get('start_date'), data.get('end_date'), data.get('status', 'open')))
    return jsonify({'success': True, 'data': {'id': pid}, 'message': 'Period created'}), 201


@periods_bp.route('/api/periods/<int:period_id>/close', methods=['POST'])
@token_required
def close_period(current_user, period_id):
    with get_db() as conn:
        execute(conn, "UPDATE financial_periods SET status='closed' WHERE id=%s", (period_id,))
    return jsonify({'success': True, 'message': 'Period closed'})


@periods_bp.route('/api/periods/<int:period_id>/reopen', methods=['POST'])
@token_required
def reopen_period(current_user, period_id):
    with get_db() as conn:
        execute(conn, "UPDATE financial_periods SET status='open' WHERE id=%s", (period_id,))
    return jsonify({'success': True, 'message': 'Period reopened'})

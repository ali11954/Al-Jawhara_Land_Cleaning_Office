from flask import Blueprint, request, jsonify
from auth import token_required
from models import db, Evaluation, Employee
from datetime import datetime
from db import get_db, fetch_all, execute

evaluations_bp = Blueprint('evaluations', __name__)


@evaluations_bp.route('/api/evaluations', methods=['GET'])
@token_required
def list_evaluations(current_user):
    page = request.args.get('page', type=int)
    per_page = request.args.get('per_page', 50, type=int)
    employee_id = request.args.get('employee_id', type=int)

    with get_db() as conn:
        q = """SELECT ev.*, e.full_name as employee_name, e.position as employee_job,
               e.company_id, ev.evaluator_id as evaluator_name
               FROM evaluations ev JOIN employees e ON ev.employee_id = e.id WHERE 1=1"""
        params = []

        if current_user.role == 'supervisor':
            if current_user.company_id:
                q += " AND e.company_id = %s"
                params.append(current_user.company_id)
            if current_user.employee_id:
                q += " AND e.supervisor_id = %s"
                params.append(current_user.employee_id)
        elif current_user.role not in ('admin', 'owner'):
            return jsonify({'success': False, 'message': 'Access denied'}), 403

        if employee_id:
            q += " AND ev.employee_id = %s"
            params.append(employee_id)

        q += " ORDER BY ev.date DESC"

        if page:
            count_q = q.replace("SELECT ev.*", "SELECT COUNT(*)")
            cur = conn.cursor()
            cur.execute(count_q, tuple(params))
            total = cur.fetchone()[0]
            offset = (page - 1) * per_page
            q += f" LIMIT {per_page} OFFSET {offset}"
            rows = fetch_all(conn, q, tuple(params))
            pages = (total + per_page - 1) // per_page
            return jsonify({'success': True, 'data': {'items': rows, 'total': total, 'page': page, 'pages': pages}})
        else:
            rows = fetch_all(conn, q, tuple(params))
            return jsonify({'success': True, 'data': rows})


@evaluations_bp.route('/api/evaluations', methods=['POST'])
@token_required
def create_evaluation(current_user):
    import json
    data = request.get_json()
    if not data or not data.get('employee_id') or not data.get('score'):
        return jsonify({'success': False, 'message': 'employee_id and score are required'}), 400

    with get_db() as conn:
        execute(conn,
            "INSERT INTO evaluations (employee_id, evaluator_id, evaluation_type, score, comments, date, criteria_scores) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (data['employee_id'], current_user.id, data.get('evaluation_type', 'supervisor'),
             data['score'], data.get('comments', ''), data.get('date', datetime.utcnow().strftime('%Y-%m-%d')),
             json.dumps(data.get('criteria_scores', []))))
    return jsonify({'success': True, 'message': 'Evaluation created'}), 201


@evaluations_bp.route('/api/evaluations/<int:eval_id>', methods=['DELETE'])
@token_required
def delete_evaluation(current_user, eval_id):
    with get_db() as conn:
        execute(conn, "DELETE FROM evaluations WHERE id=%s", (eval_id,))
    return jsonify({'success': True, 'message': 'Evaluation deleted'})


@evaluations_bp.route('/api/evaluations/areas', methods=['GET'])
@token_required
def list_areas(current_user):
    with get_db() as conn:
        rows = fetch_all(conn, "SELECT id, name, company_id FROM areas ORDER BY name")
    return jsonify({'success': True, 'data': rows})

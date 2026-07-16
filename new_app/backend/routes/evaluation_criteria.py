from flask import Blueprint, request, jsonify
from auth import token_required
from db import get_db, fetch_all, execute

eval_criteria_bp = Blueprint('eval_criteria', __name__)


@eval_criteria_bp.route('/api/evaluation-criteria', methods=['GET'])
@token_required
def list_criteria(current_user):
    job_title = request.args.get('job_title')
    region_id = request.args.get('region_id', type=int)
    with get_db() as conn:
        if region_id:
            rows = fetch_all(conn, "SELECT * FROM evaluation_criteria WHERE region_id=%s ORDER BY id", (region_id,))
        elif job_title:
            rows = fetch_all(conn, "SELECT * FROM evaluation_criteria WHERE job_title=%s ORDER BY id", (job_title,))
        else:
            rows = fetch_all(conn, "SELECT * FROM evaluation_criteria ORDER BY id")
    return jsonify({'success': True, 'data': rows})


@eval_criteria_bp.route('/api/evaluation-criteria/job-titles', methods=['GET'])
@token_required
def list_job_titles(current_user):
    with get_db() as conn:
        rows = fetch_all(conn, "SELECT DISTINCT job_title FROM evaluation_criteria WHERE job_title IS NOT NULL")
    titles = [r['job_title'] for r in rows if r.get('job_title')]
    return jsonify({'success': True, 'data': titles})


@eval_criteria_bp.route('/api/evaluation-criteria', methods=['POST'])
@token_required
def create_criterion(current_user):
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'success': False, 'message': 'name is required'}), 400
    with get_db() as conn:
        cid = execute(conn, "INSERT INTO evaluation_criteria (name, job_title, max_score, weight) VALUES (%s,%s,%s,%s) RETURNING id",
                      (data['name'], data.get('job_title'), data.get('max_score', 10), data.get('weight', 1)))
    return jsonify({'success': True, 'data': {'id': cid, **data}, 'message': 'Criterion created'}), 201


@eval_criteria_bp.route('/api/evaluation-criteria/<int:crit_id>', methods=['PUT'])
@token_required
def update_criterion(current_user, crit_id):
    data = request.get_json()
    with get_db() as conn:
        fields, vals = [], []
        for f in ['name', 'job_title', 'max_score', 'weight']:
            if f in data:
                fields.append(f'{f}=%s')
                vals.append(data[f])
        if fields:
            vals.append(crit_id)
            execute(conn, f"UPDATE evaluation_criteria SET {','.join(fields)} WHERE id=%s", vals)
    return jsonify({'success': True, 'message': 'Criterion updated'})


@eval_criteria_bp.route('/api/evaluation-criteria/<int:crit_id>', methods=['DELETE'])
@token_required
def delete_criterion(current_user, crit_id):
    with get_db() as conn:
        execute(conn, "DELETE FROM evaluation_criteria WHERE id=%s", (crit_id,))
    return jsonify({'success': True, 'message': 'Criterion deleted'})

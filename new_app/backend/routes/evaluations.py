from flask import Blueprint, request, jsonify
from auth import token_required
from models import db, Evaluation
from datetime import datetime

evaluations_bp = Blueprint('evaluations', __name__)


@evaluations_bp.route('/api/evaluations', methods=['GET'])
@token_required
def list_evaluations(current_user):
    page = request.args.get('page', type=int)
    per_page = request.args.get('per_page', 50, type=int)
    employee_id = request.args.get('employee_id', type=int)

    query = Evaluation.query
    if employee_id:
        query = query.filter_by(employee_id=employee_id)

    if page:
        pagination = query.order_by(Evaluation.date.desc()).paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            'success': True,
            'data': {
                'items': [e.to_dict() for e in pagination.items],
                'total': pagination.total,
                'page': page,
                'pages': pagination.pages,
            }
        })
    else:
        evaluations = query.order_by(Evaluation.date.desc()).all()
        return jsonify({'success': True, 'data': [e.to_dict() for e in evaluations]})


@evaluations_bp.route('/api/evaluations', methods=['POST'])
@token_required
def create_evaluation(current_user):
    import json
    data = request.get_json()
    if not data or not data.get('employee_id') or not data.get('score'):
        return jsonify({'success': False, 'message': 'employee_id and score are required'}), 400

    ev = Evaluation(
        employee_id=data['employee_id'],
        evaluator_id=current_user.id,
        evaluation_type=data.get('evaluation_type', 'supervisor'),
        score=data['score'],
        comments=data.get('comments', ''),
        date=datetime.strptime(data['date'], '%Y-%m-%d').date() if data.get('date') else datetime.utcnow().date(),
        criteria_scores=json.dumps(data.get('criteria_scores', [])),
        region_id=data.get('region_id'),
        location_id=data.get('location_id'),
    )
    db.session.add(ev)
    db.session.commit()
    return jsonify({'success': True, 'data': ev.to_dict(), 'message': 'Evaluation created'}), 201


@evaluations_bp.route('/api/evaluations/<int:eval_id>', methods=['DELETE'])
@token_required
def delete_evaluation(current_user, eval_id):
    ev = Evaluation.query.get_or_404(eval_id)
    db.session.delete(ev)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Evaluation deleted'})

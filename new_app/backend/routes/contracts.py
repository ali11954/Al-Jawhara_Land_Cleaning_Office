from flask import Blueprint, request, jsonify
from auth import token_required
from models import db, Contract
from datetime import datetime

contracts_bp = Blueprint('contracts', __name__)


@contracts_bp.route('/api/contracts', methods=['GET'])
@token_required
def list_contracts(current_user):
    page = request.args.get('page', type=int)
    per_page = request.args.get('per_page', 50, type=int)
    company_id = request.args.get('company_id', type=int)

    query = Contract.query
    if company_id:
        query = query.filter_by(company_id=company_id)

    if page:
        pagination = query.order_by(Contract.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            'success': True,
            'data': {
                'items': [c.to_dict() for c in pagination.items],
                'total': pagination.total,
                'page': page,
                'pages': pagination.pages,
            }
        })
    else:
        contracts = query.order_by(Contract.created_at.desc()).all()
        return jsonify({'success': True, 'data': [c.to_dict() for c in contracts]})


@contracts_bp.route('/api/contracts', methods=['POST'])
@token_required
def create_contract(current_user):
    data = request.get_json()
    if not data or not data.get('contract_value'):
        return jsonify({'success': False, 'message': 'contract_value is required'}), 400

    c = Contract(
        company_id=data.get('company_id'),
        contract_type=data.get('contract_type', 'annual'),
        contract_value=data['contract_value'],
        contract_number=data.get('contract_number', ''),
        start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data.get('start_date') else datetime.utcnow().date(),
        end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data.get('end_date') else None,
        amount_received=data.get('amount_received', 0),
        remaining_amount=data.get('remaining_amount', data.get('contract_value', 0)),
        monthly_value=data.get('monthly_value', 0),
        status=data.get('status', 'active'),
        notes=data.get('notes', ''),
    )
    db.session.add(c)
    db.session.commit()
    return jsonify({'success': True, 'data': c.to_dict(), 'message': 'Contract created'}), 201


@contracts_bp.route('/api/contracts/<int:contract_id>', methods=['PUT'])
@token_required
def update_contract(current_user, contract_id):
    c = Contract.query.get_or_404(contract_id)
    data = request.get_json()
    for field in ['company_id', 'contract_type', 'contract_value', 'contract_number',
                  'start_date', 'end_date', 'amount_received', 'remaining_amount',
                  'monthly_value', 'status', 'notes']:
        if field in data:
            if field in ['start_date', 'end_date'] and data[field]:
                setattr(c, field, datetime.strptime(data[field], '%Y-%m-%d').date())
            else:
                setattr(c, field, data[field])
    db.session.commit()
    return jsonify({'success': True, 'data': c.to_dict(), 'message': 'Contract updated'})


@contracts_bp.route('/api/contracts/<int:contract_id>', methods=['DELETE'])
@token_required
def delete_contract(current_user, contract_id):
    c = Contract.query.get_or_404(contract_id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Contract deleted'})

from flask import Blueprint, request, jsonify
from auth import token_required
from models import db, Company

companies_bp = Blueprint('companies', __name__)


@companies_bp.route('/api/companies', methods=['GET'])
@token_required
def list_companies(current_user):
    companies = Company.query.order_by(Company.name).all()
    return jsonify({
        'success': True,
        'data': [c.to_dict() for c in companies]
    })


@companies_bp.route('/api/companies/<int:company_id>', methods=['GET'])
@token_required
def get_company(current_user, company_id):
    c = Company.query.get_or_404(company_id)
    return jsonify({'success': True, 'data': c.to_dict()})


@companies_bp.route('/api/companies', methods=['POST'])
@token_required
def create_company(current_user):
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'success': False, 'message': 'Company name is required'}), 400

    c = Company(
        name=data['name'],
        contact_person=data.get('contact_person', ''),
        phone=data.get('phone', ''),
        email=data.get('email', ''),
    )
    db.session.add(c)
    db.session.commit()
    return jsonify({'success': True, 'data': c.to_dict(), 'message': 'Company created'}), 201


@companies_bp.route('/api/companies/<int:company_id>', methods=['PUT'])
@token_required
def update_company(current_user, company_id):
    c = Company.query.get_or_404(company_id)
    data = request.get_json()
    for field in ['name', 'contact_person', 'phone', 'email']:
        if field in data:
            setattr(c, field, data[field])
    db.session.commit()
    return jsonify({'success': True, 'data': c.to_dict(), 'message': 'Company updated'})


@companies_bp.route('/api/companies/<int:company_id>', methods=['DELETE'])
@token_required
def delete_company(current_user, company_id):
    c = Company.query.get_or_404(company_id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Company deleted'})

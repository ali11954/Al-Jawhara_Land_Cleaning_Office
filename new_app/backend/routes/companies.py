from flask import Blueprint, request, jsonify
from auth import token_required
from db import get_db, fetch_all, fetch_one, execute

companies_bp = Blueprint('companies', __name__)


@companies_bp.route('/api/companies', methods=['GET'])
@token_required
def list_companies(current_user):
    with get_db() as conn:
        if current_user.role == 'supervisor' and current_user.company_id:
            rows = fetch_all(conn, "SELECT * FROM companies WHERE id=%s", (current_user.company_id,))
        else:
            rows = fetch_all(conn, "SELECT * FROM companies ORDER BY name")
    return jsonify({'success': True, 'data': rows})


@companies_bp.route('/api/companies/<int:company_id>', methods=['GET'])
@token_required
def get_company(current_user, company_id):
    with get_db() as conn:
        row = fetch_one(conn, "SELECT * FROM companies WHERE id=%s", (company_id,))
    if not row:
        return jsonify({'success': False, 'message': 'Company not found'}), 404
    return jsonify({'success': True, 'data': row})


@companies_bp.route('/api/companies', methods=['POST'])
@token_required
def create_company(current_user):
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'success': False, 'message': 'Company name is required'}), 400
    with get_db() as conn:
        cid = execute(conn,
            "INSERT INTO companies (name, contact_person, phone, email) VALUES (%s,%s,%s,%s) RETURNING id",
            (data['name'], data.get('contact_person', ''), data.get('phone', ''), data.get('email', '')))
    return jsonify({'success': True, 'data': {'id': cid}, 'message': 'Company created'}), 201


@companies_bp.route('/api/companies/<int:company_id>', methods=['PUT'])
@token_required
def update_company(current_user, company_id):
    data = request.get_json()
    with get_db() as conn:
        fields, vals = [], []
        for f in ['name', 'contact_person', 'phone', 'email']:
            if f in data:
                fields.append(f'{f}=%s')
                vals.append(data[f])
        if fields:
            vals.append(company_id)
            execute(conn, f"UPDATE companies SET {','.join(fields)} WHERE id=%s", vals)
    return jsonify({'success': True, 'message': 'Company updated'})


@companies_bp.route('/api/companies/<int:company_id>', methods=['DELETE'])
@token_required
def delete_company(current_user, company_id):
    with get_db() as conn:
        execute(conn, "DELETE FROM companies WHERE id=%s", (company_id,))
    return jsonify({'success': True, 'message': 'Company deleted'})


@companies_bp.route('/api/companies/<int:company_id>/regions', methods=['GET'])
@token_required
def company_regions(current_user, company_id):
    with get_db() as conn:
        rows = fetch_all(conn, "SELECT * FROM regions WHERE company_id=%s ORDER BY name", (company_id,))
    return jsonify({'success': True, 'data': rows})

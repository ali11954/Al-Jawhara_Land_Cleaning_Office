from flask import Blueprint, request, jsonify
from auth import token_required
from models import db, Supplier

suppliers_bp = Blueprint('suppliers', __name__)


@suppliers_bp.route('/api/suppliers', methods=['GET'])
@token_required
def list_suppliers(current_user):
    suppliers = Supplier.query.order_by(Supplier.name).all()
    return jsonify({
        'success': True,
        'data': [s.to_dict() for s in suppliers]
    })


@suppliers_bp.route('/api/suppliers/<int:supplier_id>', methods=['GET'])
@token_required
def get_supplier(current_user, supplier_id):
    s = Supplier.query.get_or_404(supplier_id)
    return jsonify({'success': True, 'data': s.to_dict()})


@suppliers_bp.route('/api/suppliers', methods=['POST'])
@token_required
def create_supplier(current_user):
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'success': False, 'message': 'Supplier name is required'}), 400

    s = Supplier(
        name=data['name'],
        name_ar=data.get('name_ar', data['name']),
        contact_person=data.get('contact_person', ''),
        phone=data.get('phone', ''),
        email=data.get('email', ''),
        address=data.get('address', ''),
        supplier_type=data.get('supplier_type', 'general'),
        notes=data.get('notes', ''),
    )
    db.session.add(s)
    db.session.commit()
    return jsonify({'success': True, 'data': s.to_dict(), 'message': 'Supplier created'}), 201


@suppliers_bp.route('/api/suppliers/<int:supplier_id>', methods=['PUT'])
@token_required
def update_supplier(current_user, supplier_id):
    s = Supplier.query.get_or_404(supplier_id)
    data = request.get_json()
    for field in ['name', 'name_ar', 'contact_person', 'phone', 'email', 'address', 'supplier_type', 'notes']:
        if field in data:
            setattr(s, field, data[field])
    db.session.commit()
    return jsonify({'success': True, 'data': s.to_dict(), 'message': 'Supplier updated'})

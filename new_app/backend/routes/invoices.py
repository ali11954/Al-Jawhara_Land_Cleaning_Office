from flask import Blueprint, request, jsonify
from auth import token_required
from models import db, Invoice
from datetime import datetime

invoices_bp = Blueprint('invoices', __name__)


@invoices_bp.route('/api/invoices', methods=['GET'])
@token_required
def list_invoices(current_user):
    page = request.args.get('page', type=int)
    per_page = request.args.get('per_page', 50, type=int)
    contract_id = request.args.get('contract_id', type=int)

    query = Invoice.query
    if contract_id:
        query = query.filter_by(contract_id=contract_id)

    if page:
        pagination = query.order_by(Invoice.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            'success': True,
            'data': {
                'items': [i.to_dict() for i in pagination.items],
                'total': pagination.total,
                'page': page,
                'pages': pagination.pages,
            }
        })
    else:
        invoices = query.order_by(Invoice.created_at.desc()).all()
        return jsonify({'success': True, 'data': [i.to_dict() for i in invoices]})


@invoices_bp.route('/api/invoices', methods=['POST'])
@token_required
def create_invoice(current_user):
    data = request.get_json()
    if not data or not data.get('amount'):
        return jsonify({'success': False, 'message': 'amount is required'}), 400

    inv = Invoice(
        contract_id=data.get('contract_id'),
        invoice_number=data.get('invoice_number'),
        amount=data['amount'],
        invoice_date=datetime.strptime(data['invoice_date'], '%Y-%m-%d').date() if data.get('invoice_date') else datetime.utcnow().date(),
        due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date() if data.get('due_date') else None,
        is_paid=data.get('is_paid', False),
        paid_amount=data.get('paid_amount', 0),
        payment_method=data.get('payment_method', ''),
        description=data.get('description', ''),
        notes=data.get('notes', ''),
    )
    db.session.add(inv)
    db.session.commit()
    return jsonify({'success': True, 'data': inv.to_dict(), 'message': 'Invoice created'}), 201


@invoices_bp.route('/api/invoices/<int:invoice_id>/receive', methods=['POST'])
@token_required
def receive_invoice(current_user, invoice_id):
    data = request.get_json() or {}
    inv = Invoice.query.get_or_404(invoice_id)
    inv.is_paid = True
    inv.paid_amount = data.get('paid_amount', inv.amount)
    inv.paid_date = datetime.strptime(data['paid_date'], '%Y-%m-%d').date() if data.get('paid_date') else datetime.utcnow().date()
    inv.payment_method = data.get('payment_method', 'cash')
    db.session.commit()
    return jsonify({'success': True, 'data': inv.to_dict(), 'message': 'Invoice payment received'})

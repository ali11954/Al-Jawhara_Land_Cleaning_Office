from flask import Blueprint, request, jsonify
from auth import token_required
from db import get_db, fetch_all, fetch_one, execute
from datetime import datetime

supplier_invoices_bp = Blueprint('supplier_invoices', __name__)


@supplier_invoices_bp.route('/api/supplier-invoices', methods=['GET'])
@token_required
def list_supplier_invoices(current_user):
    supplier_id = request.args.get('supplier_id', type=int)
    with get_db() as conn:
        q = "SELECT si.*, s.name as supplier_name, s.name_ar as supplier_name_ar FROM supplier_invoices si LEFT JOIN suppliers s ON si.supplier_id=s.id WHERE 1=1"
        params = []
        if supplier_id:
            q += " AND si.supplier_id=%s"
            params.append(supplier_id)
        q += " ORDER BY si.created_at DESC"
        rows = fetch_all(conn, q, tuple(params))
    return jsonify({'success': True, 'data': rows})


@supplier_invoices_bp.route('/api/supplier-invoices', methods=['POST'])
@token_required
def create_supplier_invoice(current_user):
    data = request.get_json()
    if not data or not data.get('supplier_id') or not data.get('amount'):
        return jsonify({'success': False, 'message': 'supplier_id and amount required'}), 400
    with get_db() as conn:
        iid = execute(conn,
            "INSERT INTO supplier_invoices (supplier_id, amount, description, invoice_date, due_date, status, created_by) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (data['supplier_id'], data['amount'], data.get('description', ''),
             data.get('invoice_date', datetime.utcnow().strftime('%Y-%m-%d')),
             data.get('due_date'), data.get('status', 'pending'), current_user.id))
    return jsonify({'success': True, 'data': {'id': iid}, 'message': 'Supplier invoice created'}), 201


@supplier_invoices_bp.route('/api/supplier-invoices/<int:inv_id>/pay', methods=['POST'])
@token_required
def pay_supplier_invoice(current_user, inv_id):
    data = request.get_json() or {}
    with get_db() as conn:
        execute(conn,
            "INSERT INTO supplier_invoice_payments (supplier_invoice_id, amount, payment_method, payment_date, notes, created_by) "
            "VALUES (%s,%s,%s,%s,%s,%s)",
            (inv_id, data.get('amount', 0), data.get('payment_method', 'cash'),
             data.get('payment_date', datetime.utcnow().strftime('%Y-%m-%d')),
             data.get('notes', ''), current_user.id))
    return jsonify({'success': True, 'message': 'Payment recorded'}), 201


@supplier_invoices_bp.route('/api/supplier-invoices/<int:inv_id>/delete', methods=['POST'])
@token_required
def delete_supplier_invoice(current_user, inv_id):
    with get_db() as conn:
        execute(conn, "UPDATE supplier_invoices SET status='deleted' WHERE id=%s", (inv_id,))
    return jsonify({'success': True, 'message': 'Invoice deleted'})


@supplier_invoices_bp.route('/api/supplier-invoices/<int:inv_id>/voucher', methods=['GET'])
@token_required
def supplier_invoice_voucher(current_user, inv_id):
    with get_db() as conn:
        row = fetch_one(conn, "SELECT si.*, s.name as supplier_name, s.name_ar as supplier_name_ar FROM supplier_invoices si LEFT JOIN suppliers s ON si.supplier_id=s.id WHERE si.id=%s", (inv_id,))
    return jsonify({'success': True, 'data': row})


@supplier_invoices_bp.route('/api/salary-deduction/pay', methods=['POST'])
@token_required
def salary_deduction_pay(current_user):
    data = request.get_json() or {}
    with get_db() as conn:
        execute(conn, "INSERT INTO supplier_invoice_payments (supplier_invoice_id, amount, payment_method, notes, created_by) VALUES (%s,%s,%s,%s,%s)",
                (data.get('supplier_invoice_id'), data.get('amount', 0), 'salary_deduction', data.get('notes', ''), current_user.id))
    return jsonify({'success': True, 'message': 'Salary deduction recorded'}), 201


@supplier_invoices_bp.route('/api/salary-deduction/voucher', methods=['POST'])
@token_required
def salary_deduction_voucher(current_user):
    return jsonify({'success': True, 'data': {'message': 'Voucher generated'}})

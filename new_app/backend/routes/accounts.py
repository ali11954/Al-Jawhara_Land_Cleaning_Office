from flask import Blueprint, request, jsonify
from auth import token_required
from models import db, Account, JournalEntry, JournalEntryDetail
from sqlalchemy import func
from datetime import datetime
from db import get_db, fetch_all, fetch_one, execute

accounts_bp = Blueprint('accounts', __name__)


@accounts_bp.route('/api/accounts', methods=['GET'])
@token_required
def list_accounts(current_user):
    accounts = Account.query.order_by(Account.code).all()
    return jsonify({'success': True, 'data': [a.to_dict() for a in accounts]})


@accounts_bp.route('/api/accounts/<int:account_id>', methods=['GET'])
@token_required
def get_account(current_user, account_id):
    a = Account.query.get_or_404(account_id)
    return jsonify({'success': True, 'data': a.to_dict()})


@accounts_bp.route('/api/accounts', methods=['POST'])
@token_required
def create_account(current_user):
    data = request.get_json()
    if not data or not data.get('code') or not data.get('name'):
        return jsonify({'success': False, 'message': 'code and name are required'}), 400
    a = Account(
        code=data['code'], name=data['name'], name_ar=data.get('name_ar', data['name']),
        account_type=data.get('account_type', 'expense'), nature=data.get('nature', 'debit'),
        parent_id=data.get('parent_id'), opening_balance=data.get('opening_balance', 0),
        notes=data.get('notes', ''),
    )
    db.session.add(a)
    db.session.commit()
    return jsonify({'success': True, 'data': a.to_dict(), 'message': 'Account created'}), 201


@accounts_bp.route('/api/accounts/<int:account_id>', methods=['PUT'])
@token_required
def update_account(current_user, account_id):
    a = Account.query.get_or_404(account_id)
    data = request.get_json()
    for field in ['name', 'name_ar', 'account_type', 'nature', 'parent_id', 'opening_balance', 'notes', 'is_active']:
        if field in data:
            setattr(a, field, data[field])
    db.session.commit()
    return jsonify({'success': True, 'data': a.to_dict(), 'message': 'Account updated'})


@accounts_bp.route('/api/accounts/<int:account_id>', methods=['DELETE'])
@token_required
def delete_account(current_user, account_id):
    a = Account.query.get_or_404(account_id)
    db.session.delete(a)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Account deleted'})


@accounts_bp.route('/api/accounts/balance', methods=['GET'])
@token_required
def accounts_balance(current_user):
    accounts = Account.query.all()
    result = []
    for a in accounts:
        debit = db.session.query(func.coalesce(func.sum(JournalEntryDetail.debit), 0)).filter(
            JournalEntryDetail.account_id == a.id).scalar()
        credit = db.session.query(func.coalesce(func.sum(JournalEntryDetail.credit), 0)).filter(
            JournalEntryDetail.account_id == a.id).scalar()
        balance = (a.opening_balance or 0) + float(debit) - float(credit)
        result.append({'id': a.id, 'code': a.code, 'name': a.name, 'name_ar': a.name_ar,
                       'balance': balance, 'debit': float(debit), 'credit': float(credit)})
    return jsonify({'success': True, 'data': result})


@accounts_bp.route('/api/accounts/chart', methods=['GET'])
@token_required
def accounts_chart(current_user):
    accounts = Account.query.order_by(Account.code).all()
    return jsonify({'success': True, 'data': [a.to_dict() for a in accounts]})


@accounts_bp.route('/api/accounts/journal', methods=['GET'])
@token_required
def list_journal(current_user):
    with get_db() as conn:
        entries = fetch_all(conn, "SELECT * FROM journal_entries ORDER BY date DESC")
        for e in entries:
            e['details'] = fetch_all(conn,
                "SELECT jed.*, a.name as account_name FROM journal_entry_details jed "
                "LEFT JOIN accounts a ON jed.account_id=a.id WHERE jed.entry_id=%s" if isinstance(conn, type(None)) or hasattr(conn, 'cursor') else
                "SELECT jed.*, a.name as account_name FROM journal_entry_details jed "
                "LEFT JOIN accounts a ON jed.account_id=a.id WHERE jed.entry_id=?",
                (e['id'],))
    return jsonify({'success': True, 'data': entries})


@accounts_bp.route('/api/accounts/journal', methods=['POST'])
@token_required
def create_journal(current_user):
    data = request.get_json()
    if not data or not data.get('description') or not data.get('details'):
        return jsonify({'success': False, 'message': 'description and details required'}), 400
    entry_num = f"JE-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    with get_db() as conn:
        entry_id = execute(conn,
            "INSERT INTO journal_entries (entry_number, date, description, created_by) VALUES (%s,%s,%s,%s) RETURNING id",
            (entry_num, data.get('date', datetime.utcnow().strftime('%Y-%m-%d')), data['description'], current_user.id))
        for d in data['details']:
            execute(conn,
                "INSERT INTO journal_entry_details (entry_id, account_id, debit, credit, description) VALUES (%s,%s,%s,%s,%s)",
                (entry_id, d.get('account_id'), d.get('debit', 0), d.get('credit', 0), d.get('description', '')))
    return jsonify({'success': True, 'data': {'id': entry_id, 'entry_number': entry_num}, 'message': 'Journal entry created'}), 201


@accounts_bp.route('/api/accounts/journal/<int:entry_id>', methods=['DELETE'])
@token_required
def delete_journal(current_user, entry_id):
    with get_db() as conn:
        execute(conn, "DELETE FROM journal_entry_details WHERE entry_id=%s", (entry_id,))
        execute(conn, "DELETE FROM journal_entries WHERE id=%s", (entry_id,))
    return jsonify({'success': True, 'message': 'Journal entry deleted'})


@accounts_bp.route('/api/accounts/trial-balance', methods=['GET'])
@token_required
def trial_balance(current_user):
    accounts = Account.query.order_by(Account.code).all()
    result = []
    for a in accounts:
        debit = db.session.query(func.coalesce(func.sum(JournalEntryDetail.debit), 0)).filter(
            JournalEntryDetail.account_id == a.id).scalar()
        credit = db.session.query(func.coalesce(func.sum(JournalEntryDetail.credit), 0)).filter(
            JournalEntryDetail.account_id == a.id).scalar()
        bal = float(debit) - float(credit)
        if abs(bal) > 0.01 or abs(float(debit)) > 0.01 or abs(float(credit)) > 0.01:
            result.append({'account_id': a.id, 'code': a.code, 'name': a.name, 'name_ar': a.name_ar,
                           'debit': float(debit), 'credit': float(credit), 'balance': bal})
    return jsonify({'success': True, 'data': result})


@accounts_bp.route('/api/accounts/statement', methods=['GET'])
@token_required
def account_statement(current_user):
    account_id = request.args.get('account_id', type=int)
    if not account_id:
        return jsonify({'success': False, 'message': 'account_id required'}), 400
    with get_db() as conn:
        rows = fetch_all(conn,
            "SELECT jed.*, je.entry_number, je.date as entry_date, je.description as entry_desc "
            "FROM journal_entry_details jed LEFT JOIN journal_entries je ON jed.entry_id=je.id "
            "WHERE jed.account_id=%s ORDER BY je.date", (account_id,))
    return jsonify({'success': True, 'data': rows})


@accounts_bp.route('/api/accounts/income-statement', methods=['GET'])
@token_required
def income_statement(current_user):
    income_accounts = Account.query.filter_by(account_type='income').all()
    expense_accounts = Account.query.filter_by(account_type='expense').all()
    total_income = 0
    total_expense = 0
    income_detail = []
    expense_detail = []
    for a in income_accounts:
        credit = db.session.query(func.coalesce(func.sum(JournalEntryDetail.credit), 0)).filter(
            JournalEntryDetail.account_id == a.id).scalar()
        total_income += float(credit)
        income_detail.append({'code': a.code, 'name': a.name, 'name_ar': a.name_ar, 'amount': float(credit)})
    for a in expense_accounts:
        debit = db.session.query(func.coalesce(func.sum(JournalEntryDetail.debit), 0)).filter(
            JournalEntryDetail.account_id == a.id).scalar()
        total_expense += float(debit)
        expense_detail.append({'code': a.code, 'name': a.name, 'name_ar': a.name_ar, 'amount': float(debit)})
    return jsonify({'success': True, 'data': {
        'total_income': total_income, 'total_expense': total_expense,
        'net_profit': total_income - total_expense,
        'income_accounts': income_detail, 'expense_accounts': expense_detail,
    }})


@accounts_bp.route('/api/accounts/balance-sheet', methods=['GET'])
@token_required
def balance_sheet(current_user):
    asset_accounts = Account.query.filter_by(account_type='asset').all()
    liability_accounts = Account.query.filter_by(account_type='liability').all()
    equity_accounts = Account.query.filter_by(account_type='equity').all()
    total_asset = sum(float(db.session.query(func.coalesce(func.sum(JournalEntryDetail.debit), 0)).filter(
        JournalEntryDetail.account_id == a.id).scalar()) for a in asset_accounts)
    total_liability = sum(float(db.session.query(func.coalesce(func.sum(JournalEntryDetail.credit), 0)).filter(
        JournalEntryDetail.account_id == a.id).scalar()) for a in liability_accounts)
    total_equity = sum(float(db.session.query(func.coalesce(func.sum(JournalEntryDetail.credit), 0)).filter(
        JournalEntryDetail.account_id == a.id).scalar()) for a in equity_accounts)
    return jsonify({'success': True, 'data': {
        'total_assets': total_asset, 'total_liabilities': total_liability,
        'total_equity': total_equity, 'balance': total_asset - total_liability - total_equity,
    }})

from flask import Blueprint, request, jsonify
from auth import token_required
from datetime import datetime
from db import get_db, fetch_all, fetch_one, execute

accounts_bp = Blueprint('accounts', __name__)


@accounts_bp.route('/api/accounts', methods=['GET'])
@token_required
def list_accounts(current_user):
    with get_db() as conn:
        rows = fetch_all(conn, "SELECT * FROM accounts ORDER BY code")
    return jsonify({'success': True, 'data': rows})


@accounts_bp.route('/api/accounts/<int:account_id>', methods=['GET'])
@token_required
def get_account(current_user, account_id):
    with get_db() as conn:
        row = fetch_one(conn, "SELECT * FROM accounts WHERE id=%s", (account_id,))
    if not row:
        return jsonify({'success': False, 'message': 'Account not found'}), 404
    return jsonify({'success': True, 'data': row})


@accounts_bp.route('/api/accounts', methods=['POST'])
@token_required
def create_account(current_user):
    data = request.get_json()
    if not data or not data.get('code') or not data.get('name'):
        return jsonify({'success': False, 'message': 'code and name are required'}), 400
    with get_db() as conn:
        aid = execute(conn,
            "INSERT INTO accounts (code, name, name_ar, account_type, nature, parent_id, opening_balance, notes) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (data['code'], data['name'], data.get('name_ar', data['name']),
             data.get('account_type', 'expense'), data.get('nature', 'debit'),
             data.get('parent_id'), data.get('opening_balance', 0), data.get('notes', '')))
    return jsonify({'success': True, 'data': {'id': aid}, 'message': 'Account created'}), 201


@accounts_bp.route('/api/accounts/<int:account_id>', methods=['PUT'])
@token_required
def update_account(current_user, account_id):
    data = request.get_json()
    with get_db() as conn:
        fields, vals = [], []
        for f in ['name', 'name_ar', 'account_type', 'nature', 'parent_id', 'opening_balance', 'notes', 'is_active']:
            if f in data:
                fields.append(f'{f}=%s')
                vals.append(data[f])
        if fields:
            vals.append(account_id)
            execute(conn, f"UPDATE accounts SET {','.join(fields)} WHERE id=%s", vals)
    return jsonify({'success': True, 'data': {'id': account_id}, 'message': 'Account updated'})


@accounts_bp.route('/api/accounts/<int:account_id>', methods=['DELETE'])
@token_required
def delete_account(current_user, account_id):
    with get_db() as conn:
        execute(conn, "DELETE FROM accounts WHERE id=%s", (account_id,))
    return jsonify({'success': True, 'message': 'Account deleted'})


@accounts_bp.route('/api/accounts/balance', methods=['GET'])
@token_required
def accounts_balance(current_user):
    with get_db() as conn:
        accounts = fetch_all(conn, "SELECT * FROM accounts ORDER BY code")
        all_debits = fetch_all(conn, "SELECT account_id, COALESCE(SUM(debit), 0) as total FROM journal_entry_details GROUP BY account_id")
        all_credits = fetch_all(conn, "SELECT account_id, COALESCE(SUM(credit), 0) as total FROM journal_entry_details GROUP BY account_id")
        debit_map = {r['account_id']: float(r['total']) for r in all_debits}
        credit_map = {r['account_id']: float(r['total']) for r in all_credits}
        result = []
        for a in accounts:
            debit = debit_map.get(a['id'], 0)
            credit = credit_map.get(a['id'], 0)
            balance = (a.get('opening_balance') or 0) + debit - credit
            result.append({
                'id': a['id'], 'code': a['code'], 'name': a['name'],
                'name_ar': a.get('name_ar'), 'balance': balance,
                'debit': debit, 'credit': credit
            })
    return jsonify({'success': True, 'data': result})


@accounts_bp.route('/api/accounts/chart', methods=['GET'])
@token_required
def accounts_chart(current_user):
    with get_db() as conn:
        rows = fetch_all(conn, "SELECT * FROM accounts ORDER BY code")
    return jsonify({'success': True, 'data': rows})


@accounts_bp.route('/api/accounts/journal', methods=['GET'])
@token_required
def list_journal(current_user):
    with get_db() as conn:
        entries = fetch_all(conn, "SELECT * FROM journal_entries ORDER BY date DESC")
        all_details = fetch_all(conn,
            "SELECT jed.*, a.name as account_name FROM journal_entry_details jed "
            "LEFT JOIN accounts a ON jed.account_id=a.id ORDER BY jed.entry_id")
        details_by_entry = {}
        for d in all_details:
            eid = d['entry_id']
            if eid not in details_by_entry:
                details_by_entry[eid] = []
            details_by_entry[eid].append(d)
        for e in entries:
            e['details'] = details_by_entry.get(e['id'], [])
            total_debit = sum(float(d.get('debit') or 0) for d in e['details'])
            total_credit = sum(float(d.get('credit') or 0) for d in e['details'])
            e['total_debit'] = total_debit
            e['total_credit'] = total_credit
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
    with get_db() as conn:
        accounts = fetch_all(conn, "SELECT * FROM accounts ORDER BY code")
        all_debits = fetch_all(conn, "SELECT account_id, COALESCE(SUM(debit), 0) as total FROM journal_entry_details GROUP BY account_id")
        all_credits = fetch_all(conn, "SELECT account_id, COALESCE(SUM(credit), 0) as total FROM journal_entry_details GROUP BY account_id")
        debit_map = {r['account_id']: float(r['total']) for r in all_debits}
        credit_map = {r['account_id']: float(r['total']) for r in all_credits}
        result = []
        for a in accounts:
            debit = debit_map.get(a['id'], 0)
            credit = credit_map.get(a['id'], 0)
            bal = debit - credit
            if abs(bal) > 0.01 or abs(debit) > 0.01 or abs(credit) > 0.01:
                result.append({
                    'account_id': a['id'], 'code': a['code'],
                    'name': a['name'], 'name_ar': a.get('name_ar'),
                    'debit': debit, 'credit': credit, 'balance': bal
                })
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
    with get_db() as conn:
        income_accounts = fetch_all(conn, "SELECT * FROM accounts WHERE account_type='income' ORDER BY code")
        expense_accounts = fetch_all(conn, "SELECT * FROM accounts WHERE account_type='expense' ORDER BY code")
        all_credits = fetch_all(conn, "SELECT account_id, COALESCE(SUM(credit), 0) as total FROM journal_entry_details GROUP BY account_id")
        all_debits = fetch_all(conn, "SELECT account_id, COALESCE(SUM(debit), 0) as total FROM journal_entry_details GROUP BY account_id")
        credit_map = {r['account_id']: float(r['total']) for r in all_credits}
        debit_map = {r['account_id']: float(r['total']) for r in all_debits}
        total_income = 0
        total_expense = 0
        income_detail = []
        expense_detail = []
        for a in income_accounts:
            amount = credit_map.get(a['id'], 0)
            total_income += amount
            income_detail.append({'code': a['code'], 'name': a['name'], 'name_ar': a.get('name_ar'), 'amount': amount})
        for a in expense_accounts:
            amount = debit_map.get(a['id'], 0)
            total_expense += amount
            expense_detail.append({'code': a['code'], 'name': a['name'], 'name_ar': a.get('name_ar'), 'amount': amount})
    return jsonify({'success': True, 'data': {
        'total_income': total_income, 'total_expense': total_expense,
        'net_profit': total_income - total_expense,
        'income_accounts': income_detail, 'expense_accounts': expense_detail,
    }})


@accounts_bp.route('/api/accounts/balance-sheet', methods=['GET'])
@token_required
def balance_sheet(current_user):
    with get_db() as conn:
        asset_accounts = fetch_all(conn, "SELECT * FROM accounts WHERE account_type='asset' ORDER BY code")
        liability_accounts = fetch_all(conn, "SELECT * FROM accounts WHERE account_type='liability' ORDER BY code")
        equity_accounts = fetch_all(conn, "SELECT * FROM accounts WHERE account_type='equity' ORDER BY code")
        all_debits = fetch_all(conn, "SELECT account_id, COALESCE(SUM(debit), 0) as total FROM journal_entry_details GROUP BY account_id")
        all_credits = fetch_all(conn, "SELECT account_id, COALESCE(SUM(credit), 0) as total FROM journal_entry_details GROUP BY account_id")
        debit_map = {r['account_id']: float(r['total']) for r in all_debits}
        credit_map = {r['account_id']: float(r['total']) for r in all_credits}
        total_asset = sum(debit_map.get(a['id'], 0) for a in asset_accounts)
        total_liability = sum(credit_map.get(a['id'], 0) for a in liability_accounts)
        total_equity = sum(credit_map.get(a['id'], 0) for a in equity_accounts)
    return jsonify({'success': True, 'data': {
        'total_assets': total_asset, 'total_liabilities': total_liability,
        'total_equity': total_equity, 'balance': total_asset - total_liability - total_equity,
    }})

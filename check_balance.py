from app import app, db
from models import Contract, JournalEntry
from utils import create_contract_journal_entry

with app.app_context():
    contracts = Contract.query.all()
    print(f'عدد العقود: {len(contracts)}')

    for c in contracts:
        exists = JournalEntry.query.filter_by(reference_type='contract', reference_id=c.id).first()
        if exists:
            print(f'عقد {c.contract_number}: قيد موجود {exists.entry_number}')
        else:
            entry = create_contract_journal_entry(c)
            db.session.commit()
            print(f'عقد {c.contract_number}: تم إنشاء قيد {entry.entry_number}')
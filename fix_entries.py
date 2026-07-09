from app import app, db
from utils import fix_old_contract_entries, fix_old_invoice_entries

with app.app_context():
    print("="*50)
    print("🔧 بدء تصحيح القيود المحاسبية القديمة")
    print("="*50)
    
    fix_old_contract_entries()
    fix_old_invoice_entries()
    
    print("="*50)
    print("✅ اكتمل التصحيح")
    print("="*50)
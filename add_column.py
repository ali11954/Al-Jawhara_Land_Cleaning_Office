# fix_cleaning_db.py
from app import app, db
from models import Supplier

with app.app_context():
    db.create_all()
    print('✅ تم تحديث قاعدة البيانات وإضافة العمود payable_account_id')
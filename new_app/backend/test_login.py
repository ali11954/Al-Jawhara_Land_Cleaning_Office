import sys
sys.path.insert(0, '.')
from app import create_app
from werkzeug.security import check_password_hash
from models import User

app = create_app()
with app.app_context():
    users = User.query.all()
    for user in users:
        print(f'\nUser: {user.username} (role={user.role})')
        print(f'  Password hash: {user.password_hash[:60]}...')
        
        # Try common passwords
        for pwd in ['aljaber123', 'owner123', 'admin123', 'password', '123456', 'hady123', 'jaber123', 'abod123', 'atar123']:
            try:
                if check_password_hash(user.password_hash, pwd):
                    print(f'  Password matches: {pwd}')
                    break
            except Exception as e:
                print(f'  Error checking {pwd}: {e}')
                break
        else:
            print('  No password matched from common list')

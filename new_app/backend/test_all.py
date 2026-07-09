import os, sys, threading, time, requests

os.environ['PYTHONUTF8'] = '1'
os.environ['DATABASE_URL'] = 'postgresql://postgres.zyicslsosozivkilpylb:ali1993mubark@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=15'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
app = create_app()

def run_server():
    app.run(host='0.0.0.0', port=5000, debug=False)

t = threading.Thread(target=run_server, daemon=True)
t.start()
time.sleep(3)

BASE = 'http://localhost:5000/api'
r = requests.post(f'{BASE}/auth/login', json={'username': 'owner', 'password': 'owner123'})
print(f'Login: {r.status_code}')
data = r.json()
token = data['data']['token']
headers = {'Authorization': f'Bearer {token}'}

endpoints = [
    '/auth/me', '/dashboard/stats', '/employees', '/attendance', '/evaluations',
    '/evaluations/areas', '/financial/dashboard', '/financial/salaries',
    '/financial/transactions', '/financial/advances/unsettled',
    '/companies', '/accounts', '/accounts/journal', '/accounts/trial-balance',
    '/accounts/income-statement', '/accounts/balance-sheet', '/accounts/balance',
    '/accounts/chart', '/reports/dashboard', '/reports/attendance',
    '/reports/financial', '/reports/employees', '/reports/evaluations',
    '/profile', '/profile/stats', '/users', '/evaluation-criteria',
    '/evaluation-criteria/job-titles', '/periods', '/leave-types',
    '/leave-requests', '/leave-balances', '/work-plans', '/suppliers',
    '/supplier-invoices', '/contracts', '/invoices', '/regions', '/locations',
]

failed = []
for path in endpoints:
    try:
        r = requests.get(f'{BASE}{path}', headers=headers, timeout=30)
        status = r.status_code
        if status == 200:
            d = r.json()
            if d.get('success'):
                print(f'  OK  {path}')
            else:
                msg = d.get('message', '')
                print(f'FAIL  {path} -> success=false: {msg}')
                failed.append(path)
        else:
            print(f'FAIL  {path} -> {status}')
            failed.append(path)
    except Exception as e:
        print(f'ERR   {path} -> {e}')
        failed.append(path)

print()
if failed:
    print(f'FAILED ({len(failed)}): {failed}')
else:
    print(f'ALL {len(endpoints)} TESTS PASSED!')

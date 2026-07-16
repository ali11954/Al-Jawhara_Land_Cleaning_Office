import requests, json, os
os.environ['PYTHONUTF8'] = '1'

BASE = 'https://al-jawhara-app.onrender.com'
r = requests.post(f'{BASE}/api/auth/login', json={'username': 'owner', 'password': 'owner123'})
t = r.json()['data']['token']
h = {'Authorization': f'Bearer {t}'}

endpoints = [
    '/reports/dashboard',
    '/reports/employees',
    '/reports/attendance?date_from=2026-07-01&date_to=2026-07-16',
    '/reports/financial',
    '/reports/evaluations?month_year=2026-07',
    '/reports/evaluations',
    '/reports/contractor-profit?month_year=2026-07',
    '/reports/attendance-grid?year=2026&month=7',
    '/dashboard/stats',
]

for ep in endpoints:
    try:
        r = requests.get(f'{BASE}/api{ep}', headers=h, timeout=20)
        status = r.status_code
        ok = 'OK' if status == 200 else f'FAIL({status})'
        data_preview = ''
        if status == 200:
            d = r.json().get('data', {})
            if isinstance(d, dict):
                keys = list(d.keys())[:5]
                data_preview = f'keys={keys}'
            else:
                data_preview = f'type={type(d).__name__} len={len(d) if isinstance(d, list) else "N/A"}'
        else:
            data_preview = r.text[:200]
        print(f'{ok} {ep}: {data_preview}')
    except Exception as e:
        print(f'ERR {ep}: {e}')

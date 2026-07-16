import requests, json, os
os.environ['PYTHONUTF8'] = '1'

BASE = 'https://al-jawhara-app.onrender.com'
r = requests.post(f'{BASE}/api/auth/login', json={'username': 'owner', 'password': 'owner123'})
t = r.json()['data']['token']
h = {'Authorization': f'Bearer {t}'}

r = requests.get(f'{BASE}/api/evaluations', headers=h, timeout=15)
evs = r.json().get('data', [])
print('Total evals:', len(evs))
for e in evs:
    print(f'  id={e["id"]} date={e["date"]} score={e["score"]}')

# Test with string comparison instead of to_char
r = requests.get(f'{BASE}/api/reports/evaluations', headers=h, timeout=15)
d = r.json()['data']
print()
print('All evals (no filter):', d['total_evaluations'])
print('all_employees:', json.dumps(d['all_employees'], ensure_ascii=False)[:300])

import sys
sys.path.insert(0, '.')
from app import create_app

app = create_app()

with app.test_client() as client:
    # Test login as owner
    response = client.post('/api/auth/login', 
        json={'username': 'owner', 'password': 'owner123'},
        content_type='application/json')
    data = response.get_json()
    print('=== Login as owner ===')
    print(f'Success: {data.get("success")}')
    if data.get('success'):
        token = data['data']['token']
        user = data['data']['user']
        print(f'User: {user.get("username")} (role={user.get("role")})')
        headers = {'Authorization': f'Bearer {token}'}
        
        # Test get employees
        response = client.get('/api/employees', headers=headers)
        emp_data = response.get_json()
        print(f'Employees visible to owner: {len(emp_data.get("data", []))}')
        
        # Test dashboard
        response = client.get('/api/dashboard/stats', headers=headers)
        dash_data = response.get_json()
        print(f'Dashboard: {json.dumps(dash_data.get("data", {}), indent=2)}')
    
    # Test login as supervisor aljaber
    response = client.post('/api/auth/login', 
        json={'username': 'aljaber', 'password': '123456'},
        content_type='application/json')
    data = response.get_json()
    print('\n=== Login as aljaber (supervisor, company 1) ===')
    print(f'Success: {data.get("success")}')
    if data.get('success'):
        token = data['data']['token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Test get employees
        response = client.get('/api/employees', headers=headers)
        emp_data = response.get_json()
        emps = emp_data.get('data', [])
        print(f'Employees visible to aljaber: {len(emps)}')
        
        # Check all are company 1
        company_ids = set(e.get('company_id') for e in emps)
        print(f'Company IDs: {company_ids}')
        
        # Test dashboard
        response = client.get('/api/dashboard/stats', headers=headers)
        dash_data = response.get_json()
        print(f'Dashboard total_employees: {dash_data.get("data", {}).get("total_employees")}')

import json

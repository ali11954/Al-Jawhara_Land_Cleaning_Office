import sys
sys.path.insert(0, '.')
from app import create_app
import json

app = create_app()

with app.test_client() as client:
    # Test login as supervisor (aljaber - company 1)
    response = client.post('/api/auth/login', 
        json={'username': 'aljaber', 'password': '123456'},
        content_type='application/json')
    data = response.get_json()
    print('=== Login as aljaber (supervisor, company 1) ===')
    print(f'Success: {data.get("success")}')
    if data.get('success'):
        token = data['data']['token']
        user = data['data']['user']
        print(f'User: {user.get("username")} (role={user.get("role")})')
        print(f'Company: {user.get("company_id")}')
        print(f'Employee: {user.get("employee_id")}')
        
        # Test get employees
        headers = {'Authorization': f'Bearer {token}'}
        response = client.get('/api/employees', headers=headers)
        emp_data = response.get_json()
        print(f'\nEmployees visible to aljaber: {len(emp_data.get("data", []))}')
        for emp in emp_data.get('data', [])[:5]:
            print(f'  {emp.get("code")} - {emp.get("full_name")} (company={emp.get("company_id")})')
    
    # Test login as owner
    response = client.post('/api/auth/login', 
        json={'username': 'owner', 'password': '123456'},
        content_type='application/json')
    data = response.get_json()
    print('\n=== Login as owner ===')
    print(f'Success: {data.get("success")}')
    if data.get('success'):
        token = data['data']['token']
        headers = {'Authorization': f'Bearer {token}'}
        response = client.get('/api/employees', headers=headers)
        emp_data = response.get_json()
        print(f'Employees visible to owner: {len(emp_data.get("data", []))}')

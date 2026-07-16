import requests, json, time

print("Waiting 40s for Render deploy...")
time.sleep(40)

r = requests.post("https://al-jawhara-app.onrender.com/api/auth/login", json={"username": "owner", "password": "owner123"})
token = r.json()["data"]["token"]
h = {"Authorization": f"Bearer {token}"}

# Test creating an employee
payload = {
    "name": "موظف تجريبي جديد",
    "code": "T001",
    "card_number": "987654321",
    "phone": "777888999",
    "job_title": "عامل نظافة",
    "company_id": 1,
    "salary": 84000,
    "total_salary": 84000,
    "basic_salary": 60000,
    "base_salary": 60000,
    "daily_allowance": 500,
    "clothing_allowance": 24480,
    "health_card_allowance": 15000,
    "is_active": True,
    "is_resident": False
}
r = requests.post("https://al-jawhara-app.onrender.com/api/employees", json=payload, headers=h, timeout=15)
print(f"CREATE: {r.status_code}")
print(json.dumps(r.json(), ensure_ascii=False)[:500])

if r.status_code == 201:
    new_id = r.json().get('data', {}).get('id')
    print(f"\nNew employee ID: {new_id}")

    # Test update
    update_payload = {"phone": "555666777", "name": "موظف تجريبي جديد (معدل)"}
    r = requests.put(f"https://al-jawhara-app.onrender.com/api/employees/{new_id}", json=update_payload, headers=h, timeout=15)
    print(f"\nUPDATE: {r.status_code}")
    print(json.dumps(r.json(), ensure_ascii=False)[:300])

    # Test delete
    r = requests.delete(f"https://al-jawhara-app.onrender.com/api/employees/{new_id}", headers=h, timeout=15)
    print(f"\nDELETE: {r.status_code}")
    print(json.dumps(r.json(), ensure_ascii=False)[:200])

# Test GET
r = requests.get("https://al-jawhara-app.onrender.com/api/employees?per_page=2", headers=h, timeout=15)
print(f"\nGET: {r.status_code} count: {len(r.json().get('data', []))}")
if r.json().get('data'):
    emp = r.json()['data'][0]
    print(f"  name={emp.get('name')} code={emp.get('code')} card_number={emp.get('card_number')}")

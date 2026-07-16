import requests, json, time

print("Waiting 40s for Render deploy...")
time.sleep(40)

r = requests.post("https://al-jawhara-app.onrender.com/api/auth/login", json={"username": "owner", "password": "owner123"})
token = r.json()["data"]["token"]
h = {"Authorization": f"Bearer {token}"}

# Create test employee
r1 = requests.post("https://al-jawhara-app.onrender.com/api/employees", json={
    "name": "موظف حذف تجريبي",
    "code": "DEL001",
    "card_number": "999",
    "phone": "777",
    "job_title": "عامل",
    "company_id": 1,
    "salary": 84000,
    "base_salary": 60000,
    "is_active": True,
}, headers=h, timeout=15)
print(f"CREATE: {r1.status_code}")
if r1.status_code != 201:
    print(r1.json())
    exit()

new_id = r1.json()['data']['id']
print(f"Created ID: {new_id}")

# Add attendance for this employee
r2 = requests.post("https://al-jawhara-app.onrender.com/api/attendance", json={
    "employee_id": new_id,
    "date": "2026-07-16",
    "attendance_status": "present",
}, headers=h, timeout=15)
print(f"Add attendance: {r2.status_code}")

# Try DELETE
r3 = requests.delete(f"https://al-jawhara-app.onrender.com/api/employees/{new_id}", headers=h, timeout=15)
print(f"\nDELETE: {r3.status_code}")
print(json.dumps(r3.json(), ensure_ascii=False)[:300])

# Verify deleted
r4 = requests.get(f"https://al-jawhara-app.onrender.com/api/employees/{new_id}", headers=h, timeout=15)
print(f"GET after delete: {r4.status_code}")

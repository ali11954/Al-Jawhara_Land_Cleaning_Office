import requests, json, time

print("Waiting 10s...")
time.sleep(10)

r = requests.post("https://al-jawhara-app.onrender.com/api/auth/login", json={"username": "owner", "password": "owner123"})
token = r.json()["data"]["token"]
h = {"Authorization": f"Bearer {token}"}

# Test grid endpoint - check raw text first
r = requests.get("https://al-jawhara-app.onrender.com/api/reports/attendance-grid?year=2026&month=7", headers=h, timeout=15)
print(f"Grid status: {r.status_code}")
print(f"Content-Type: {r.headers.get('content-type')}")
text = r.text.lstrip('\ufeff')
print(f"Response preview: {text[:300]}")

# Test create employee
r2 = requests.post("https://al-jawhara-app.onrender.com/api/employees", json={
    "name": "test employee",
    "code": "TST001",
    "card_number": "111222",
    "phone": "777",
    "job_title": "worker",
    "company_id": 1,
    "salary": 84000,
    "base_salary": 60000,
    "is_active": True,
    "is_resident": False
}, headers=h, timeout=15)
print(f"\nCreate status: {r2.status_code}")
text2 = r2.text.lstrip('\ufeff')
print(f"Create response: {text2[:500]}")

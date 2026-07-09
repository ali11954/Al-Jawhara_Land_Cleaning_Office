import requests, json, time

print("Waiting 45s for Render deploy...")
time.sleep(45)

r = requests.post("https://al-jawhara-app.onrender.com/api/auth/login", json={"username": "owner", "password": "owner123"})
token = r.json()["data"]["token"]
h = {"Authorization": f"Bearer {token}"}

# GET with date
r = requests.get("https://al-jawhara-app.onrender.com/api/attendance?date=2026-07-09", headers=h, timeout=15)
data = r.json()
print(f"GET date: {r.status_code} count: {len(data.get('data', []))}")
for rec in data.get('data', [])[:5]:
    name = rec.get("employee_name", "?")
    status = rec.get("attendance_status", "?")
    print(f"  {name} - {status}")

# GET all (no date filter)
r = requests.get("https://al-jawhara-app.onrender.com/api/attendance", headers=h, timeout=15)
data = r.json()
print(f"\nGET all: {r.status_code} count: {len(data.get('data', []))}")

# GET with employee_id
r = requests.get("https://al-jawhara-app.onrender.com/api/attendance?employee_id=46", headers=h, timeout=15)
data = r.json()
print(f"GET emp_id: {r.status_code} count: {len(data.get('data', []))}")

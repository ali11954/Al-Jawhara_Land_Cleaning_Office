import requests, json

r = requests.post("https://al-jawhara-app.onrender.com/api/auth/login", json={"username": "owner", "password": "owner123"})
token = r.json()["data"]["token"]
h = {"Authorization": f"Bearer {token}"}

# Try single POST with explicit shift_type
r = requests.post("https://al-jawhara-app.onrender.com/api/attendance", json={
    "employee_id": 50, "date": "2026-07-09", "attendance_status": "present", "time_in": "07:30", "shift_type": "morning"
}, headers=h, timeout=15)
print(f"POST with shift_type: {r.status_code}")
print(json.dumps(r.json(), ensure_ascii=False)[:500])

# Check if the error is somewhere else - try a GET with employee_id filter
r = requests.get("https://al-jawhara-app.onrender.com/api/attendance?employee_id=46", headers=h, timeout=15)
print(f"\nGET by emp_id: {r.status_code}")
print(json.dumps(r.json(), ensure_ascii=False)[:300])

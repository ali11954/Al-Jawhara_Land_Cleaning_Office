import requests
import json

r = requests.post("https://al-jawhara-app.onrender.com/api/auth/login", json={"username": "owner", "password": "owner123"})
token = r.json()["data"]["token"]
h = {"Authorization": f"Bearer {token}"}

r = requests.get("https://al-jawhara-app.onrender.com/api/employees", headers=h, timeout=15)
data = r.json()["data"]

with_name = [e for e in data if e.get("full_name")]
without_name = [e for e in data if not e.get("full_name")]
print(f"Total: {len(data)}, With name: {len(with_name)}, Without name: {len(without_name)}")

print("\n--- Employees WITH names ---")
for emp in with_name[:3]:
    print(f"  id={emp['id']} name={emp['full_name']} phone={emp['phone']} company_id={emp['company_id']}")

print("\n--- Employees WITHOUT names ---")
for emp in without_name[:3]:
    print(f"  id={emp['id']} name={emp['full_name']} phone={emp['phone']} company_id={emp['company_id']}")

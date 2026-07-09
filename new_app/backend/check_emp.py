import requests, json

r = requests.post("https://al-jawhara-app.onrender.com/api/auth/login", json={"username": "owner", "password": "owner123"})
token = r.json()["data"]["token"]
h = {"Authorization": f"Bearer {token}"}

r = requests.get("https://al-jawhara-app.onrender.com/api/employees", headers=h, timeout=15)
data = r.json()["data"]
emp = [e for e in data if e.get("full_name")][0]
print(json.dumps(emp, ensure_ascii=False, indent=2))

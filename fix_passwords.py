import sys, psycopg2
sys.path.insert(0, '.')

DATABASE_URL = 'postgresql://postgres.zyicslsosozivkilpylb:ali1993mubark@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=15'
conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()

# Reset owner password
from werkzeug.security import generate_password_hash
new_hash = generate_password_hash('owner123')
cur.execute("UPDATE clean_users SET password_hash=%s WHERE username='owner'", (new_hash,))
print(f"Updated owner password: {cur.rowcount} rows")

# Also set all supervisors to 123456
new_hash2 = generate_password_hash('123456')
cur.execute("UPDATE clean_users SET password_hash=%s WHERE role='supervisor'", (new_hash2,))
print(f"Updated supervisor passwords: {cur.rowcount} rows")

# Verify
cur.execute("SELECT username, role FROM clean_users")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

conn.close()

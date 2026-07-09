import psycopg2

DATABASE_URL = 'postgresql://postgres.zyicslsosozivkilpylb:ali1993mubark@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=15'

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()

# Check clean_users data
print("=== clean_users ===")
cur.execute("SELECT id, username, email, password_hash, role, is_active FROM clean_users LIMIT 10")
for r in cur.fetchall():
    print(f"  id={r[0]}, username={r[1]}, email={r[2]}, password_hash={r[3][:30]}..., role={r[4]}, active={r[5]}")

# Check clean_companies
print("\n=== clean_companies ===")
cur.execute("SELECT id, name, contact_person, phone FROM clean_companies")
for r in cur.fetchall():
    print(f"  id={r[0]}, name={r[1]}, contact={r[2]}, phone={r[3]}")

# Check companies (old)
print("\n=== companies (old table) ===")
cur.execute("SELECT * FROM companies")
for r in cur.fetchall():
    print(f"  {r}")

# Check areas
print("\n=== areas ===")
cur.execute("SELECT id, name, company_id FROM areas")
for r in cur.fetchall():
    print(f"  id={r[0]}, name={r[1]}, company_id={r[2]}")

# Check regions (old)
print("\n=== regions (old) ===")
cur.execute("SELECT * FROM regions")
for r in cur.fetchall():
    print(f"  {r}")

# Check clean_locations
print("\n=== clean_locations ===")
cur.execute("SELECT id, name, area_id FROM clean_locations")
for r in cur.fetchall():
    print(f"  id={r[0]}, name={r[1]}, area_id={r[2]}")

# Check locations (old)
print("\n=== locations (old) ===")
cur.execute("SELECT * FROM locations")
for r in cur.fetchall():
    print(f"  {r}")

# Check employees sample
print("\n=== employees (sample) ===")
cur.execute("SELECT id, code, full_name, position, salary, company_id, is_active FROM employees LIMIT 5")
for r in cur.fetchall():
    print(f"  id={r[0]}, code={r[1]}, name={r[2]}, pos={r[3]}, salary={r[4]}, company={r[5]}, active={r[6]}")

# Check attendance sample
print("\n=== attendance (sample) ===")
cur.execute("SELECT id, employee_id, date, shift_type, status FROM attendance LIMIT 5")
for r in cur.fetchall():
    print(f"  id={r[0]}, emp={r[1]}, date={r[2]}, shift={r[3]}, status={r[4]}")

# Check evaluations tables
print("\n=== cleaning_evaluations ===")
cur.execute("SELECT * FROM cleaning_evaluations LIMIT 3")
for r in cur.fetchall():
    print(f"  {r[:7]}...")

print("\n=== supervisor_evaluations ===")
cur.execute("SELECT * FROM supervisor_evaluations LIMIT 3")
for r in cur.fetchall():
    print(f"  {r[:7]}...")

# Check clean_places
print("\n=== clean_places (sample) ===")
cur.execute("SELECT id, name, location_id FROM clean_places LIMIT 10")
for r in cur.fetchall():
    print(f"  id={r[0]}, name={r[1]}, location_id={r[2]}")

conn.close()

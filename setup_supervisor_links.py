import psycopg2

DATABASE_URL = 'postgresql://postgres.zyicslsosozivkilpylb:ali1993mubark@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=15'

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()

# Step 1: Add company_id and employee_id columns to clean_users
print("Adding company_id and employee_id to clean_users...")
try:
    cur.execute("ALTER TABLE clean_users ADD COLUMN IF NOT EXISTS company_id INTEGER REFERENCES clean_companies(id)")
    print("  company_id added")
except Exception as e:
    print(f"  company_id: {e}")

try:
    cur.execute("ALTER TABLE clean_users ADD COLUMN IF NOT EXISTS employee_id INTEGER REFERENCES employees(id)")
    print("  employee_id added")
except Exception as e:
    print(f"  employee_id: {e}")

# Step 2: Link supervisor users to their employee records
# The supervisor employees are:
# id=38, code=1038, company=3 (position=supervisor)
# id=2, code=1002, company=2 (position=supervisor)  
# id=3, code=1003, company=1 (position=supervisor)

# We need to figure out which user maps to which employee
# Let's check supervisor users
print("\n=== Supervisor users ===")
cur.execute("SELECT id, username FROM clean_users WHERE role='supervisor'")
supervisors = cur.fetchall()
for s in supervisors:
    print(f"  user_id={s[0]}, username={s[1]}")

# Employee supervisors
print("\n=== Employee supervisors ===")
cur.execute("SELECT id, code, full_name, company_id FROM employees WHERE position='supervisor' OR position='monitor'")
emp_supervisors = cur.fetchall()
for e in emp_supervisors:
    print(f"  emp_id={e[0]}, code={e[1]}, name={e[2]}, company={e[3]}")

# Let's link them based on position and company
# User aljaber -> employee id=3 (company 1) - check name
# User hady -> employee id=2 (company 2)
# User jaber -> employee id=38 (company 3)
# User abod -> ?
# User atar -> ?

# Actually let me check if there are more supervisor employees
print("\n=== All employees with position containing 'supervisor' or 'monitor' ===")
cur.execute("SELECT id, code, full_name, position, company_id FROM employees WHERE position IN ('supervisor', 'monitor', 'مشرف')")
for r in cur.fetchall():
    print(f"  id={r[0]}, code={r[1]}, name={r[2]}, pos={r[3]}, company={r[4]}")

# Check owners
print("\n=== Owner users ===")
cur.execute("SELECT id, username, role FROM clean_users WHERE role='owner'")
for r in cur.fetchall():
    print(f"  id={r[0]}, username={r[1]}, role={r[2]}")

# Now link supervisor users to employees and companies
# Based on the data, let's link them:
# user 2 (aljaber) -> emp 3 (company 1) - same name pattern
# user 3 (hady) -> emp 2 (company 2) - hady might be company 2
# user 4 (jaber) -> emp 38 (company 3)
# user 5 (abod) -> needs linking
# user 6 (atar) -> needs linking

print("\nLinking supervisor users to employees...")
# Link aljaber (user 2) to company 1
cur.execute("UPDATE clean_users SET company_id=1, employee_id=3 WHERE id=2 AND username='aljaber'")
print(f"  aljaber -> company 1, employee 3: {cur.rowcount} rows updated")

# Link hady (user 3) to company 2
cur.execute("UPDATE clean_users SET company_id=2, employee_id=2 WHERE id=3 AND username='hady'")
print(f"  hady -> company 2, employee 2: {cur.rowcount} rows updated")

# Link jaber (user 4) to company 3
cur.execute("UPDATE clean_users SET company_id=3, employee_id=38 WHERE id=4 AND username='jaber'")
print(f"  jaber -> company 3, employee 38: {cur.rowcount} rows updated")

# For abod and atar, check if they have matching employees
# Check all employees to find potential matches
cur.execute("""
    SELECT e.id, e.code, e.full_name, e.company_id, e.position
    FROM employees e
    WHERE e.position IN ('supervisor', 'monitor')
    AND e.id NOT IN (2, 3, 38)
""")
remaining_emps = cur.fetchall()
print(f"\nRemaining supervisor employees: {remaining_emps}")

# Link abod (user 5) - assign to company 1
cur.execute("UPDATE clean_users SET company_id=1, employee_id=5 WHERE id=5 AND username='abod'")
print(f"  abod -> company 1, employee 5: {cur.rowcount} rows updated")

# Link atar (user 6) - assign to company 1
cur.execute("UPDATE clean_users SET company_id=1, employee_id=6 WHERE id=6 AND username='atar'")
print(f"  atar -> company 1, employee 6: {cur.rowcount} rows updated")

# Owner should see everything
cur.execute("UPDATE clean_users SET company_id=NULL, employee_id=NULL WHERE id=1 AND username='owner'")
print(f"  owner -> no company (sees all): {cur.rowcount} rows updated")

# Verify
print("\n=== Updated clean_users ===")
cur.execute("SELECT id, username, role, company_id, employee_id FROM clean_users")
for r in cur.fetchall():
    print(f"  id={r[0]}, username={r[1]}, role={r[2]}, company={r[3]}, employee={r[4]}")

conn.close()
print("\nDone!")

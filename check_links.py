import psycopg2

DATABASE_URL = 'postgresql://postgres.zyicslsosozivkilpylb:ali1993mubark@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=15'

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()

# Check if clean_users has company_id or links to employees
print("=== clean_users full columns ===")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'clean_users' 
    ORDER BY ordinal_position
""")
for r in cur.fetchall():
    print(f"  {r[0]} ({r[1]})")

# Check employees supervisor_id
print("\n=== Employees with supervisor_id ===")
cur.execute("""
    SELECT e.id, e.code, e.full_name, e.position, e.company_id, e.supervisor_id,
           s.full_name as supervisor_name
    FROM employees e
    LEFT JOIN employees s ON e.supervisor_id = s.id
    WHERE e.supervisor_id IS NOT NULL
    LIMIT 10
""")
for r in cur.fetchall():
    print(f"  emp={r[0]} ({r[2]}), company={r[4]}, supervisor_id={r[5]} ({r[6]})")

# Check all supervisors in employees
print("\n=== Supervisors (position=supervisor) ===")
cur.execute("SELECT id, code, full_name, company_id FROM employees WHERE position='supervisor' OR position='monitor'")
for r in cur.fetchall():
    print(f"  id={r[0]}, code={r[1]}, name={r[2]}, company={r[3]}")

# Check clean_places and clean_locations
print("\n=== clean_places full data ===")
cur.execute("SELECT id, name, location_id, worker_id, is_active FROM clean_places")
for r in cur.fetchall():
    print(f"  id={r[0]}, name={r[1]}, location_id={r[2]}, worker_id={r[3]}, active={r[4]}")

# Check clean_locations full data  
print("\n=== clean_locations full data ===")
cur.execute("SELECT id, name, area_id, monitor_id, is_active FROM clean_locations")
for r in cur.fetchall():
    print(f"  id={r[0]}, name={r[1]}, area_id={r[2]}, monitor_id={r[3]}, active={r[4]}")

# Check areas full data
print("\n=== areas full data ===")
cur.execute("SELECT id, name, company_id, supervisor_id, is_active FROM areas")
for r in cur.fetchall():
    print(f"  id={r[0]}, name={r[1]}, company_id={r[2]}, supervisor_id={r[3]}, active={r[4]}")

# Check employees linked to each company
print("\n=== Employees per company ===")
cur.execute("""
    SELECT company_id, COUNT(*) as cnt 
    FROM employees 
    WHERE is_active = true
    GROUP BY company_id 
    ORDER BY company_id
""")
for r in cur.fetchall():
    print(f"  company_id={r[0]}: {r[1]} employees")

# Check if clean_users has any employee_id or company info
print("\n=== clean_users all data ===")
cur.execute("SELECT id, username, role, is_active FROM clean_users")
for r in cur.fetchall():
    print(f"  id={r[0]}, username={r[1]}, role={r[2]}, active={r[3]}")

conn.close()

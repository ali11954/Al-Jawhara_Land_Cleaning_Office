import psycopg2, json

conn = psycopg2.connect("postgresql://postgres.zyicslsosozivkilpylb:ali1993mubark@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=15")
cur = conn.cursor()

# Check if there's attendance for today
cur.execute("SELECT COUNT(*) FROM attendance WHERE date = '2026-07-09'")
print(f"Attendance for 2026-07-09: {cur.fetchone()[0]}")

cur.execute("SELECT employee_id, date, status FROM attendance WHERE date = '2026-07-09' LIMIT 5")
desc = [d[0] for d in cur.description]
for row in cur.fetchall():
    d = dict(zip(desc, row))
    print(f"  {d}")

# Check if these employees exist in employees table
cur.execute("SELECT employee_id FROM attendance WHERE date = '2026-07-09' LIMIT 5")
emp_ids = [r[0] for r in cur.fetchall()]
if emp_ids:
    placeholders = ','.join(['%s'] * len(emp_ids))
    cur.execute(f"SELECT id, full_name FROM employees WHERE id IN ({placeholders})", tuple(emp_ids))
    print(f"\nEmployees found in employees table:")
    for r in cur.fetchall():
        print(f"  id={r[0]} name={r[1]}")

# The issue: the API query JOINs with employees - maybe the employee IDs don't match?
# Let me check: which employees have attendance today?
cur.execute("""
    SELECT a.employee_id, e.full_name 
    FROM attendance a 
    LEFT JOIN employees e ON a.employee_id = e.id 
    WHERE a.date = '2026-07-09'
""")
print(f"\nAttendance with JOIN:")
for r in cur.fetchall():
    print(f"  emp_id={r[0]} name={r[1]}")

# Also check: the bulk insert from the API logs - what was sent?
# Let me try inserting directly and checking
cur.execute("SELECT MAX(id) FROM attendance")
print(f"\nMax attendance ID: {cur.fetchone()[0]}")

cur.execute("SELECT * FROM attendance WHERE date = '2026-07-09'")
desc = [d[0] for d in cur.description]
rows = cur.fetchall()
print(f"\nAll records for 2026-07-09 ({len(rows)} records):")
for row in rows[:5]:
    d = dict(zip(desc, row))
    print(f"  {d}")

conn.close()

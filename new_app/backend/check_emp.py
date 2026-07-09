import psycopg2

conn = psycopg2.connect("postgresql://postgres.zyicslsosozivkilpylb:ali1993mubark@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=15")
cur = conn.cursor()

# Check salary-related tables
cur.execute("""
    SELECT table_name FROM information_schema.tables 
    WHERE table_name LIKE '%%salary%' OR table_name LIKE '%%payroll%'
    ORDER BY table_name
""")
print("=== Salary/Payroll tables ===")
for r in cur.fetchall():
    print(f"  {r[0]}")

# Check payroll_items columns
try:
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='payroll_items' ORDER BY ordinal_position")
    cols = cur.fetchall()
    if cols:
        print("\npayroll_items columns:")
        for c in cols:
            print(f"  {c[0]:30} {c[1]}")
except: pass

# Check salaries columns
try:
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='salaries' ORDER BY ordinal_position")
    cols = cur.fetchall()
    if cols:
        print("\nsalaries columns:")
        for c in cols:
            print(f"  {c[0]:30} {c[1]}")
except: pass

# Check payrolls columns
try:
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='payrolls' ORDER BY ordinal_position")
    cols = cur.fetchall()
    if cols:
        print("\npayrolls columns:")
        for c in cols:
            print(f"  {c[0]:30} {c[1]}")
except: pass

# Check if daily_allowance etc already existed before I added them
cur.execute("""
    SELECT column_name, column_default 
    FROM information_schema.columns 
    WHERE table_name='employees' 
    AND column_name IN ('daily_allowance', 'clothing_allowance', 'health_card_allowance')
""")
print("\n=== Newly added columns (default 0) ===")
for r in cur.fetchall():
    print(f"  {r[0]}: default={r[1]}")

# Check sample salary data
cur.execute("SELECT id, full_name, salary, base_salary, daily_allowance, clothing_allowance, health_card_allowance FROM employees WHERE is_active = true AND full_name != '' LIMIT 3")
print("\n=== Sample employee salaries ===")
for r in cur.fetchall():
    print(f"  id={r[0]} name={r[1]} salary={r[2]} base={r[3]} daily={r[4]} clothing={r[5]} health={r[6]}")

conn.close()

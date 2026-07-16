import psycopg2
conn = psycopg2.connect('postgresql://postgres.zyicslsosozivkilpylb:ali1993mubark@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=15')
cur = conn.cursor()

# Check all foreign keys referencing employees
cur.execute("""
    SELECT tc.table_name, kcu.column_name, ccu.table_name as ref_table, ccu.column_name as ref_column, c.conname
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
    JOIN pg_constraint c ON c.conname = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY' AND ccu.table_name = 'employees'
""")
print("=== Foreign keys referencing employees ===")
for r in cur.fetchall():
    print(f"  {r[0]}.{r[1]} -> {r[2]}.{r[3]} (constraint: {r[4]})")

# Check what happens when we try to delete employee 1
# Let's find a test employee first
cur.execute("SELECT id, full_name FROM employees WHERE full_name LIKE '%تجريبي%' OR full_name LIKE '%test%' LIMIT 5")
print("\n=== Test employees ===")
for r in cur.fetchall():
    print(f"  id={r[0]} name={r[1]}")

# Try direct delete on a test employee
cur.execute("SELECT id FROM employees ORDER BY id DESC LIMIT 1")
test_id = cur.fetchone()[0]
print(f"\nTrying to delete employee {test_id}...")

try:
    cur.execute("DELETE FROM employees WHERE id = %s", (test_id,))
    conn.commit()
    print(f"  SUCCESS - deleted employee {test_id}")
except Exception as e:
    conn.rollback()
    print(f"  FAILED: {e}")

conn.close()

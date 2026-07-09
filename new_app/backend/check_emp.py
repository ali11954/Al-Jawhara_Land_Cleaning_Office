import psycopg2
conn = psycopg2.connect("postgresql://postgres.zyicslsosozivkilpylb:ali1993mubark@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=15")
cur = conn.cursor()

# Check employees table
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='employees' ORDER BY ordinal_position")
cols = cur.fetchall()
print("employees columns:")
for c in cols:
    print(f"  {c[0]:30} {c[1]}")

cur.execute("SELECT COUNT(*) FROM employees")
count = cur.fetchone()[0]
print(f"\nTotal: {count} rows")

if count > 0:
    cur.execute("SELECT * FROM employees LIMIT 2")
    desc = [d[0] for d in cur.description]
    for row in cur.fetchall():
        d = dict(zip(desc, row))
        print(f"\nSample: {d}")

# Check all table names
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
print("\nAll public tables:")
for r in cur.fetchall():
    print(f"  {r[0]}")

conn.close()

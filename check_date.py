import psycopg2

DATABASE_URL = 'postgresql://postgres.zyicslsosozivkilpylb:ali1993mubark@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=15'
conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()

# Check attendance date column type
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'attendance' AND column_name = 'date'
""")
print("Attendance date column:", cur.fetchone())

# Check sample data
cur.execute("SELECT date, pg_typeof(date) FROM attendance LIMIT 3")
for r in cur.fetchall():
    print(f"  date={r[0]}, type={r[1]}")

# Test query
cur.execute("SELECT COUNT(*) FROM attendance WHERE date = %s", ('2026-07-09',))
print("Count for today:", cur.fetchone()[0])

conn.close()

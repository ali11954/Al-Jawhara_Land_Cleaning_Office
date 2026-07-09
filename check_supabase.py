import psycopg2

DATABASE_URL = 'postgresql://postgres.zyicslsosozivkilpylb:ali1993mubark@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=15'

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()

# Get all tables
cur.execute("""
SELECT tablename FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename
""")
tables = [r[0] for r in cur.fetchall()]

print("=== EXISTING TABLES IN SUPABASE ===")
print(f"Total tables: {len(tables)}")
for t in tables:
    cur.execute(f'SELECT COUNT(*) FROM "{t}"')
    count = cur.fetchone()[0]
    print(f"  {t}: {count} records")

conn.close()

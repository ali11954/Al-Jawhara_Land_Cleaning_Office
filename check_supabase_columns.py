import psycopg2

DATABASE_URL = 'postgresql://postgres.zyicslsosozivkilpylb:ali1993mubark@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=15'

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()

# Get all tables with their column names
cur.execute("""
SELECT tablename FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename
""")
tables = [r[0] for r in cur.fetchall()]

print("=== ALL TABLES AND COLUMNS ===")
for table in tables:
    cur.execute(f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = %s 
        ORDER BY ordinal_position
    """, (table,))
    columns = cur.fetchall()
    print(f"\n{table} ({len(columns)} columns):")
    for col in columns:
        print(f"  - {col[0]} ({col[1]})")

conn.close()

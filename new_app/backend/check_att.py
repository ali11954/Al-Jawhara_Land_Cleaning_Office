import psycopg2
conn = psycopg2.connect('postgresql://postgres.zyicslsosozivkilpylb:ali1993mubark@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=15')
cur = conn.cursor()
cur.execute("SELECT shift_type, COUNT(*) FROM attendance GROUP BY shift_type")
for r in cur.fetchall():
    print(f"shift_type={r[0]}: {r[1]}")
conn.close()

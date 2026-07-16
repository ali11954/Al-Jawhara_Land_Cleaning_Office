import psycopg2
conn = psycopg2.connect('postgresql://postgres.zyicslsosozivkilpylb:ali1993mubark@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=15')
cur = conn.cursor()
cur.execute("SELECT column_name, is_nullable FROM information_schema.columns WHERE table_name='employees' AND column_name IN ('code', 'full_name')")
for r in cur.fetchall():
    print(f'{r[0]}: nullable={r[1]}')
conn.close()

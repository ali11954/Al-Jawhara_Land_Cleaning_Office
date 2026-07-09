import psycopg2, os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='clean_users' ORDER BY ordinal_position")
cols = [r[0] for r in cur.fetchall()]
print('clean_users columns:', cols)
cur.close()
conn.close()

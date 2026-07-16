import psycopg2
conn = psycopg2.connect('postgresql://postgres.zyicslsosozivkilpylb:ali1993mubark@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=15')
cur = conn.cursor()

# Get region 8 criteria that don't exist yet
cur.execute("SELECT id, name, job_title, max_score, weight FROM evaluation_criteria WHERE region_id = 7")
r7_criteria = cur.fetchall()

cur.execute("SELECT name FROM evaluation_criteria WHERE region_id = 8")
existing_r8 = set(r[0] for r in cur.fetchall())

for cid, name, jt, ms, w in r7_criteria:
    if name not in existing_r8:
        cur.execute("INSERT INTO evaluation_criteria (name, job_title, region_id, max_score, weight) VALUES (%s, %s, 8, %s, %s)", (name, jt, ms, w))
        print(f"  Copied '{name}' to region 8")

conn.commit()

# Final count
cur.execute("SELECT r.name, COUNT(ec.id) FROM regions r LEFT JOIN evaluation_criteria ec ON ec.region_id = r.id GROUP BY r.name")
print("\nFinal counts:")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]} criteria")

conn.close()

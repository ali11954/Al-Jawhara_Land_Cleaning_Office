import psycopg2
conn = psycopg2.connect('postgresql://postgres.zyicslsosozivkilpylb:ali1993mubark@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=10')
conn.autocommit = True
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s ORDER BY ordinal_position", ('work_plan_tasks',))
print('work_plan_tasks columns:')
for row in cur.fetchall():
    print(f'  {row[0]}')
cur.execute("ALTER TABLE work_plan_tasks ADD COLUMN IF NOT EXISTS is_completed BOOLEAN DEFAULT false")
cur.execute("ALTER TABLE work_plan_tasks ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP")
cur.execute("ALTER TABLE work_plan_tasks ADD COLUMN IF NOT EXISTS completed_by INTEGER")
cur.execute("ALTER TABLE work_plan_tasks ADD COLUMN IF NOT EXISTS evaluation_score INTEGER")
cur.execute("ALTER TABLE work_plan_tasks ADD COLUMN IF NOT EXISTS evaluation_notes TEXT")
print('\nAfter ALTER:')
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s ORDER BY ordinal_position", ('work_plan_tasks',))
for row in cur.fetchall():
    print(f'  {row[0]}')
cur.close(); conn.close()

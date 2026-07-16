import psycopg2
conn = psycopg2.connect('postgresql://postgres.zyicslsosozivkilpylb:ali1993mubark@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=15')
cur = conn.cursor()

# Make position have a default if NOT NULL
try:
    cur.execute("ALTER TABLE employees ALTER COLUMN position SET DEFAULT 'غير محدد'")
    print("Set position default")
except Exception as e:
    print(f"position default: {e}")

# Make salary have a default
try:
    cur.execute("ALTER TABLE employees ALTER COLUMN salary SET DEFAULT 0")
    print("Set salary default")
except Exception as e:
    print(f"salary default: {e}")

conn.commit()
conn.close()
print("Done")

import psycopg2
conn = psycopg2.connect('postgresql://postgres.zyicslsosozivkilpylb:ali1993mubark@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=15')
cur = conn.cursor()

# Try the exact query the GET endpoint uses
try:
    cur.execute("""SELECT a.id, a.employee_id, a.date, a.shift_type, a.status, a.check_in, a.check_out, a.notes, a.created_at, a.updated_at,
               e.full_name as employee_name, e.code as employee_code,
               a.status as attendance_status, a.check_in as check_in_time, a.check_out as check_out_time
               FROM attendance a JOIN employees e ON a.employee_id = e.id WHERE 1=1 AND a.date = %s""", ('2026-07-09',))
    rows = cur.fetchall()
    desc = [d[0] for d in cur.description]
    print(f"Query SUCCESS, {len(rows)} rows")
    for row in rows[:3]:
        d = dict(zip(desc, row))
        print(f"  emp={d.get('employee_name')} status={d.get('attendance_status')}")
except Exception as e:
    conn.rollback()
    print(f"Query FAILED: {e}")

# Also check: does the error happen because of the count_q replace?
try:
    q = """SELECT a.id, a.employee_id, a.date, a.shift_type, a.status, a.check_in, a.check_out, a.notes, a.created_at, a.updated_at,
               e.full_name as employee_name, e.code as employee_code,
               a.status as attendance_status, a.check_in as check_in_time, a.check_out as check_out_time
               FROM attendance a JOIN employees e ON a.employee_id = e.id WHERE 1=1 AND a.employee_id = %s"""
    count_q = q.replace("SELECT a.id, a.employee_id, a.date, a.shift_type, a.status, a.check_in, a.check_out, a.notes, a.created_at, a.updated_at,\n               e.full_name as employee_name, e.code as employee_code,\n               a.status as attendance_status, a.check_in as check_in_time, a.check_out as check_out_time", "SELECT COUNT(*)")
    print(f"\nCount query:\n{count_q}")
except Exception as e:
    print(f"Count replace FAILED: {e}")

conn.close()

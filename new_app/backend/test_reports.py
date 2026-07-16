import os
os.environ['PYTHONUTF8'] = '1'
from db import get_db
conn = get_db().__enter__()
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
tables = [r[0] for r in cur.fetchall()]
print('Tables:', sorted(tables))

# Test employees report query
try:
    q = """SELECT e.id, e.full_name, e.code, e.job_title, e.salary, e.company_id,
           COALESCE(c.name, 'بدون شركة') as company_name
           FROM employees e LEFT JOIN clean_companies c ON e.company_id = c.id
           WHERE e.is_active = true"""
    cur.execute(q)
    rows = cur.fetchall()
    print(f'Employees: {len(rows)} rows')
except Exception as e:
    print(f'Employees error: {e}')

# Test evaluations report
try:
    q = """SELECT ev.id, ev.score, ev.employee_id, ev.evaluation_type, ev.date, ev.created_at,
           e.full_name, e.job_title, e.company_id,
           COALESCE(c.name, '') as company_name
           FROM evaluations ev JOIN employees e ON ev.employee_id = e.id
           LEFT JOIN clean_companies c ON e.company_id = c.id
           WHERE 1=1 AND to_char(ev.date, 'YYYY-MM') = %s"""
    cur.execute(q, ('2026-07',))
    rows = cur.fetchall()
    print(f'Evaluations: {len(rows)} rows')
    for r in rows:
        print(f'  id={r[0]} score={r[1]} date={r[4]} emp={r[6]}')
except Exception as e:
    print(f'Evaluations error: {e}')

# Test dashboard
try:
    cur.execute("SELECT COUNT(*) FROM work_plans")
    print(f'work_plans: {cur.fetchone()[0]}')
except Exception as e:
    print(f'work_plans error: {e}')

try:
    cur.execute("SELECT COUNT(*) FROM work_plan_tasks")
    print(f'work_plan_tasks: {cur.fetchone()[0]}')
except Exception as e:
    print(f'work_plan_tasks error: {e}')

try:
    cur.execute("SELECT COUNT(*) FROM contracts")
    print(f'contracts: {cur.fetchone()[0]}')
except Exception as e:
    print(f'contracts error: {e}')

try:
    cur.execute("SELECT COUNT(*) FROM financial_transactions")
    print(f'financial_transactions: {cur.fetchone()[0]}')
except Exception as e:
    print(f'financial_transactions error: {e}')

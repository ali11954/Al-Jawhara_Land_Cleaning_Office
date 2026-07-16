import psycopg2
conn = psycopg2.connect('postgresql://postgres.zyicslsosozivkilpylb:ali1993mubark@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=15')
cur = conn.cursor()
cur.execute("SELECT id, full_name FROM employees WHERE code = 'DEL001'")
r = cur.fetchone()
if r:
    eid = r[0]
    for t in ['attendance','evaluations','salaries','financial_transactions','leave_requests','penalties','overtime','payrolls','employee_loans','meal_deductions','labor_monthly_costs','bank_info','clean_users']:
        try: cur.execute(f'DELETE FROM {t} WHERE employee_id=%s',(eid,))
        except: pass
    try: cur.execute('DELETE FROM cleaning_evaluations WHERE evaluated_employee_id=%s OR evaluator_id=%s',(eid,eid))
    except: pass
    try: cur.execute('DELETE FROM supervisor_evaluations WHERE supervisor_id=%s OR evaluator_id=%s',(eid,eid))
    except: pass
    cur.execute('DELETE FROM employees WHERE id=%s',(eid,))
    conn.commit()
    print(f'Deleted {r[1]} (id={eid})')
else:
    print('Not found')
conn.close()

import psycopg2
conn = psycopg2.connect('postgresql://postgres.zyicslsosozivkilpylb:ali1993mubark@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=15')
cur = conn.cursor()

cur.execute("SELECT id, code, full_name FROM employees WHERE full_name IS NULL OR TRIM(full_name) = '' ORDER BY id")
rows = cur.fetchall()
print(f"Employees with empty names: {len(rows)}")
for r in rows:
    print(f"  id={r[0]} code={r[1]} name='{r[2]}'")

if rows:
    ids = [r[0] for r in rows]
    placeholders = ','.join(['%s'] * len(ids))
    
    tables_to_clean = [
        "attendance", "evaluations", "salaries", "financial_transactions",
        "leave_requests", "penalties", "overtime", "payrolls", "employee_loans",
        "meal_deductions", "labor_monthly_costs", "bank_info", "clean_users",
    ]
    for table in tables_to_clean:
        try:
            cur.execute(f"DELETE FROM {table} WHERE employee_id IN ({placeholders})", tuple(ids))
            print(f"  Cleaned {table}: {cur.rowcount} rows")
        except Exception as e:
            print(f"  Skip {table}: {e}")
    
    try:
        cur.execute(f"DELETE FROM cleaning_evaluations WHERE evaluated_employee_id IN ({placeholders}) OR evaluator_id IN ({placeholders})", tuple(ids) + tuple(ids))
        print(f"  Cleaned cleaning_evaluations: {cur.rowcount} rows")
    except Exception as e:
        print(f"  Skip cleaning_evaluations: {e}")
    try:
        cur.execute(f"DELETE FROM supervisor_evaluations WHERE supervisor_id IN ({placeholders}) OR evaluator_id IN ({placeholders})", tuple(ids) + tuple(ids))
        print(f"  Cleaned supervisor_evaluations: {cur.rowcount} rows")
    except Exception as e:
        print(f"  Skip supervisor_evaluations: {e}")
    try:
        cur.execute(f"UPDATE employees SET supervisor_id=NULL WHERE supervisor_id IN ({placeholders})", tuple(ids))
        print(f"  Cleared supervisor refs: {cur.rowcount} rows")
    except Exception as e:
        print(f"  Skip supervisor clear: {e}")

    cur.execute(f"DELETE FROM employees WHERE id IN ({placeholders})", tuple(ids))
    print(f"\nDeleted {cur.rowcount} employees with empty names")
    conn.commit()

cur.execute("SELECT COUNT(*) FROM employees")
print(f"\nRemaining employees: {cur.fetchone()[0]}")
conn.close()

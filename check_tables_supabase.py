import psycopg2

DATABASE_URL = 'postgresql://postgres.zyicslsosozivkilpylb:ali1993mubark@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=15'

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()

# Check which tables the app needs
app_tables = [
    'users', 'employees', 'attendances', 'evaluations', 'companies',
    'regions', 'locations', 'contracts', 'invoices', 'financial_transactions',
    'accounts', 'suppliers', 'journal_entries', 'journal_entry_details',
    'salaries', 'evaluation_criteria', 'financial_periods', 'leave_types',
    'leave_requests', 'leave_balances', 'bank_info', 'work_plans',
    'work_plan_tasks', 'supplier_invoices', 'supplier_invoice_payments',
    'system_settings'
]

print("=== TABLES STATUS ===")
for table in app_tables:
    cur.execute(f"""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = %s
        )
    """, (table,))
    exists = cur.fetchone()[0]
    
    if exists:
        cur.execute(f'SELECT COUNT(*) FROM "{table}"')
        count = cur.fetchone()[0]
        print(f"  {table}: EXISTS ({count} records)")
    else:
        print(f"  {table}: MISSING")

# Check attendance vs attendances
print("\n=== CHECK TABLE NAMES ===")
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE '%attend%'")
for r in cur.fetchall():
    print(f"  Found: {r[0]}")

conn.close()

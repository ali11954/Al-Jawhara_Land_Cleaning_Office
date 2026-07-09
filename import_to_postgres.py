import psycopg2
import json
from datetime import datetime

DATABASE_URL = 'postgresql://postgres.zyicslsosozivkilpylb:ali1993mubark@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=15'

# Load exported data
with open('D:/ghith/aljwahrh_land/export_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()

# Drop all existing tables
print("Dropping existing tables...")
cur.execute("""
DO $$ DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END $$;
""")

# Create tables in correct order
print("Creating tables...")

tables_sql = """
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password VARCHAR(200) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    employee_id INTEGER,
    allowed_pages TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    receivable_account_id INTEGER
);

CREATE TABLE regions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    company_id INTEGER REFERENCES companies(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    region_id INTEGER REFERENCES regions(id),
    address VARCHAR(200),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    position VARCHAR(20),
    salary FLOAT DEFAULT 60000,
    total_salary FLOAT DEFAULT 60000,
    daily_allowance FLOAT DEFAULT 500,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    is_resident BOOLEAN DEFAULT FALSE,
    basic_salary FLOAT DEFAULT 2000,
    clothing_allowance FLOAT DEFAULT 24480,
    health_card_allowance FLOAT DEFAULT 15000,
    monthly_insurance FLOAT DEFAULT 10800,
    contractor_tax FLOAT DEFAULT 500000,
    contractor_zakat FLOAT DEFAULT 75000,
    worker_type VARCHAR(20) DEFAULT 'permanent',
    region_id INTEGER REFERENCES regions(id),
    user_id INTEGER REFERENCES users(id),
    company_id INTEGER REFERENCES companies(id),
    supervisor_id INTEGER REFERENCES employees(id),
    qualification VARCHAR(100),
    specialization VARCHAR(100),
    hire_date DATE,
    allowances_updated_at TIMESTAMP
);

CREATE TABLE attendances (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id) NOT NULL,
    date DATE NOT NULL,
    attendance_type VARCHAR(20) DEFAULT 'individual',
    attendance_status VARCHAR(20) DEFAULT 'present',
    late_minutes INTEGER DEFAULT 0,
    sick_leave BOOLEAN DEFAULT FALSE,
    sick_leave_days INTEGER DEFAULT 0,
    annual_leave_days INTEGER DEFAULT 0,
    check_in_time TIME,
    check_out_time TIME,
    notes VARCHAR(500),
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(employee_id, date)
);

CREATE TABLE evaluation_criteria (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    job_title VARCHAR(100),
    max_score INTEGER DEFAULT 10,
    weight FLOAT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE evaluations (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id) NOT NULL,
    evaluator_id INTEGER REFERENCES users(id),
    evaluation_type VARCHAR(50) NOT NULL,
    score INTEGER NOT NULL,
    comments TEXT,
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    criteria_scores TEXT,
    region_id INTEGER REFERENCES regions(id),
    location_id INTEGER REFERENCES locations(id)
);

CREATE TABLE contracts (
    id SERIAL PRIMARY KEY,
    contract_number VARCHAR(50),
    company_id INTEGER REFERENCES companies(id),
    contract_type VARCHAR(20),
    contract_value FLOAT NOT NULL,
    monthly_value FLOAT,
    start_date DATE NOT NULL,
    end_date DATE,
    amount_received FLOAT DEFAULT 0,
    remaining_amount FLOAT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    contract_id INTEGER REFERENCES contracts(id),
    invoice_number VARCHAR(50),
    amount FLOAT NOT NULL,
    invoice_date DATE NOT NULL,
    due_date DATE,
    is_paid BOOLEAN DEFAULT FALSE,
    paid_date DATE,
    paid_amount FLOAT DEFAULT 0,
    payment_method VARCHAR(50),
    description TEXT,
    payment_reference VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    journal_entry_id INTEGER
);

CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    name_ar VARCHAR(100) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(120),
    address TEXT,
    tax_number VARCHAR(50),
    bank_name VARCHAR(100),
    bank_account VARCHAR(100),
    supplier_type VARCHAR(50) DEFAULT 'general',
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    payable_account_id INTEGER
);

CREATE TABLE financial_transactions (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    amount FLOAT NOT NULL,
    date DATE NOT NULL,
    description VARCHAR(200),
    is_settled BOOLEAN DEFAULT FALSE,
    settled_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    payment_method VARCHAR(20) DEFAULT 'cash',
    supplier_id INTEGER REFERENCES suppliers(id),
    monthly_installment FLOAT DEFAULT 0,
    settled_amount FLOAT DEFAULT 0,
    journal_entry_id INTEGER
);

CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    name_ar VARCHAR(100) NOT NULL,
    account_type VARCHAR(20) NOT NULL,
    nature VARCHAR(10) NOT NULL,
    parent_id INTEGER REFERENCES accounts(id),
    opening_balance FLOAT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE journal_entries (
    id SERIAL PRIMARY KEY,
    entry_number VARCHAR(50) UNIQUE NOT NULL,
    date DATE NOT NULL,
    description VARCHAR(500) NOT NULL,
    reference_type VARCHAR(50),
    reference_id INTEGER,
    created_by INTEGER REFERENCES users(id),
    is_posted BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE journal_entry_details (
    id SERIAL PRIMARY KEY,
    entry_id INTEGER REFERENCES journal_entries(id) ON DELETE CASCADE,
    account_id INTEGER REFERENCES accounts(id) NOT NULL,
    debit FLOAT DEFAULT 0,
    credit FLOAT DEFAULT 0,
    description VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE salaries (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id) NOT NULL,
    month_year VARCHAR(20) NOT NULL,
    base_salary FLOAT DEFAULT 0,
    attendance_days INTEGER DEFAULT 0,
    attendance_amount FLOAT DEFAULT 0,
    daily_allowance_amount FLOAT DEFAULT 0,
    overtime_amount FLOAT DEFAULT 0,
    advance_amount FLOAT DEFAULT 0,
    deduction_amount FLOAT DEFAULT 0,
    penalty_amount FLOAT DEFAULT 0,
    total_salary FLOAT DEFAULT 0,
    is_paid BOOLEAN DEFAULT FALSE,
    paid_date DATE,
    payment_method VARCHAR(50),
    payment_reference VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cafeteria_deduction FLOAT DEFAULT 0,
    restaurant_deduction FLOAT DEFAULT 0,
    meal_deduction_amount FLOAT DEFAULT 0,
    basic_salary_amount FLOAT DEFAULT 0,
    resident_allowance_amount FLOAT DEFAULT 0,
    clothing_allowance_amount FLOAT DEFAULT 0,
    health_card_amount FLOAT DEFAULT 0,
    insurance_amount FLOAT DEFAULT 0,
    contractor_profit FLOAT DEFAULT 0,
    cafeteria_supplier_id INTEGER REFERENCES suppliers(id),
    restaurant_supplier_id INTEGER REFERENCES suppliers(id),
    cafeteria_paid_to_supplier BOOLEAN DEFAULT FALSE,
    restaurant_paid_to_supplier BOOLEAN DEFAULT FALSE,
    is_calculated BOOLEAN DEFAULT FALSE,
    calculated_at TIMESTAMP,
    journal_entry_id INTEGER,
    UNIQUE(employee_id, month_year)
);

CREATE TABLE financial_periods (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    start_date DATE,
    end_date DATE,
    status VARCHAR(20) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE leave_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    days_per_year INTEGER DEFAULT 0,
    is_paid BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE leave_requests (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id) NOT NULL,
    leave_type_id INTEGER REFERENCES leave_types(id) NOT NULL,
    start_date DATE,
    end_date DATE,
    days INTEGER DEFAULT 1,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP,
    rejection_reason TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE leave_balances (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id) NOT NULL,
    leave_type_id INTEGER REFERENCES leave_types(id) NOT NULL,
    year INTEGER NOT NULL,
    total_days INTEGER DEFAULT 0,
    used_days INTEGER DEFAULT 0,
    remaining_days INTEGER DEFAULT 0,
    UNIQUE(employee_id, leave_type_id, year)
);

CREATE TABLE bank_info (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id) NOT NULL,
    bank_name VARCHAR(100),
    account_number VARCHAR(50),
    iban VARCHAR(50),
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE work_plans (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    company_id INTEGER REFERENCES companies(id),
    region_id INTEGER REFERENCES regions(id),
    location_id INTEGER REFERENCES locations(id),
    assigned_to INTEGER REFERENCES employees(id),
    status VARCHAR(20) DEFAULT 'pending',
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE work_plan_tasks (
    id SERIAL PRIMARY KEY,
    plan_id INTEGER REFERENCES work_plans(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    assigned_to INTEGER REFERENCES employees(id),
    status VARCHAR(20) DEFAULT 'pending',
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE supplier_invoices (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER REFERENCES suppliers(id) NOT NULL,
    amount FLOAT NOT NULL,
    description TEXT,
    invoice_date DATE,
    due_date DATE,
    status VARCHAR(20) DEFAULT 'pending',
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE supplier_invoice_payments (
    id SERIAL PRIMARY KEY,
    supplier_invoice_id INTEGER REFERENCES supplier_invoices(id),
    amount FLOAT DEFAULT 0,
    payment_method VARCHAR(50),
    payment_date DATE,
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE system_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

cur.execute(tables_sql)
print("Tables created successfully!")

# Insert data
print("\nInserting data...")

def insert_data(table_name, records):
    if not records:
        return 0
    
    # Filter out empty records
    records = [r for r in records if any(v is not None for v in r.values())]
    if not records:
        return 0
    
    columns = list(records[0].keys())
    placeholders = ', '.join(['%s'] * len(columns))
    cols = ', '.join([f'"{c}"' for c in columns])
    
    inserted = 0
    for record in records:
        values = []
        for col in columns:
            val = record.get(col)
            if isinstance(val, bool):
                val = val
            elif isinstance(val, (int, float)):
                val = val
            elif isinstance(val, str) and val == '':
                val = None
            values.append(val)
        
        try:
            cur.execute(f'INSERT INTO {table_name} ({cols}) VALUES ({placeholders})', values)
            inserted += 1
        except Exception as e:
            print(f"  Warning: {table_name} - {e}")
            conn.rollback()
            continue
    
    return inserted

# Insert in correct order
insert_order = [
    'users', 'companies', 'regions', 'locations', 'employees',
    'accounts', 'suppliers', 'attendances', 'evaluation_criteria',
    'evaluations', 'contracts', 'invoices', 'financial_transactions',
    'journal_entries', 'journal_entry_details', 'salaries',
    'financial_periods', 'leave_types', 'leave_requests', 'leave_balances',
    'bank_info', 'work_plans', 'work_plan_tasks',
    'supplier_invoices', 'supplier_invoice_payments', 'system_settings'
]

total_inserted = 0
for table in insert_order:
    if table in data and data[table]:
        count = insert_data(table, data[table])
        total_inserted += count
        print(f"  {table}: {count} records inserted")

print(f"\nTotal: {total_inserted} records inserted")

# Create admin password hash
from werkzeug.security import generate_password_hash
admin_password = generate_password_hash('admin123')
cur.execute("UPDATE users SET password = %s WHERE username = 'admin'", (admin_password,))
print("\nAdmin password updated")

conn.close()
print("\nDone!")

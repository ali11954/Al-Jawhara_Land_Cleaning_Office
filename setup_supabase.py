import psycopg2
from werkzeug.security import generate_password_hash

DATABASE_URL = 'postgresql://postgres.zyicslsosozivkilpylb:ali1993mubark@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=15'

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()

# Create missing tables
print("Creating missing tables...")

cur.execute("""
-- Users table
CREATE TABLE IF NOT EXISTS users (
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

-- Companies table
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    receivable_account_id INTEGER
);

-- Regions table
CREATE TABLE IF NOT EXISTS regions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    company_id INTEGER REFERENCES companies(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Locations table
CREATE TABLE IF NOT EXISTS locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    region_id INTEGER REFERENCES regions(id),
    address VARCHAR(200),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Evaluations table
CREATE TABLE IF NOT EXISTS evaluations (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    evaluator_id INTEGER,
    evaluation_type VARCHAR(50) NOT NULL,
    score INTEGER NOT NULL,
    comments TEXT,
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    criteria_scores TEXT,
    region_id INTEGER,
    location_id INTEGER
);

-- Evaluation criteria table
CREATE TABLE IF NOT EXISTS evaluation_criteria (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    job_title VARCHAR(100),
    max_score INTEGER DEFAULT 10,
    weight FLOAT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Financial periods table
CREATE TABLE IF NOT EXISTS financial_periods (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    start_date DATE,
    end_date DATE,
    status VARCHAR(20) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Leave types table
CREATE TABLE IF NOT EXISTS leave_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    days_per_year INTEGER DEFAULT 0,
    is_paid BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Leave requests table
CREATE TABLE IF NOT EXISTS leave_requests (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    leave_type_id INTEGER,
    start_date DATE,
    end_date DATE,
    days INTEGER DEFAULT 1,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    approved_by INTEGER,
    approved_at TIMESTAMP,
    rejection_reason TEXT,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Leave balances table
CREATE TABLE IF NOT EXISTS leave_balances (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    leave_type_id INTEGER,
    year INTEGER NOT NULL,
    total_days INTEGER DEFAULT 0,
    used_days INTEGER DEFAULT 0,
    remaining_days INTEGER DEFAULT 0,
    UNIQUE(employee_id, leave_type_id, year)
);

-- Bank info table
CREATE TABLE IF NOT EXISTS bank_info (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    bank_name VARCHAR(100),
    account_number VARCHAR(50),
    iban VARCHAR(50),
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Work plans table
CREATE TABLE IF NOT EXISTS work_plans (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    company_id INTEGER REFERENCES companies(id),
    region_id INTEGER REFERENCES regions(id),
    location_id INTEGER REFERENCES locations(id),
    assigned_to INTEGER,
    status VARCHAR(20) DEFAULT 'pending',
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Work plan tasks table
CREATE TABLE IF NOT EXISTS work_plan_tasks (
    id SERIAL PRIMARY KEY,
    plan_id INTEGER REFERENCES work_plans(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    assigned_to INTEGER,
    status VARCHAR(20) DEFAULT 'pending',
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System settings table
CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Supplier invoice payments table (if not exists)
CREATE TABLE IF NOT EXISTS supplier_invoice_payments (
    id SERIAL PRIMARY KEY,
    supplier_invoice_id INTEGER,
    amount FLOAT DEFAULT 0,
    payment_method VARCHAR(50),
    payment_date DATE,
    notes TEXT,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

print("Tables created successfully!")

# Insert seed data
print("\nInserting seed data...")

# Insert users (admin)
admin_password = generate_password_hash('admin123')
cur.execute("""
    INSERT INTO users (username, password, full_name, role, is_active) 
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (username) DO NOTHING
""", ('admin', admin_password, 'مدير النظام', 'admin', True))

cur.execute("""
    INSERT INTO users (username, password, full_name, role, is_active) 
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (username) DO NOTHING
""", ('accountant', generate_password_hash('accountant123'), ' المحاسب', 'accountant', True))

cur.execute("""
    INSERT INTO users (username, password, full_name, role, is_active) 
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (username) DO NOTHING
""", ('supervisor', generate_password_hash('supervisor123'), 'المشرف', 'supervisor', True))

print("  Users inserted")

# Insert companies
cur.execute("SELECT COUNT(*) FROM companies")
if cur.fetchone()[0] == 0:
    cur.execute("INSERT INTO companies (name) VALUES (%s)", ('شركة النظافة العامة',))
    cur.execute("INSERT INTO companies (name) VALUES (%s)", ('شركة الرشاد',))
    cur.execute("INSERT INTO companies (name) VALUES (%s), (%s), (%s)",
                ('الشركة اليمنية لتكرير السكر', 'شركة رأس عيسى الصناعية', 'الشركة اليمنية للمطاحن وصوامع الغلال'))
    print("  Companies inserted")

# Insert regions
cur.execute("SELECT COUNT(*) FROM regions")
if cur.fetchone()[0] == 0:
    cur.execute("SELECT id FROM companies LIMIT 1")
    company_id = cur.fetchone()[0]
    for name in ['صنعاء', 'الحديدة', 'تعز', 'عدن', 'إب', 'ذمار']:
        cur.execute("INSERT INTO regions (name, company_id) VALUES (%s, %s)", (name, company_id))
    print("  Regions inserted")

# Insert locations
cur.execute("SELECT COUNT(*) FROM locations")
if cur.fetchone()[0] == 0:
    cur.execute("SELECT id FROM regions LIMIT 1")
    region_id = cur.fetchone()[0]
    for name in ['المطار', 'الميناء', 'المدينة القديمة', 'المنطقة الصناعية']:
        cur.execute("INSERT INTO locations (name, region_id) VALUES (%s, %s)", (name, region_id))
    print("  Locations inserted")

# Insert leave types
cur.execute("SELECT COUNT(*) FROM leave_types")
if cur.fetchone()[0] == 0:
    for name, days in [('إجازة سنوية', 21), ('إجازة مرضية', 15), ('إجازة طارئة', 5), ('إجازة بدون أجر', 0)]:
        cur.execute("INSERT INTO leave_types (name, days_per_year, is_paid) VALUES (%s, %s, %s)",
                    (name, days, days > 0))
    print("  Leave types inserted")

# Insert financial period
cur.execute("SELECT COUNT(*) FROM financial_periods")
if cur.fetchone()[0] == 0:
    cur.execute("INSERT INTO financial_periods (name, start_date, end_date, status) VALUES (%s, %s, %s, %s)",
                ('2026', '2026-01-01', '2026-12-31', 'open'))
    print("  Financial period inserted")

# Insert system settings
cur.execute("SELECT COUNT(*) FROM system_settings")
if cur.fetchone()[0] == 0:
    cur.execute("INSERT INTO system_settings (key, value) VALUES (%s, %s)", ('company_name', 'أرض الجوهرة'))
    cur.execute("INSERT INTO system_settings (key, value) VALUES (%s, %s)", ('company_name_en', 'Al-Jawhara Land'))
    print("  System settings inserted")

print("\nDone!")
conn.close()

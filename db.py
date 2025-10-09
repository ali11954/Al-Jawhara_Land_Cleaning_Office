import psycopg2

# بيانات الاتصال بقاعدة البيانات
conn_params = {
    "host": "dpg-d3ft80u3jp1c73f87ib0-a.frankfurt-postgres.render.com",
    "database": "evaluation_db_3th0",
    "user": "evaluation_db_3th0_user",
    "password": "RylVGtHAlaIWTv63DcOjIMPPn1lJ54kT",
    "port": 5432
}

try:
    # إنشاء الاتصال
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()

    # تنفيذ استعلام بسيط
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
    tables = cursor.fetchall()

    print("📄 الجداول الموجودة في قاعدة البيانات:")
    for table in tables:
        print(" -", table[0])

    cursor.close()
    conn.close()

except Exception as e:
    print("❌ حدث خطأ أثناء الاتصال بقاعدة البيانات:", e)

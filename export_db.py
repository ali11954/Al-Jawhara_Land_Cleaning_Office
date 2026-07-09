import sqlite3
import json
from datetime import datetime

DB_PATH = 'D:/ghith/aljwahrh_land/instance/aljwahrh_land.db'

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Get all tables
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cursor.fetchall()]

print("=== TABLES ===")
for t in tables:
    cursor.execute(f"SELECT COUNT(*) FROM [{t}]")
    count = cursor.fetchone()[0]
    print(f"{t}: {count} rows")

print("\n=== DATA EXPORT ===")
export_data = {}
for table in tables:
    cursor.execute(f"SELECT * FROM [{table}]")
    rows = [dict(r) for r in cursor.fetchall()]
    # Convert datetime objects to strings
    for row in rows:
        for key, value in row.items():
            if isinstance(value, datetime):
                row[key] = value.isoformat()
    export_data[table] = rows

# Save to JSON
with open('D:/ghith/aljwahrh_land/export_data.json', 'w', encoding='utf-8') as f:
    json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)

print(f"\nExported {len(tables)} tables to export_data.json")

# Print summary
print("\n=== SUMMARY ===")
for table, rows in export_data.items():
    print(f"{table}: {len(rows)} records")

conn.close()

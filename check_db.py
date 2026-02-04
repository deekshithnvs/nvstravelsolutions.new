
import sqlite3
import os

db_path = "backend-services/nvs_portal.db"
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Invoices Table ---")
print("\n--- Error Log Table ---")
cursor.execute("SELECT id, timestamp, error_message FROM error_log ORDER BY timestamp DESC LIMIT 5")
for row in cursor.fetchall():
    print(row)

conn.close()

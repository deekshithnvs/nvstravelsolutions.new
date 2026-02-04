import sqlite3
import os

db_path = "backend-services/nvs_portal.db"
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Users Table ---")
cursor.execute("SELECT id, email, role FROM users")
users = cursor.fetchall()
for user in users:
    print(user)

print("\n--- Vendors Table ---")
cursor.execute("SELECT id, company_name, email, status FROM vendors")
vendors = cursor.fetchall()
for vendor in vendors:
    print(vendor)

conn.close()

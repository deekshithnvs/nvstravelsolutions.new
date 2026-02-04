import sqlite3
import os

db_path = r'd:\Asmitha\OneDrive\Nithin\Learning\Antigravity\Vendor management portal\backend-services\nvs_portal.db'

def dump_schema():
    if not os.path.exists(db_path):
        print(f"DB not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    with open('full_actual_schema.txt', 'w') as f:
        for table_name, schema_sql in tables:
            f.write(f"--- Table: {table_name} ---\n")
            f.write(f"{schema_sql}\n\n")
    conn.close()
    print("Schema dumped to full_actual_schema.txt")

if __name__ == "__main__":
    dump_schema()

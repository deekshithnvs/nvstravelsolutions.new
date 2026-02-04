import sqlite3
import sys
import os

def add_column(cursor, table, column_def):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")
        print(f"Added column: {column_def}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"Column already exists: {column_def.split()[0]}")
        else:
            print(f"Error adding {column_def}: {e}")

def fix_schema():
    print("Fixing database schema...")
    db_path = 'backend-services/nvs_portal.db'
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Missing columns based on model evaluation
    columns_to_add = [
        "taxable_value FLOAT DEFAULT 0",
        "non_taxable_value FLOAT DEFAULT 0",
        "discount FLOAT DEFAULT 0",
        "cgst FLOAT DEFAULT 0",
        "sgst FLOAT DEFAULT 0",
        "igst FLOAT DEFAULT 0",
    ]
    
    for col in columns_to_add:
        add_column(cursor, "invoices", col)
        
    conn.commit()
    conn.close()
    print("Schema update complete.")

if __name__ == "__main__":
    fix_schema()

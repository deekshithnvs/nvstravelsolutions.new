import sqlite3
import os

db_path = r'd:\Asmitha\OneDrive\Nithin\Learning\Antigravity\Vendor management portal\backend-services\nvs_portal.db'

def check_columns():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(invoices);")
    columns = [col[1] for col in cursor.fetchall()]
    
    target_columns = ['taxable_value', 'non_taxable_value', 'discount', 'cgst', 'sgst', 'igst']
    
    print("Columns in 'invoices' table:")
    print(columns)
    
    missing = [c for c in target_columns if c not in columns]
    if missing:
        print(f"\nCRITICAL: Missing columns: {missing}")
    else:
        print("\nAll financial columns present.")
        
    conn.close()

if __name__ == "__main__":
    check_columns()

import sqlite3
import os

DB_PATH = "backend-services/nvs_portal.db"

def check_data():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT invoice_no, amount, tax_amount, cgst, sgst, igst FROM invoices LIMIT 10")
    rows = cursor.fetchall()
    
    print(f"{'Invoice #':<20} {'Amount':<10} {'Tax':<10} {'CGST':<10} {'SGST':<10} {'IGST':<10}")
    print("-" * 70)
    for row in rows:
        print(f"{row[0]:<20} {row[1]:<10} {row[2]:<10} {row[3]:<10} {row[4]:<10} {row[5]:<10}")
    
    conn.close()

if __name__ == "__main__":
    check_data()

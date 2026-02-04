import sqlite3
import os

DB_PATH = "backend-services/nvs_portal.db"

def inspect_invoice(invoice_no):
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print(f"--- Inspecting Invoice: {invoice_no} ---")
    cursor.execute("SELECT * FROM invoices WHERE invoice_no = ?", (invoice_no,))
    row = cursor.fetchone()
    
    if not row:
        print("Invoice not found.")
        return
    
    for key in row.keys():
        if key in ['amount', 'tax_amount', 'cgst', 'sgst', 'igst', 'taxable_value']:
            print(f"{key}: {row[key]}")
    
    conn.close()

if __name__ == "__main__":
    inspect_invoice("Y44W25SCr05042")

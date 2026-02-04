import sqlite3
import os

DB_PATH = "backend-services/nvs_portal.db"
INVOICE_NO = "HR4W25SCr02548"

def check_line_items():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get invoice ID
    cursor.execute("SELECT id FROM invoices WHERE invoice_no = ?", (INVOICE_NO,))
    inv = cursor.fetchone()
    if not inv:
        print(f"Invoice {INVOICE_NO} not found.")
        return
    
    inv_id = inv[0]
    print(f"Invoice ID: {inv_id}")

    # Get line items from line_items_json
    cursor.execute("SELECT line_items_json FROM invoices WHERE id = ?", (inv_id,))
    row = cursor.fetchone()
    
    if not row or not row[0]:
        print(f"No line items found in line_items_json for invoice ID {inv_id}")
    else:
        print(f"Line items for invoice ID {inv_id}:")
        print(row[0])

    conn.close()

if __name__ == "__main__":
    check_line_items()

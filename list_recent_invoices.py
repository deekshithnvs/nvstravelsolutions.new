import sqlite3
import os

DB_PATH = "backend-services/nvs_portal.db"

def list_invoices():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Recent Invoices:")
    cursor.execute("SELECT id, invoice_no, amount FROM invoices ORDER BY created_at DESC LIMIT 10")
    for row in cursor.fetchall():
        print(row)

    conn.close()

if __name__ == "__main__":
    list_invoices()

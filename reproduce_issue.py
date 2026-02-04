import sqlite3
import os
from decimal import Decimal

DB_PATH = "backend-services/nvs_portal.db"

def reproduce():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    invoice_no = "Y44W25SCr05042"
    print(f"--- Reproducing for Invoice: {invoice_no} ---")
    cursor.execute("SELECT * FROM invoices WHERE invoice_no = ?", (invoice_no,))
    inv = cursor.fetchone()
    
    if not inv:
        print("Invoice not found.")
        return
    
    # Simulate get_invoice_detail logic
    tax_amount = inv['tax_amount']
    # In Python, Decimal('0.00') is falsy, but float(0.0) is also falsy.
    # Let's see what type it actually is when fetched via sqlite3.Row
    print(f"Original tax_amount: {tax_amount} (Type: {type(tax_amount)})")
    
    if not tax_amount or float(tax_amount) == 0:
        tax_amount = float(inv['cgst'] or 0) + float(inv['sgst'] or 0) + float(inv['igst'] or 0)
    
    base_val = float(inv['amount'] or 0)
    tax_val = float(tax_amount or 0)
    total_val = base_val + tax_val
    
    print(f"Calculated base_val: {base_val}")
    print(f"Calculated tax_val: {tax_val}")
    print(f"Calculated total_val (base + tax): {total_val}")
    
    # Simulate list_my_invoices logic
    list_tax = float(inv['tax_amount']) if inv['tax_amount'] else (float(inv['cgst'] or 0) + float(inv['sgst'] or 0) + float(inv['igst'] or 0))
    print(f"List API Tax: {list_tax}")

    conn.close()

if __name__ == "__main__":
    reproduce()

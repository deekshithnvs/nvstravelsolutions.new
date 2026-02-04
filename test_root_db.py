import sqlite3
import os

def test_root_db():
    db_path = 'nvs_portal.db'
    if not os.path.exists(db_path):
        print(f"File {db_path} not found in root.")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        # Try to insert a row with all expected columns
        query = """
        INSERT INTO invoices (
            invoice_no, vendor_id, amount, tax_amount, status, category, invoice_date, 
            file_hash, internal_remarks, paid_amount
        ) VALUES ('TEST-SYNC', 1, 100.0, 10.0, 'pending', 'General', '2026-02-04', 
                 'hash', 'remarks', 0.0)
        """
        cursor.execute(query)
        conn.commit()
        print("Insert successful (Surprising!)")
    except sqlite3.OperationalError as e:
        print(f"CAUGHT EXPECTED ERROR: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_root_db()

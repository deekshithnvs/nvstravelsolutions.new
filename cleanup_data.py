import sqlite3
import os

def cleanup_vendor_status():
    db_path = 'backend-services/nvs_portal.db'
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Fetch all vendors
        cursor.execute("SELECT id, status FROM vendors")
        vendors = cursor.fetchall()
        
        updated_count = 0
        for vendor_id, status in vendors:
            if status:
                # Remove whitespace, newlines, etc.
                cleaned_status = status.strip().lower()
                if cleaned_status != status:
                    cursor.execute("UPDATE vendors SET status = ? WHERE id = ?", (cleaned_status, vendor_id))
                    updated_count += 1
                    print(f"Updated vendor ID {vendor_id}: '{status!r}' -> '{cleaned_status}'")

        conn.commit()
        print(f"Successfully updated {updated_count} vendors.")
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    cleanup_vendor_status()

import sys
import os

# Add backend-services to python path
sys.path.append(os.path.join(os.getcwd(), "backend-services"))

from sqlalchemy.orm import Session
from models.database import SessionLocal, init_db
from models.invoice import Invoice
from models.vendor import Vendor
from models.user import User

def test_query():
    db = SessionLocal()
    try:
        print("Testing Invoice Query...")
        vendor_id = 1
        query = db.query(Invoice)
        query = query.filter(Invoice.vendor_id == vendor_id)
        print(f"Query: {query}")
        invoices = query.all()
        print(f"Found {len(invoices)} invoices.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_query()

from sqlalchemy import create_engine, func, case
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add backend-services to path to import models
sys.path.append(os.path.join(os.getcwd(), "backend-services"))

from models.invoice import Invoice, InvoiceStatus
from models.database import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    print("Testing Admin Stats Query Final...")
    # This matches the logic in admin.py
    admin_totals = db.query(
        func.sum(Invoice.amount).label("pending_amount"),
        func.sum(
            func.coalesce(Invoice.tax_amount, 0) + 
            case(
                (func.coalesce(Invoice.tax_amount, 0) == 0, 
                 func.coalesce(Invoice.cgst, 0) + func.coalesce(Invoice.sgst, 0) + func.coalesce(Invoice.igst, 0)),
                else_=0
            )
        ).label("pending_tax"),
        func.sum(func.coalesce(Invoice.igst, 0)).label("pending_igst")
    ).filter(Invoice.status != InvoiceStatus.PAID).first()

    print(f"Pending Amount: {admin_totals.pending_amount}")
    print(f"Pending Tax: {admin_totals.pending_tax}")
    print(f"Pending IGST: {admin_totals.pending_igst}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

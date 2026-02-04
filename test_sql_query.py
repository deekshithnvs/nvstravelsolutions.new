from sqlalchemy import create_engine, func, case, Numeric
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
    print("Testing Invoices Totals Query with SQLAlchemy 2.0 Case Syntax...")
    
    # Components calculation
    components = func.coalesce(Invoice.cgst, 0) + func.coalesce(Invoice.sgst, 0) + func.coalesce(Invoice.igst, 0)
    cond = (func.coalesce(Invoice.tax_amount, 0) == 0)

    # In 2.0, case() takes *whens, else_=...
    # So we pass the tuple directly if using *whens
    totals_query = db.query(
        func.sum(Invoice.amount).label("total_amount"),
        func.sum(
            func.coalesce(Invoice.tax_amount, 0) + 
            case(
                (cond, components), 
                else_=0
            )
        ).label("total_tax")
    )
    
    totals = totals_query.first()
    print(f"Total Amount: {totals.total_amount}")
    print(f"Total Tax: {totals.total_tax}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

import sys
import os

# Add parent directory to path to import models
sys.path.append(os.path.join(os.getcwd(), "backend-services"))

from models.database import SessionLocal, engine, Base
from models.user import User, UserRole
from models.vendor import Vendor, VendorStatus
from models.invoice import Invoice, InvoiceStatus
from models.audit import AuditLog
from services.auth import auth_service
from datetime import datetime
import uuid

def seed_data(count=100):
    db = SessionLocal()
    try:
        print(f"🌱 Seeding {count} test vendors...")
        
        for i in range(1, count + 1):
            email = f"test_vendor_{i}@example.com"
            company = f"Test Vendor {i} Ltd"
            
            # 1. Create Vendor
            vendor = db.query(Vendor).filter(Vendor.email == email).first()
            if not vendor:
                vendor = Vendor(
                    company_name=company,
                    contact_person=f"Contact {i}",
                    email=email,
                    mobile=f"9876543{i:03d}",
                    pan=f"ABCDE{i:04d}F",
                    gstin=f"27ABCDE{i:04d}F1Z5",
                    status="verified",
                    kyc_verified=True,
                    tds_applicable=True,
                    tds_rate=2.0,
                    tds_nature_of_payment="194C"
                )
                db.add(vendor)
                db.flush() # Get vendor ID
            
            # 2. Create User
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(
                    email=email,
                    name=company,
                    password_hash=auth_service._hash_password("vendor123"),
                    role=UserRole.VENDOR,
                    is_active=True
                )
                db.add(user)
            
            # 3. Create a few invoices for each
            for j in range(1, 3):
                inv_no = f"INV-{i:03d}-{j:02d}"
                if not db.query(Invoice).filter(Invoice.invoice_no == inv_no).first():
                    invoice = Invoice(
                        invoice_no=inv_no,
                        vendor_id=vendor.id,
                        amount=1000.0 * j,
                        tax_amount=180.0 * j,
                        status=InvoiceStatus.PENDING,
                        invoice_date=datetime.now(),
                        category="Software",
                        description=f"Auto-generated invoice {j} for {company}"
                    )
                    db.add(invoice)
            
            if i % 10 == 0:
                print(f"   Processed {i}/{count}...")
        
        db.commit()
        print("✅ Seeding completed successfully.")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data(100)

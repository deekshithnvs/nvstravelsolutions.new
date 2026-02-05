"""
Script to add test vendors to the database
Run this to populate the vendor dropdown with sample data
"""

from models.database import SessionLocal
from models.vendor import Vendor, VendorStatus
from datetime import datetime

def add_test_vendors():
    db = SessionLocal()
    
    try:
        # Check if test vendors already exist
        existing_count = db.query(Vendor).count()
        print(f"ℹ Database currently has {existing_count} vendor(s)")
        
        # Sample vendors
        test_vendors = [
            {
                "company_name": "ABC Transport Services",
                "email": "contact@abctransport.com",
                "mobile": "9876543210",
                "pan": "ABCPT1234D",
                "gstin": "29ABCPT1234D1Z5",
                "entity_type": "Private Limited",
                "status": VendorStatus.ACTIVE,
                "kyc_verified": True,
                "bank_account_no": "1234567890",
                "bank_name": "HDFC Bank",
                "ifsc_code": "HDFC0001234",
                "tds_applicable": True,
                "tds_rate": 2.0
            },
            {
                "company_name": "XYZ Logistics Pvt Ltd",
                "email": "info@xyzlogistics.com",
                "mobile": "9876543211",
                "pan": "XYZPL5678E",
                "gstin": "29XYZPL5678E1Z6",
                "entity_type": "Private Limited",
                "status": VendorStatus.ACTIVE,
                "kyc_verified": True,
                "bank_account_no": "0987654321",
                "bank_name": "ICICI Bank",
                "ifsc_code": "ICIC0005678",
                "tds_applicable": True,
                "tds_rate": 2.0
            },
            {
                "company_name": "Quick Delivery Services",
                "email": "support@quickdelivery.com",
                "mobile": "9876543212",
                "pan": "QDSPL9012F",
                "gstin": "29QDSPL9012F1Z7",
                "entity_type": "Partnership",
                "status": VendorStatus.ACTIVE,
                "kyc_verified": True,
                "bank_account_no": "5555666677",
                "bank_name": "SBI",
                "ifsc_code": "SBIN0009012",
                "tds_applicable": True,
                "tds_rate": 1.0
            },
            {
                "company_name": "Express Cargo Solutions",
                "email": "admin@expresscargo.com",
                "mobile": "9876543213",
                "pan": "ECSPL3456G",
                "gstin": "29ECSPL3456G1Z8",
                "entity_type": "Private Limited",
                "status": VendorStatus.ACTIVE,
                "kyc_verified": False,
                "bank_account_no": "7777888899",
                "bank_name": "Axis Bank",
                "ifsc_code": "UTIB0003456",
                "tds_applicable": True,
                "tds_rate": 2.0
            },
            {
                "company_name": "Metro Transport Co.",
                "email": "contact@metrotransport.com",
                "mobile": "9876543214",
                "pan": "MTCPL7890H",
                "gstin": "29MTCPL7890H1Z9",
                "entity_type": "LLP",
                "status": VendorStatus.PENDING,
                "kyc_verified": False,
                "bank_account_no": "1111222233",
                "bank_name": "Kotak Mahindra Bank",
                "ifsc_code": "KKBK0007890",
                "tds_applicable": True,
                "tds_rate": 1.0
            }
        ]
        
        # Add vendors to database
        for vendor_data in test_vendors:
            vendor = Vendor(**vendor_data)
            db.add(vendor)
        
        db.commit()
        print(f"\n✅ Successfully added {len(test_vendors)} test vendors!")
        print("\nVendors added:")
        for v in test_vendors:
            print(f"  - {v['company_name']} ({v['status']})")
        
        print("\n🎉 You can now select vendors from the dropdown in the invoice form!")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error adding vendors: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Adding Test Vendors to Database")
    print("=" * 60)
    add_test_vendors()
    print("=" * 60)

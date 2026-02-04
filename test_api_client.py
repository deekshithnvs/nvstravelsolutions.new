from fastapi.testclient import TestClient
import sys
import os

# Add backend-services to path
sys.path.append(os.path.abspath("backend-services"))
os.chdir("backend-services") # Change CWD for DB check

from main import app
from models.database import SessionLocal
from models.invoice import Invoice

client = TestClient(app)

def test_invoice_detail():
    # Login as admin
    login_data = {"email": "admin@nvs.com", "password": "admin123"}
    response = client.post("/api/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return
        
    token = response.json()["token"]
    headers = {"Authorization": token}
    
    # Find invoice Y44W25SCr05042
    db = SessionLocal()
    inv = db.query(Invoice).filter(Invoice.invoice_no == "Y44W25SCr05042").first()
    db.close()
    
    if not inv:
        print("Invoice not found in DB")
        return
        
    print(f"Testing ID: {inv.id}")
    
    # Get Detail
    response = client.get(f"/api/invoices/detail?invoice_id={inv.id}", headers=headers)
    if response.status_code != 200:
        print(f"Detail API failed: {response.text}")
        return
        
    detail = response.json()
    print("--- Detail API Response ---")
    keys = ['amount', 'base_amount', 'tax_amount', 'cgst', 'sgst', 'igst', 'taxable_value']
    for k in keys:
        print(f"{k}: {detail.get(k)}")

if __name__ == "__main__":
    test_invoice_detail()

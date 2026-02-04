import os
import sys

from fastapi.testclient import TestClient

# Add backend-services to path
sys.path.append(os.path.abspath("backend-services"))
os.chdir("backend-services") # Change CWD for DB check

from main import app
from services.auth import AuthService

client = TestClient(app)

def test_list_apis():
    # Login
    auth_service = AuthService()
    # Use the known user from previous tests
    user = auth_service.authenticate("admin@nvs.com", "admin123")
    assert user is not None, "Login failed"
    token = user["token"]
    headers = {"Authorization": token}

    print("\n--- Testing Vendor Invoice List ---")
    response = client.get("/api/invoices/data", headers=headers)
    assert response.status_code == 200
    data = response.json()
    items = data.get("items", [])
    if items:
        first = items[0]
        print(f"Invoice: {first.get('invoice_no')}")
        print(f"Amount: {first.get('amount')}")
        print(f"Base Amount: {first.get('base_amount')}")
        print(f"Tax: {first.get('tax')}")
        print(f"ID: {first.get('id')}")
        
        # Verify base_amount and id presence
        assert "base_amount" in first, "base_amount missing from vendor list"
        assert "id" in first, "id missing from vendor list"
    else:
        print("No invoices found for vendor")

    print("\n--- Testing Admin Pending Invoices ---")
    # Need admin login
    admin_user = auth_service.authenticate("admin@nvs.com", "admin123")
    if admin_user:
        admin_token = admin_user["token"]
        admin_headers = {"Authorization": admin_token}
        
        response = client.get("/api/admin/pending-invoices", headers=admin_headers)
        assert response.status_code == 200
        admin_data = response.json()
        if admin_data:
            first_admin = admin_data[0]
            print(f"Invoice: {first_admin.get('invoice_no')}")
            print(f"Amount: {first_admin.get('amount')}")
            print(f"Base Amount: {first_admin.get('base_amount')}")
            print(f"Tax Amount: {first_admin.get('tax_amount')}")
            print(f"ID: {first_admin.get('id')}")
            
            # Verify base_amount presence
            assert "base_amount" in first_admin, "base_amount missing from admin list"
            assert "id" in first_admin, "id missing from admin list"
        else:
            print("No pending invoices found for admin")
    else:
        print("Admin login failed (might not exist in seed)")

if __name__ == "__main__":
    test_list_apis()

"""
Quick test script to verify vendor addition API endpoint
Run this after starting the server to test if vendor creation works
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8001"
ADMIN_EMAIL = "admin@nvstravels.com"
ADMIN_PASSWORD = "NVSadmin2026!"

def test_vendor_addition():
    print("=" * 60)
    print("Testing Vendor Addition API")
    print("=" * 60)
    
    # Step 1: Login to get auth token
    print("\n[1/3] Logging in as admin...")
    login_response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={
            "username": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return False
    
    auth_token = login_response.json().get("access_token")
    print(f"✅ Login successful! Token: {auth_token[:20]}...")
    
    # Step 2: Prepare vendor data
    print("\n[2/3] Preparing test vendor data...")
    vendor_data = {
        "company_name": "Test Vendor Company",
        "entity_type": "Company",
        "contact_person": "John Doe",
        "email": "testvendor@example.com",
        "mobile": "9876543210",
        "pan": "ABCDE1234F",
        "gstin": "29ABCDE1234F1Z5",
        "bank_account_no": "1234567890",
        "bank_name": "HDFC Bank",
        "ifsc_code": "HDFC0001234",
        "tds_applicable": 1,  # Testing int to bool conversion
        "tds_rate": 2.0,
        "tds_nature_of_payment": "194C - Contractors",
        "remarks": "Test vendor created via API"
    }
    
    print(f"Vendor data prepared: {vendor_data['company_name']}")
    
    # Step 3: Create vendor
    print("\n[3/3] Creating vendor...")
    headers = {
        "Authorization": auth_token,
        "Content-Type": "application/json"
    }
    
    create_response = requests.post(
        f"{BASE_URL}/api/admin/vendors",
        headers=headers,
        json=vendor_data
    )
    
    print(f"\nResponse Status: {create_response.status_code}")
    print(f"Response Body: {json.dumps(create_response.json(), indent=2)}")
    
    if create_response.status_code == 200:
        print("\n" + "=" * 60)
        print("✅ SUCCESS! Vendor created successfully!")
        print("=" * 60)
        print("\nDefault credentials for vendor:")
        print(f"  Email: {vendor_data['email']}")
        print(f"  Password: nvs@123")
        return True
    else:
        print("\n" + "=" * 60)
        print("❌ FAILED! Vendor creation failed!")
        print("=" * 60)
        return False

if __name__ == "__main__":
    try:
        test_vendor_addition()
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

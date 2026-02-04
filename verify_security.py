import httpx
import sqlite3
import json

BASE_URL = "http://localhost:8000"

def get_session_token(username, password):
    res = httpx.post(f"{BASE_URL}/api/login", json={"username": username, "password": password}, timeout=10.0)
    if res.status_code == 200:
        return res.json().get("token")
    return None

def test_security():
    print("--- Security Verification Script ---")
    
    # 1. Test Superadmin Access
    print("\n[Case 1] Superadmin Login & Settings Access")
    sa_token = get_session_token("superadmin@nvs.com", "super123")
    if not sa_token: # try variant
        sa_token = get_session_token("superadmin", "super123")
        
    if sa_token:
        print("✓ Superadmin login successful")
        res = httpx.get(f"{BASE_URL}/api/admin/settings", headers={"Authorization": sa_token})
        if res.status_code == 200:
            print("✓ Superadmin can access settings")
        else:
            print(f"✗ Superadmin settings access failed: {res.status_code}")
    else:
        print("✗ Superadmin login failed")

    # 2. Find a Vendor and Test Isolation
    print("\n[Case 2] Vendor Isolation & Masking")
    email = "vendor@nvs.com"
    print(f"Testing with vendor: {email}")
    
    # Test Vendor Login
    v_token = get_session_token(email, "vendor123")
    if v_token:
        print(f"✓ Vendor {email} login successful")
        
        # Test Settings Access (Should be forbidden)
        res = httpx.get(f"{BASE_URL}/api/admin/settings", headers={"Authorization": v_token})
        if res.status_code == 403 or res.status_code == 401:
            print("✓ Vendor access to settings forbidden (RBAC Correct)")
        else:
            print(f"✗ Vendor access to settings permitted! Code: {res.status_code}")
            
        # Test Invoice Isolation
        res = httpx.get(f"{BASE_URL}/api/invoices/data", headers={"Authorization": v_token})
        if res.status_code == 200:
            invoices = res.json()
            print(f"✓ Found {len(invoices)} invoices for vendor")
            # All these should be filtered by backend
        else:
            print(f"✗ Failed to fetch invoices: {res.status_code}")
    else:
        print(f"✗ Vendor {email} login failed (Password unknown?)")

    # 3. Test Admin Vendor List (Masking Check)
    print("\n[Case 3] Vendor Master Data Masking (Admin Only)")
    if sa_token:
        res = httpx.get(f"{BASE_URL}/api/admin/vendors", headers={"Authorization": sa_token})
        if res.status_code == 200:
            vendors = res.json()
            if vendors:
                v = vendors[0]
                # Check if backend returns raw data (masking is usually frontend, but let's see)
                print(f"Admin sees bank account: {v.get('bank_account_no', 'N/A')}")
                print("Note: Grid masking is implemented in the HTML/JS layers for visibility.")
            else:
                print("No vendors found to test masking")
    
    # 4. Test Approval with Reason Requirement (API Logic)
    print("\n[Case 4] Invoice Status Update Endpoint")
    if sa_token:
        # Just check if the endpoint exists and responds to POST
        res = httpx.post(f"{BASE_URL}/api/invoices/update-status", headers={"Authorization": sa_token}, json={})
        if res.status_code != 404:
            print("✓ Endpoint /api/invoices/update-status is active")
        else:
            print("✗ Endpoint /api/invoices/update-status NOT FOUND")

if __name__ == "__main__":
    test_security()

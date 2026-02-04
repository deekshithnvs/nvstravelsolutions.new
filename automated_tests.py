import requests
import json
import os

BASE_URL = "http://localhost:8000"

def test_auth(email, password):
    print(f"Testing Auth for {email}...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            token = response.json().get("token")
            print(f"[OK] Auth successful. Token: {token[:10]}...")
            return token
        else:
            print(f"[FAIL] Auth failed for {email}: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"[ERROR] Connection error: {e}")
        return None

def test_admin_stats(token):
    print("Testing Admin Stats...")
    headers = {"Authorization": f"{token}"}
    response = requests.get(f"{BASE_URL}/api/admin/stats", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Stats fetched: {data}")
        return data
    else:
        print(f"[FAIL] Stats fetch failed: {response.status_code}")
        return None

def test_list_invoices(token, is_admin=False):
    print(f"Testing Listing Invoices (Admin: {is_admin})...")
    headers = {"Authorization": f"{token}"}
    endpoint = "/api/admin/pending-invoices" if is_admin else "/api/invoices/data"
    response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
    if response.status_code == 200:
        invoices = response.json()
        print(f"[OK] Invoices listed: {len(invoices)} found.")
        if invoices:
            print(f"Sample Invoice: {invoices[0].get('invoice_no') or invoices[0].get('invoice_number')}")
        return invoices
    else:
        print(f"[FAIL] Invoice listing failed: {response.status_code} - {response.text}")
        return None

def test_invoice_detail(token, invoice_id):
    print(f"Testing Invoice Detail for ID {invoice_id}...")
    headers = {"Authorization": f"{token}"}
    response = requests.get(f"{BASE_URL}/api/invoices/detail?invoice_id={invoice_id}", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Detail fetched for {data.get('invoice_no')}")
        print(f"Financials: Taxable={data.get('taxable_value')}, CGST={data.get('cgst')}")
        return data
    else:
        print(f"[FAIL] Detail fetch failed: {response.status_code} - {response.text}")
        return None

def test_upload_invoice(token, file_path):
    print(f"Testing Invoice Upload with {file_path}...")
    headers = {"Authorization": f"{token}"}
    files = {'file': open(file_path, 'rb')}
    data = {
        "manual_invoice_no": f"AUTO-TEST-{datetime.now().strftime('%H%M%S')}",
        "manual_amount": 5000.0,
        "manual_tax": 900.0,
        "manual_taxable_value": 4100.0,
        "manual_cgst": 450.0,
        "manual_sgst": 450.0,
        "manual_date": datetime.now().strftime("%d-%m-%Y"),
        "manual_category": "Test"
    }
    response = requests.post(f"{BASE_URL}/api/invoices/upload", headers=headers, files=files, data=data)
    if response.status_code == 200:
        res_json = response.json()
        if res_json.get("success"):
            print(f"[OK] Invoice uploaded successfully!")
            return res_json
        else:
            print(f"[FAIL] Upload failed: {res_json.get('message')}")
    else:
        print(f"[FAIL] Upload crashed: {response.status_code} - {response.text}")
    return None

def test_update_status(token, invoice_no, status, reason=""):
    print(f"Testing Status Update for {invoice_no} to {status}...")
    headers = {"Authorization": f"{token}"}
    payload = {"invoice_no": invoice_no, "status": status, "reason": reason}
    response = requests.post(f"{BASE_URL}/api/invoices/update-status", headers=headers, json=payload)
    if response.status_code == 200:
        res_json = response.json()
        if res_json.get("success"):
            print(f"[OK] Status updated successfully!")
            return res_json
        else:
            print(f"[FAIL] Update failed: {res_json.get('message')}")
    else:
        print(f"[FAIL] Update crashed: {response.status_code} - {response.text}")
    return None

def test_reports(token):
    print("Testing Invoices CSV Report...")
    headers = {"Authorization": f"{token}"}
    response = requests.get(f"{BASE_URL}/api/reports/invoices-csv", headers=headers)
    if response.status_code == 200:
        if "text/csv" in response.headers.get("Content-Type", ""):
            print(f"[OK] Report fetched. Length: {len(response.content)} bytes.")
            return response.content
        else:
            print(f"[FAIL] Report content missing or invalid type.")
    else:
        print(f"[FAIL] Report fetch failed: {response.status_code} - {response.text}")
    return None

def test_list_vendors(token):
    print("Testing Vendor Listing...")
    headers = {"Authorization": f"{token}"}
    response = requests.get(f"{BASE_URL}/api/admin/vendors", headers=headers)
    if response.status_code == 200:
        vendors = response.json()
        print(f"[OK] Vendors listed: {len(vendors)} found.")
        return vendors
    else:
        print(f"[FAIL] Vendor listing failed: {response.status_code}")
    return None

def test_vendor_detail(token, vendor_id):
    print(f"Testing Vendor Detail for ID {vendor_id}...")
    headers = {"Authorization": f"{token}"}
    response = requests.get(f"{BASE_URL}/api/admin/vendors/{vendor_id}", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Vendor detail fetched for {data.get('company_name')}")
        return data
    else:
        print(f"[FAIL] Vendor detail failed: {response.status_code}")
    return None

def test_monitoring(token):
    print("Testing Monitoring Logs...")
    headers = {"Authorization": f"{token}"}
    response = requests.get(f"{BASE_URL}/api/monitoring/errors", headers=headers)
    if response.status_code == 200:
        logs = response.json()
        print(f"[OK] Monitoring logs fetched: {len(logs)} found.")
        return logs
    else:
        print(f"[FAIL] Monitoring failed: {response.status_code}")
    return None

def test_excel_download(token, invoice_no):
    print(f"Testing Excel Download for {invoice_no}...")
    headers = {"Authorization": f"{token}"}
    response = requests.get(f"{BASE_URL}/api/reports/invoice/{invoice_no}/excel", headers=headers)
    if response.status_code == 200:
        print(f"[OK] Excel report fetched.")
    else:
        print(f"[INFO] Excel report fetch returned {response.status_code} (Expected if not implemented)")

from datetime import datetime
def run_all_tests():
    # 1. Admin Auth
    admin_token = test_auth("admin@nvs.com", "admin123")
    if admin_token:
        test_admin_stats(admin_token)
        admin_invoices = test_list_invoices(admin_token, is_admin=True)
        if admin_invoices:
            inv_id = admin_invoices[0].get("id")
            inv_no = admin_invoices[0].get("invoice_no") or admin_invoices[0].get("invoice_number")
            test_invoice_detail(admin_token, inv_id)
            # Test Approve
            test_update_status(admin_token, inv_no, "approved", "Looks good")
            # Test Excel (likely 404)
            test_excel_download(admin_token, inv_no)
        
        # Test Report
        test_reports(admin_token)
        
        # Test Vendors
        vendors = test_list_vendors(admin_token)
        if vendors:
            test_vendor_detail(admin_token, vendors[0].get("id"))
            
        # Test Monitoring
        test_monitoring(admin_token)
    
    print("\n" + "="*20 + "\n")
    
    # 2. Vendor Auth
    vendor_token = test_auth("vendor@nvs.com", "vendor123")
    if vendor_token:
        test_list_invoices(vendor_token, is_admin=False)
        img_path = r"C:\Users\NVS\.gemini\antigravity\brain\32344653-6a49-4952-90bd-f3d26503a971\test_invoice_image_1770105437058.png"
        test_upload_invoice(vendor_token, img_path)

if __name__ == "__main__":
    run_all_tests()

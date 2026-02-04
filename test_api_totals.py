import requests
import json

BASE_URL = "http://localhost:8000"

def test_invoice_api():
    # Login to get token
    login_data = {"email": "vendor@nvs.com", "password": "vendor123"}
    r = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if r.status_code != 200:
        print("Login failed")
        return
    
    token = r.json().get("token")
    headers = {"Authorization": token}
    
    # Fetch invoices
    r = requests.get(f"{BASE_URL}/api/invoices/data", headers=headers)
    if r.status_code != 200:
        print(f"API failed: {r.status_code}")
        print(r.text)
        return
    
    data = r.json()
    print(f"Total Amount: {data.get('total_amount')}")
    print(f"Total Tax: {data.get('total_tax')}")
    print(f"Item Count: {len(data.get('items', []))}")
    
    if data.get('items'):
        print("\nSample Item:")
        item = data['items'][0]
        print(f"Invoice #: {item['invoice_no']}")
        print(f"Amount: {item['amount']}")
        print(f"Tax: {item['tax']}")

if __name__ == "__main__":
    test_invoice_api()

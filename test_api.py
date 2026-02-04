import requests

# We need to login first to get a token
def check_api():
    login_url = "http://localhost:8001/api/auth/login"
    login_data = {"email": "admin@nvs.com", "password": "admin123"}
    
    try:
        r = requests.post(login_url, json=login_data)
        if r.status_code != 200:
            print(f"Login failed: {r.text}")
            return
        
        token = r.json().get("token")
        headers = {"Authorization": token}
        
        # Now get the invoice detail
        # We need the ID of invoice Y44W25SCr05042
        # I'll first find it via the data API
        data_url = "http://localhost:8001/api/invoices/data?search=Y44W25SCr05042"
        r = requests.get(data_url, headers=headers)
        items = r.json().get("items", [])
        if not items:
            print("Invoice not found in data API")
            return
            
        inv_id = items[0]["id"]
        print(f"Found ID: {inv_id}")
        
        # Now get details
        detail_url = f"http://localhost:8001/api/invoices/detail?invoice_id={inv_id}"
        r = requests.get(detail_url, headers=headers)
        detail = r.json()
        
        print("--- Detail API Response ---")
        for key in ['amount', 'tax_amount', 'cgst', 'sgst', 'igst', 'taxable_value']:
            print(f"{key}: {detail.get(key)}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_api()

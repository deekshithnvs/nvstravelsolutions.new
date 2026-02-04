import requests

BASE_URL = "http://localhost:8001"

def test_password_length_validation():
    print("Testing password length validation...")
    payload = {
        "email": "test@too-long-password.com",
        "password": "p" * 73,
        "company_name": "Test Company",
        "contact_person": "Test Person"
    }
    try:
        r = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        if r.status_code == 400 and "Password cannot be longer than 72 characters" in r.text:
            print("[OK] Backend correctly rejected long password.")
        else:
            print(f"[FAIL] Unexpected response for long password: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")

def test_vendor_api_contact_person():
    print("\nTesting vendor API for contact_person field...")
    # Admin Login
    login_data = {"email": "admin@nvs.com", "password": "admin123"}
    try:
        r = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if r.status_code != 200:
            print("[FAIL] Admin login failed.")
            return
        
        token = r.json().get("token")
        headers = {"Authorization": token}
        
        r = requests.get(f"{BASE_URL}/api/admin/vendors", headers=headers)
        if r.status_code == 200:
            vendors = r.json()
            if vendors and "contact_person" in vendors[0]:
                print(f"[OK] Found contact_person in API response: {vendors[0]['contact_person']}")
            else:
                print("[FAIL] contact_person field missing from API response.")
                if vendors: print(f"Keys found: {vendors[0].keys()}")
        else:
            print(f"[FAIL] Failed to fetch vendors: {r.status_code}")
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")

if __name__ == "__main__":
    test_password_length_validation()
    test_vendor_api_contact_person()

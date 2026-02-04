import requests
import string
import random

BASE_URL = "http://127.0.0.1:8000"

def test_password_length():
    email = f"test_{random.randint(1000, 9999)}@example.com"
    # 72 character password
    password = "".join(random.choices(string.ascii_letters + string.digits, k=72))
    
    data = {
        "email": email,
        "password": password,
        "company_name": "Test Company",
        "contact_person": "Test User",
        "mobile": "1234567890"
    }
    
    print(f"Testing registration with {len(password)} char password...")
    response = requests.post(f"{BASE_URL}/api/auth/register", json=data)
    
    if response.status_code == 200:
        print("Registration successful!")
        # Try login
        login_data = {"email": email, "password": password}
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if login_res.status_code == 200:
            print("Login successful with long password!")
        else:
            print(f"Login failed: {login_res.text}")
    else:
        print(f"Registration failed: {response.text}")

def test_password_overflow():
    email = f"test_{random.randint(1000, 9999)}@example.com"
    # 73 character password (should fail)
    password = "".join(random.choices(string.ascii_letters + string.digits, k=73))
    
    data = {
        "email": email,
        "password": password,
        "company_name": "Test Company",
        "contact_person": "Test User",
        "mobile": "1234567890"
    }
    
    print(f"Testing registration with {len(password)} char password (expecting failure)...")
    response = requests.post(f"{BASE_URL}/api/auth/register", json=data)
    
    if response.status_code == 400 and "longer than 72" in response.text:
        print("Registration failed as expected with correct error message.")
    else:
        print(f"Unexpected result: {response.status_code} - {response.text}")

if __name__ == "__main__":
    try:
        test_password_length()
        test_password_overflow()
    except Exception as e:
        print(f"Error connecting to server: {e}")

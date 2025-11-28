import requests
import time

BASE_URL = "http://127.0.0.1:8000"
USERNAME = "admin"
PASSWORD = "admin123" # This is the password for the hash in auth.py

def test_api():
    print("Testing API...")

    # 1. Get Login Page
    resp = requests.get(f"{BASE_URL}/login")
    assert resp.status_code == 200, "Failed to get login page"
    print("✓ Login page accessible")

    # 2. Login
    resp = requests.post(f"{BASE_URL}/token", data={"username": USERNAME, "password": PASSWORD})
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
    token = resp.json()["access_token"]
    print("✓ Login successful, token received")
    
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Get Status
    resp = requests.get(f"{BASE_URL}/agent/status", headers=headers)
    assert resp.status_code == 200, f"Failed to get status: {resp.text}"
    print(f"✓ Status: {resp.json()['status']}")

    # 4. Start Agent
    resp = requests.post(f"{BASE_URL}/agent/start", headers=headers)
    if resp.status_code == 200:
        print("✓ Agent started")
    elif resp.status_code == 400 and "already running" in resp.text:
        print("✓ Agent already running")
    else:
        print(f"Failed to start agent: {resp.text}")

    # 5. Check Status again
    time.sleep(1)
    resp = requests.get(f"{BASE_URL}/agent/status", headers=headers)
    print(f"✓ Status after start: {resp.json()['status']}")

    # 6. Stop Agent
    resp = requests.post(f"{BASE_URL}/agent/stop", headers=headers)
    if resp.status_code == 200:
        print("✓ Agent stopped")
    else:
        print(f"Failed to stop agent: {resp.text}")

    # 7. Rate Limit Test (Optional)
    print("Testing rate limit (sending 10 requests)...")
    for i in range(10):
        resp = requests.get(f"{BASE_URL}/agent/status", headers=headers)
        if resp.status_code == 429:
            print("✓ Rate limit hit as expected")
            break
    else:
        print("Warning: Rate limit not hit (maybe limit is higher or per-endpoint)")

if __name__ == "__main__":
    test_api()

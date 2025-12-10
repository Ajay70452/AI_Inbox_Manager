"""Test the actual API endpoints"""
import requests

API_BASE = "http://localhost:8000/api/v1"
EMAIL = "test@example.com"
PASSWORD = "password123"  # UPDATE THIS
THREAD_ID = "19b06d362600c33a"

print("1. Logging in...")
response = requests.post(f"{API_BASE}/auth/login", json={"email": EMAIL, "password": PASSWORD})
print(f"   Status: {response.status_code}")

if response.status_code != 200:
    print(f"   Error: {response.text}")
    print("\n[ERROR] Login failed. Please update PASSWORD in this script.")
    exit(1)

token = response.json()['access_token']
print(f"   Token: {token[:30]}...")

headers = {"Authorization": f"Bearer {token}"}

print(f"\n2. Fetching summary for thread {THREAD_ID}...")
response = requests.get(f"{API_BASE}/threads/{THREAD_ID}/summary", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   Summary: {data.get('summary_text', '')[:100]}...")
else:
    print(f"   Response: {response.text}")

print("\nDone!")

"""
Test script to debug on-demand processing

Run this to simulate what the Chrome extension does when clicking an email
"""

import requests
import json

API_BASE = "http://localhost:8000/api/v1"

# CONFIGURATION - UPDATE THESE
EMAIL = "your_email@example.com"  # Your test account email
PASSWORD = "your_password"  # Your test account password
THREAD_ID = "19b06d362600c33a"  # The thread ID from the error log

def test_on_demand_processing():
    print("=" * 60)
    print("Testing On-Demand Email Processing")
    print("=" * 60)

    # Step 1: Login
    print("\n1. Logging in...")
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={"email": EMAIL, "password": PASSWORD}
        )
        response.raise_for_status()
        data = response.json()
        token = data['access_token']
        print(f"✅ Login successful! Token: {token[:20]}...")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # Step 2: Check if thread exists
    print(f"\n2. Checking if thread {THREAD_ID} exists...")
    try:
        response = requests.get(
            f"{API_BASE}/threads/{THREAD_ID}/summary",
            headers=headers
        )
        if response.status_code == 200:
            print("✅ Thread exists and has summary!")
            print(json.dumps(response.json(), indent=2))
            return
        elif response.status_code == 404:
            print("⚠️  Thread or summary not found (404)")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Failed to fetch summary: {e}")

    # Step 3: Trigger AI processing
    print(f"\n3. Triggering AI processing for thread {THREAD_ID}...")
    try:
        response = requests.post(
            f"{API_BASE}/workers/ai/process/trigger",
            headers=headers,
            json={"thread_id": THREAD_ID}
        )

        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")

        if response.status_code == 200:
            print("✅ AI processing triggered successfully!")
            data = response.json()
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ AI processing failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(f"Raw error: {response.text}")
    except Exception as e:
        print(f"❌ Failed to trigger AI processing: {e}")
        import traceback
        traceback.print_exc()

    # Step 4: Wait and check if summary is now available
    print(f"\n4. Checking if summary is now available...")
    import time
    time.sleep(2)

    try:
        response = requests.get(
            f"{API_BASE}/threads/{THREAD_ID}/summary",
            headers=headers
        )
        if response.status_code == 200:
            print("✅ Summary now available!")
            print(json.dumps(response.json(), indent=2))
        elif response.status_code == 404:
            print("⚠️  Summary still not available (processing may take longer)")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Failed to fetch summary: {e}")

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    print("\n⚠️  IMPORTANT: Update EMAIL, PASSWORD, and THREAD_ID at the top of this file!\n")
    test_on_demand_processing()

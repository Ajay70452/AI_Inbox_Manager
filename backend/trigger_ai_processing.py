"""
Script to trigger AI processing for all threads
Run this to process all synced emails with AI
"""

import sys
import requests

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "test@example.com"  # Change this to your email
PASSWORD = "password123"     # Change this to your password

def main():
    print("🤖 AI Processing Trigger Script")
    print("=" * 50)
    
    # Step 1: Login
    print("\n1️⃣ Logging in...")
    login_response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"email": EMAIL, "password": PASSWORD}
    )
    
    if not login_response.ok:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    print("✅ Login successful!")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Get all threads from database
    print("\n2️⃣ Getting threads from database...")
    from db.session import SessionLocal
    from models.thread import Thread
    
    db = SessionLocal()
    try:
        threads = db.query(Thread).limit(10).all()  # Process first 10 threads
        print(f"📧 Found {len(threads)} threads to process")
        
        if not threads:
            print("⚠️  No threads found. Make sure you've synced your emails first!")
            return
        
        # Step 3: Trigger AI processing for each thread
        print("\n3️⃣ Triggering AI processing...")
        processed = 0
        failed = 0
        
        for thread in threads:
            print(f"\n   Processing thread: {thread.subject[:50]}...")
            
            try:
                response = requests.post(
                    f"{API_BASE_URL}/workers/ai/process/trigger",
                    headers=headers,
                    json={"thread_id": str(thread.id), "tasks": ["summary", "priority", "sentiment", "reply", "tasks"]}
                )
                
                if response.ok:
                    print(f"   ✅ Processed successfully")
                    processed += 1
                else:
                    print(f"   ❌ Failed: {response.text}")
                    failed += 1
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                failed += 1
        
        print("\n" + "=" * 50)
        print(f"📊 Summary:")
        print(f"   ✅ Processed: {processed}")
        print(f"   ❌ Failed: {failed}")
        print("\n🎉 Done! Now open Gmail and check the sidebar for AI insights!")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()

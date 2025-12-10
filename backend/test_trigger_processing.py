"""
Direct test of AI processing trigger (bypasses API auth)
"""
import sys
from db import SessionLocal
from models import User
from workers.ai_processing_worker import process_thread_ai

# Configuration
THREAD_ID = "19b06d362600c33a"  # The thread ID from your error
USER_EMAIL = "test@example.com"

def main():
    db = SessionLocal()

    # Get user
    user = db.query(User).filter(User.email == USER_EMAIL).first()
    if not user:
        print(f"[ERROR] User not found: {USER_EMAIL}")
        return

    print(f"[OK] Found user: {user.email} (ID: {user.id})")
    print(f"\n[AI] Triggering AI processing for thread: {THREAD_ID}")
    print("=" * 60)

    try:
        result = process_thread_ai(
            user_id=str(user.id),
            thread_id=THREAD_ID,
            tasks=['summarize', 'reply']
        )

        print("\n[OK] Processing completed!")
        print(f"Status: {result['status']}")
        print(f"Job ID: {result['job_id']}")

        if result['status'] == 'success':
            print(f"\n[RESULTS]:")
            if 'result' in result:
                for key, value in result['result'].items():
                    print(f"  - {key}: {value}")
        else:
            print(f"\n[ERROR]: {result.get('error')}")

    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

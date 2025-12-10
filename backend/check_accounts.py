"""Check database for users and account tokens"""
from db import SessionLocal
from models import AccountToken, User

db = SessionLocal()

users = db.query(User).all()
print(f"Users: {len(users)}")
for u in users:
    print(f"  - {u.email} (ID: {u.id})")

tokens = db.query(AccountToken).all()
print(f"\nAccount Tokens: {len(tokens)}")
for t in tokens:
    print(f"  - {t.provider} for user_id={t.user_id} (expires: {t.expires_at})")

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from base64 import urlsafe_b64encode
from app.config import settings


def get_encryption_key() -> bytes:
    """
    Derive encryption key from SECRET_KEY

    Returns:
        32-byte encryption key
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'ai_inbox_salt',  # In production, use a secure random salt
        iterations=100000
    )
    key = kdf.derive(settings.SECRET_KEY.encode())
    return urlsafe_b64encode(key)


def encrypt_token(token: str) -> str:
    """
    Encrypt OAuth refresh token

    Args:
        token: Plain token string

    Returns:
        Encrypted token string
    """
    key = get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(token.encode())
    return encrypted.decode()


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt OAuth refresh token

    Args:
        encrypted_token: Encrypted token string

    Returns:
        Decrypted token string
    """
    key = get_encryption_key()
    f = Fernet(key)
    decrypted = f.decrypt(encrypted_token.encode())
    return decrypted.decode()

"""
Encryption module for Civ4 PBEM Manager.

Encrypts sensitive configuration data (transport credentials, SMTP passwords)
using AES-256 via Fernet (cryptography library).
Key is derived from a user-provided master password using PBKDF2-HMAC-SHA256.

Flow:
1. User sets master password on first run (or when enabling encryption)
2. Sensitive data is encrypted before saving to disk
3. On startup, user must enter master password to unlock
4. Without correct password, transport/smtp fields stay hidden/inaccessible
"""
import base64
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

# Salt is stored alongside encrypted data (not secret, just ensures unique keys)
SALT_SIZE = 16
# PBKDF2 iterations — high enough for security, fast enough for UX
PBKDF2_ITERATIONS = 600_000


def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive a Fernet-compatible key from password + salt using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    key = kdf.derive(password.encode("utf-8"))
    return base64.urlsafe_b64encode(key)


def encrypt_data(data: dict, password: str) -> dict:
    """Encrypt a dict of sensitive data.

    Returns a dict with:
        - "salt": base64-encoded salt
        - "data": base64-encoded encrypted JSON blob
    """
    salt = os.urandom(SALT_SIZE)
    key = _derive_key(password, salt)
    fernet = Fernet(key)

    plaintext = json.dumps(data, ensure_ascii=False).encode("utf-8")
    ciphertext = fernet.encrypt(plaintext)

    return {
        "salt": base64.b64encode(salt).decode("ascii"),
        "data": ciphertext.decode("ascii"),
    }


def decrypt_data(encrypted: dict, password: str) -> Optional[dict]:
    """Decrypt an encrypted data blob.

    Args:
        encrypted: dict with "salt" and "data" keys
        password: master password

    Returns:
        Decrypted dict, or None if password is wrong / data corrupted.
    """
    try:
        salt = base64.b64decode(encrypted["salt"])
        ciphertext = encrypted["data"].encode("ascii")

        key = _derive_key(password, salt)
        fernet = Fernet(key)

        plaintext = fernet.decrypt(ciphertext)
        return json.loads(plaintext.decode("utf-8"))
    except (InvalidToken, KeyError, ValueError, json.JSONDecodeError) as e:
        logger.warning(f"Decryption failed: {type(e).__name__}")
        return None


def verify_password(encrypted: dict, password: str) -> bool:
    """Check if a password can decrypt the data (without returning data)."""
    return decrypt_data(encrypted, password) is not None


def hash_password_check(password: str) -> str:
    """Create a quick-check hash for password validation hint.

    This is NOT used for encryption — only to give a fast "wrong password"
    response before attempting expensive PBKDF2 decryption.
    Stored as sha256(password + fixed_prefix) — not security-critical.
    """
    check = hashlib.sha256(f"civ4pbem_check_{password}".encode()).hexdigest()[:16]
    return check

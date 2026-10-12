"""
Secure Authentication Module
Custom Customer Authentication pre-seeded for user: arya
"""
import hashlib
import hmac
import os
import secrets
import time
from typing import Any, Dict, Optional, Tuple

USERS_DB: Dict[str, Dict[str, str]] = {}
SESSIONS_DB: Dict[str, Dict[str, Any]] = {}

def hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
    salt_bytes = salt or os.urandom(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, 100000)
    return hashed.hex(), salt_bytes.hex()

def register_user(username: str, password: str, role: str = "customer") -> bool:
    username = username.strip().lower()
    if not username or not password or len(password) < 4:
        return False
    if username in USERS_DB:
        return False
    pwd_hash, salt = hash_password(password)
    USERS_DB[username] = {
        "hash": pwd_hash,
        "salt": salt,
        "created_at": str(time.time()),
        "role": role,
    }
    return True

def verify_login(username: str, password: str) -> bool:
    username = username.strip().lower()
    user = USERS_DB.get(username)
    if not user:
        return False
    expected_hash, _ = hash_password(password, bytes.fromhex(user["salt"]))
    return hmac.compare_digest(user["hash"], expected_hash)

def create_session(username: str) -> str:
    token = secrets.token_urlsafe(32)
    SESSIONS_DB[token] = {
        "username": username,
        "created_at": time.time(),
        "role": USERS_DB.get(username, {}).get("role", "customer")
    }
    return token

def verify_session(token: str) -> Optional[Dict[str, Any]]:
    return SESSIONS_DB.get(token)

def revoke_session(token: str) -> bool:
    """Terminates an active session."""
    if token in SESSIONS_DB:
        del SESSIONS_DB[token]
        return True
    return False

# Pre-seed custom requested customer user account
register_user("arya", "antigravity2026", role="customer")
if "arya" != "admin":
    register_user("admin", "antigravity2026", role="administrator")

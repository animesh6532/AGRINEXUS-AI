"""
Security utility module for AgriNexus-AI.
Provides PBKDF2-HMAC-SHA256 password hashing and RFC 7519 compliant JWT access tokens.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from .config import settings

SECRET_KEY = os.getenv("JWT_SECRET", "agrinexus_secret_key_2026_production_secure_key_99")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30


def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with random 16-byte salt."""
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return f"{salt.hex()}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against stored salt and key."""
    try:
        if not hashed_password or '$' not in hashed_password:
            return False
        salt_hex, key_hex = hashed_password.split('$', 1)
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        key = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, 100000)
        return hmac.compare_digest(key, expected_key)
    except Exception:
        return False


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')


def _b64url_decode(data: str) -> bytes:
    padding = '=' * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode(data + padding)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generate signed JWT access token containing subject identity and claims."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS))
    to_encode.update({
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    })
    header = {"alg": ALGORITHM, "typ": "JWT"}

    header_json = json.dumps(header, separators=(',', ':')).encode('utf-8')
    payload_json = json.dumps(to_encode, separators=(',', ':')).encode('utf-8')

    b64_header = _b64url_encode(header_json)
    b64_payload = _b64url_encode(payload_json)

    signature_input = f"{b64_header}.{b64_payload}".encode('utf-8')
    signature = hmac.new(SECRET_KEY.encode('utf-8'), signature_input, hashlib.sha256).digest()
    b64_signature = _b64url_encode(signature)

    return f"{b64_header}.{b64_payload}.{b64_signature}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify HMAC signature and expiration of JWT token."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        b64_header, b64_payload, b64_signature = parts

        signature_input = f"{b64_header}.{b64_payload}".encode('utf-8')
        expected_signature = hmac.new(SECRET_KEY.encode('utf-8'), signature_input, hashlib.sha256).digest()
        actual_signature = _b64url_decode(b64_signature)

        if not hmac.compare_digest(expected_signature, actual_signature):
            return None

        payload_bytes = _b64url_decode(b64_payload)
        payload = json.loads(payload_bytes.decode('utf-8'))

        exp = payload.get("exp")
        if exp and int(datetime.now(timezone.utc).timestamp()) > exp:
            return None

        return payload
    except Exception:
        return None

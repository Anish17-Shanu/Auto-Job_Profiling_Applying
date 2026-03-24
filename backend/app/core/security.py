from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import os

from jose import jwt

from app.core.config import settings

ALGORITHM = "HS256"


def hash_password(password: str, salt: bytes | None = None) -> str:
    effective_salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), effective_salt, 120000)
    return f"{base64.b64encode(effective_salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, hashed_password: str) -> bool:
    salt_b64, digest_b64 = hashed_password.split("$", maxsplit=1)
    salt = base64.b64decode(salt_b64.encode())
    expected = hash_password(password, salt).split("$", maxsplit=1)[1]
    return hmac.compare_digest(expected, digest_b64)


def create_access_token(subject: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


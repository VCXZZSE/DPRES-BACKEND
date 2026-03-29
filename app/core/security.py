from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _create_token(subject: str, expires_delta: timedelta, token_type: str) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        'sub': subject,
        'type': token_type,
        'iat': int(now.timestamp()),
        'exp': int((now + expires_delta).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(subject: str) -> str:
    return _create_token(
        subject=subject,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type='access',
    )


def create_refresh_token(subject: str) -> str:
    return _create_token(
        subject=subject,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        token_type='refresh',
    )


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise ValueError('Invalid token') from exc


def generate_random_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def generate_numeric_token(digits: int = 8) -> str:
    if digits < 6:
        raise ValueError('Token length must be at least 6 digits')
    # Cryptographically secure numeric OTP-like token.
    upper_bound = 10 ** digits
    return f"{secrets.randbelow(upper_bound):0{digits}d}"


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def extract_email_domain(email: str) -> str:
    return email.split('@', 1)[1].strip().lower()

"""JWT access-token and refresh-token creation / verification."""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from .schemas import TokenData

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration (overridable via environment variables)
# ---------------------------------------------------------------------------

_DEFAULT_SECRET = "change-me-in-production"
SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", _DEFAULT_SECRET)
ALGORITHM: str = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
    os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)
REFRESH_TOKEN_EXPIRE_DAYS: int = int(
    os.environ.get("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")
)

if SECRET_KEY == _DEFAULT_SECRET:
    logger.warning(
        "JWT_SECRET_KEY is using the insecure default value. "
        "Set the JWT_SECRET_KEY environment variable before deploying to production."
    )


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Token creation
# ---------------------------------------------------------------------------


def create_access_token(
    user_id: str,
    username: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Return a signed JWT access token."""
    expire = _utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(
    user_id: str,
    username: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Return a signed JWT refresh token."""
    expire = _utcnow() + (
        expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "type": "refresh",
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# Token verification
# ---------------------------------------------------------------------------


def decode_token(token: str) -> TokenData:
    """
    Decode and validate a JWT token.

    Raises ``JWTError`` on failure (expired, invalid signature, etc.).
    """
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return TokenData(
        sub=payload["sub"],
        username=payload["username"],
        role=payload["role"],
        exp=payload.get("exp"),
    )


def verify_access_token(token: str) -> Optional[TokenData]:
    """Return ``TokenData`` for a valid access token, or ``None``."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        return TokenData(
            sub=payload["sub"],
            username=payload["username"],
            role=payload["role"],
            exp=payload.get("exp"),
        )
    except JWTError:
        return None


def verify_refresh_token(token: str) -> Optional[TokenData]:
    """Return ``TokenData`` for a valid refresh token, or ``None``."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return TokenData(
            sub=payload["sub"],
            username=payload["username"],
            role=payload["role"],
            exp=payload.get("exp"),
        )
    except JWTError:
        return None
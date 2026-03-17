"""API key validation for Alexa webhook requests."""

import logging
import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

_ALEXA_API_KEY: str = os.environ.get("ALEXA_API_KEY", "")

if not _ALEXA_API_KEY:
    logger.warning(
        "ALEXA_API_KEY is not set — webhook endpoint will reject all requests "
        "with HTTP 401 until the variable is configured."
    )

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(_api_key_header)) -> str:
    """
    FastAPI dependency that validates the ``X-API-Key`` header.

    Raises ``HTTP 503`` if the webhook is not configured server-side.
    Raises ``HTTP 401`` if the key is missing or invalid.
    """
    if not _ALEXA_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Alexa webhook API key is not configured on this server.",
        )
    if not api_key or api_key != _ALEXA_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key
"""
API key authentication for /api/v1/* routes.
Validates X-API-Key header; raises HTTPException 401 if missing or invalid.
"""

from fastapi import Header, HTTPException, status

from app.config import API_KEY


def require_api_key(x_api_key: str | None = Header(None, alias="X-API-Key")) -> str:
    """
    Dependency: require valid X-API-Key header.
    Returns the key if valid; otherwise raises 401 with JSON body.
    """
    if not API_KEY:
        # Server misconfiguration: no key set
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "API key not configured", "code": "auth_not_configured"},
        )
    if not x_api_key or x_api_key.strip() != API_KEY.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Missing or invalid API key", "code": "invalid_api_key"},
        )
    return x_api_key

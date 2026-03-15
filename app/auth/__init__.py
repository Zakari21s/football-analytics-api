"""
API key authentication for /api/v1/* routes.
Validates X-API-Key header; raises HTTPException 401 if missing or invalid.
Uses APIKeyHeader for OpenAPI security scheme (Swagger Authorize).
"""

from fastapi import HTTPException, Security, status, Request
from fastapi.security import APIKeyHeader

from app.config import settings

# OpenAPI: documents X-API-Key and enables Swagger "Authorize"
API_KEY_HEADER = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
    description="API key for authentication. Required for all /api/v1 endpoints.",
)


def require_api_key(request: Request, api_key: str | None = Security(API_KEY_HEADER)) -> str:
    """
    Dependency: require valid X-API-Key header.
    Returns the key if valid; otherwise raises 401 with consistent JSON body.
    """
    if request.method == "OPTIONS":
        return ""
    if not settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "API key not configured", "code": "auth_not_configured"},
        )
    if not api_key or api_key.strip() != (settings.api_key or "").strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Missing or invalid API key", "code": "invalid_api_key"},
        )
    return api_key

"""
FastAPI dependencies for admin auth.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.auth import decode_token

http_bearer = HTTPBearer(auto_error=False)


def get_admin_token(
    creds: HTTPAuthorizationCredentials | None = Depends(http_bearer),
) -> str | None:
    """Extract Bearer token from Authorization header."""
    if creds and creds.scheme.lower() == "bearer":
        return creds.credentials
    return None


async def get_current_admin(token: str | None = Depends(get_admin_token)) -> str:
    """Verify JWT and return admin username. Raises 401 if invalid."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Yetkilendirme gerekli",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya süresi dolmuş oturum",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload["sub"]

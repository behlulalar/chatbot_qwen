"""
Admin auth API - login, me.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.config import settings
from app.core.auth import create_access_token
from app.core.deps import get_current_admin

router = APIRouter(prefix="/admin/auth", tags=["admin-auth"])


# --- Schemas ---
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class MeResponse(BaseModel):
    username: str


# --- Endpoints ---
@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest):
    """Admin login - returns JWT."""
    if data.username != settings.admin_username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya şifre hatalı",
        )
    # Admin password is stored in env (plain for simplicity) - production: use bcrypt hash
    if data.password != settings.admin_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya şifre hatalı",
        )
    token = create_access_token(data.username)
    return LoginResponse(access_token=token, username=data.username)


@router.get("/me", response_model=MeResponse)
def me(username: str = Depends(get_current_admin)):
    """Get current admin - requires Bearer token."""
    return MeResponse(username=username)

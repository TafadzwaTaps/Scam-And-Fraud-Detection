"""
JWT validation middleware for Supabase Auth tokens.
Supabase issues standard HS256 JWTs signed with the JWT secret.
"""
from __future__ import annotations
import os
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from config import SUPABASE_JWT_SECRET

_bearer = HTTPBearer(auto_error=False)


def _decode(token: str) -> dict:
    """Decode and validate a Supabase JWT. Raises JWTError on failure."""
    return jwt.decode(
        token,
        SUPABASE_JWT_SECRET,
        algorithms=["HS256"],
        options={"verify_aud": False},   # Supabase uses 'authenticated' audience
    )


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> dict:
    """Dependency that REQUIRES a valid JWT. Returns the decoded payload."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
        )
    try:
        payload = _decode(credentials.credentials)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
        )
    return payload


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Optional[dict]:
    """Dependency that OPTIONALLY validates a JWT. Returns None if absent/invalid."""
    if not credentials:
        return None
    try:
        return _decode(credentials.credentials)
    except JWTError:
        return None

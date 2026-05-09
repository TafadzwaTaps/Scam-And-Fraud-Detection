from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from database import get_supabase
from utils.logger import get_logger

log = get_logger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class AuthPayload(BaseModel):
    email: str
    password: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: AuthPayload):
    db = get_supabase()
    try:
        res = db.auth.sign_up({"email": payload.email, "password": payload.password})
        if res.user is None:
            raise HTTPException(status_code=400, detail="Registration failed. Check your email/password.")
        log.info(f"New user registered: {payload.email}")
        return {"message": "Registration successful. Please check your email to confirm your account."}
    except Exception as exc:
        log.warning(f"Register failed: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/login")
async def login(payload: AuthPayload):
    db = get_supabase()
    try:
        res = db.auth.sign_in_with_password({"email": payload.email, "password": payload.password})
        if res.session is None:
            raise HTTPException(status_code=401, detail="Invalid credentials.")
        return {
            "access_token": res.session.access_token,
            "token_type": "bearer",
            "user_id": res.user.id,
            "email": res.user.email,
        }
    except Exception as exc:
        log.warning(f"Login failed for {payload.email}: {exc}")
        raise HTTPException(status_code=401, detail="Invalid email or password.")


@router.post("/logout")
async def logout():
    # JWT is stateless; client should discard the token
    return {"message": "Logged out successfully."}

"""
Authentication API Router for TRANSLARA (Register, Login, Profile).
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.auth.security import create_access_token, get_password_hash, verify_password
from backend.database.models import User
from backend.database.session import get_db

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# --- Schemas ---

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    role: Optional[str] = Field(default="teacher")
    preferred_source_lang: Optional[str] = Field(default="ta")
    preferred_target_lang: Optional[str] = Field(default="ml")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str
    preferred_source_lang: Optional[str] = "ta"
    preferred_target_lang: Optional[str] = "ml"
    is_active: bool


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# --- Routes ---

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new teacher or admin account in TRANSLARA MSSQL database."""
    # Check if email is already taken
    existing_user = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    # Validate role
    role = req.role.lower() if req.role else "teacher"
    if role not in ("teacher", "admin"):
        role = "teacher"

    # Create user with hashed password
    user = User(
        name=req.name.strip(),
        email=req.email.lower().strip(),
        password_hash=get_password_hash(req.password),
        role=role,
        preferred_source_lang=req.preferred_source_lang or "ta",
        preferred_target_lang=req.preferred_target_lang or "ml",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate JWT
    token = create_access_token(subject=user.id, role=user.role)

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate with email and password to receive a JWT access token."""
    user = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    token = create_access_token(subject=user.id, role=user.role)

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get profile of the currently authenticated user."""
    return UserResponse.model_validate(current_user)

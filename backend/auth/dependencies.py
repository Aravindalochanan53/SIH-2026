"""
Authentication and Authorization dependencies for FastAPI routes.
"""
from __future__ import annotations

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.auth.security import decode_access_token
from backend.database.models import User
from backend.database.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Retrieve user if valid bearer token is provided; otherwise returns None."""
    if not token:
        return None

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None

    user_id_or_email = payload.get("sub")
    try:
        if str(user_id_or_email).isdigit():
            user = db.query(User).filter(User.id == int(user_id_or_email)).first()
        else:
            user = db.query(User).filter(User.email == str(user_id_or_email)).first()
        return user
    except Exception:
        return None


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Enforce authentication: raises 401 Unauthorized if invalid or missing token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise credentials_exception

    user_id_or_email = payload.get("sub")
    try:
        if str(user_id_or_email).isdigit():
            user = db.query(User).filter(User.id == int(user_id_or_email)).first()
        else:
            user = db.query(User).filter(User.email == str(user_id_or_email)).first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {e}")

    if user is None or not user.is_active:
        raise credentials_exception

    return user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Enforce administrator role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required",
        )
    return current_user

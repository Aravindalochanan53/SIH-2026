"""
Authentication module for TRANSLARA.
"""
from backend.auth.dependencies import get_admin_user, get_current_user, get_optional_user
from backend.auth.router import router
from backend.auth.security import create_access_token, decode_access_token, get_password_hash, verify_password

__all__ = [
    "router",
    "get_current_user",
    "get_optional_user",
    "get_admin_user",
    "create_access_token",
    "decode_access_token",
    "get_password_hash",
    "verify_password",
]

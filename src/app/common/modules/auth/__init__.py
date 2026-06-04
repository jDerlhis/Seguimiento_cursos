"""
Autenticación Supabase (email/contraseña).
"""

from app.common.modules.auth.service import (
    get_current_user,
    is_authenticated,
    sign_in_with_password,
    sign_out,
    sign_up_with_password,
)
from app.common.modules.auth.types import AuthError, EmailCredentials

__all__ = [
    "AuthError",
    "EmailCredentials",
    "get_current_user",
    "is_authenticated",
    "sign_in_with_password",
    "sign_out",
    "sign_up_with_password",
]

from data.entities.auth_user import AuthUser
from app.common.modules.auth import (
    AuthError,
    EmailCredentials,
    get_current_user,
    is_authenticated,
    sign_in_with_password,
    sign_out,
    sign_up_with_password,
)

__all__ = [
    "AuthError",
    "EmailCredentials",
    "AuthUser",
    "get_current_user",
    "is_authenticated",
    "sign_in",
    "sign_out_user",
    "sign_up",
]


def sign_in(credentials: EmailCredentials) -> AuthUser:
    return sign_in_with_password(credentials)


def sign_up(credentials: EmailCredentials) -> AuthUser:
    return sign_up_with_password(credentials)


def sign_out_user() -> None:
    sign_out()

from data.entities.auth_user import AuthUser
from app.common.modules.auth.types import AuthError, EmailCredentials
from infra.supabase.client import get_client, reset_client_cache
from infra.supabase.session import (
    clear_persisted_session,
    persist_session_from_client,
)
from shared.logger import get_logger

logger = get_logger(__name__)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _map_auth_exception(exc: Exception) -> AuthError:
    msg = str(exc)
    code = getattr(exc, "code", None)
    if hasattr(exc, "message") and exc.message:
        msg = str(exc.message)
    return AuthError(message=msg or "Error de autenticación", code=code)


def sign_in_with_password(credentials: EmailCredentials) -> AuthUser:
    email = _normalize_email(credentials.email)
    if not email or not credentials.password:
        raise AuthError("Email y contraseña son obligatorios.")

    client = get_client()
    try:
        response = client.auth.sign_in_with_password(
            {"email": email, "password": credentials.password}
        )
    except Exception as ex:
        logger.warning("sign_in falló: %s", ex)
        raise _map_auth_exception(ex) from ex

    user = AuthUser.from_auth(response.user)
    if not user:
        raise AuthError("No se recibió usuario tras el inicio de sesión.")

    persist_session_from_client(client)
    return user


def sign_up_with_password(credentials: EmailCredentials) -> AuthUser:
    email = _normalize_email(credentials.email)
    if not email or not credentials.password:
        raise AuthError("Email y contraseña son obligatorios.")
    if len(credentials.password) < 6:
        raise AuthError("La contraseña debe tener al menos 6 caracteres.")

    client = get_client()
    try:
        response = client.auth.sign_up(
            {"email": email, "password": credentials.password}
        )
    except Exception as ex:
        logger.warning("sign_up falló: %s", ex)
        raise _map_auth_exception(ex) from ex

    user = AuthUser.from_auth(response.user)
    if not user:
        raise AuthError("No se pudo crear la cuenta.")

    if response.session:
        persist_session_from_client(client)
    else:
        raise AuthError(
            "Cuenta creada. Revisa tu correo para confirmar el registro antes de iniciar sesión.",
            code="email_confirmation_required",
        )

    return user


def sign_out() -> None:
    client = get_client()
    clear_persisted_session(client)
    reset_client_cache()


def get_current_user() -> AuthUser | None:
    try:
        client = get_client()
        session = client.auth.get_session()
        if not session or not session.user:
            return None
        return AuthUser.from_auth(session.user)
    except Exception:
        return None


def is_authenticated() -> bool:
    return get_current_user() is not None

from data.entities.auth_user import AuthUser
from app.common.modules.auth.email_confirm import (
    auto_confirm_enabled,
    confirm_user_by_email,
    confirm_user_by_id,
    is_email_not_confirmed_error,
)
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

    lower = msg.lower()
    if is_email_not_confirmed_error(exc):
        if auto_confirm_enabled():
            msg = "No se pudo confirmar el correo automáticamente. Reintenta iniciar sesión."
        else:
            msg = (
                "Debes confirmar el correo antes de iniciar sesión. "
                "Añade PY_SUPABASE_SERVICE_ROLE_KEY en .env o desactiva "
                "'Confirm email' en Supabase → Authentication."
            )
        code = "email_not_confirmed"
    elif "invalid format" in lower or "unable to validate email" in lower:
        msg = "El formato del correo no es válido."
        code = "invalid_email"
    elif "already registered" in lower or "user already exists" in lower:
        msg = "Ese correo ya está registrado. Usa «Iniciar sesión»."
        code = "user_already_registered"

    return AuthError(message=msg or "Error de autenticación", code=code)


def _sign_in_with_password_raw(email: str, password: str):
    client = get_client()
    return client.auth.sign_in_with_password(
        {"email": email, "password": password}
    )


def sign_in_with_password(
    credentials: EmailCredentials,
    *,
    _allow_confirm_retry: bool = True,
) -> AuthUser:
    email = _normalize_email(credentials.email)
    if not email or not credentials.password:
        raise AuthError("Email y contraseña son obligatorios.")

    try:
        response = _sign_in_with_password_raw(email, credentials.password)
    except Exception as ex:
        if (
            _allow_confirm_retry
            and auto_confirm_enabled()
            and is_email_not_confirmed_error(ex)
        ):
            if confirm_user_by_email(email):
                return sign_in_with_password(
                    credentials,
                    _allow_confirm_retry=False,
                )
        logger.warning("sign_in falló: %s", ex)
        raise _map_auth_exception(ex) from ex

    user = AuthUser.from_auth(response.user)
    if not user:
        raise AuthError("No se recibió usuario tras el inicio de sesión.")

    persist_session_from_client(get_client())
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
        return user

    if auto_confirm_enabled() and user.id:
        try:
            confirm_user_by_id(user.id)
            return sign_in_with_password(credentials, _allow_confirm_retry=False)
        except Exception as ex:
            logger.warning("Auto-confirmación tras registro falló: %s", ex)

    raise AuthError(
        "Cuenta creada pero no hay sesión. Configura PY_SUPABASE_SERVICE_ROLE_KEY "
        "o desactiva la confirmación de correo en Supabase.",
        code="email_confirmation_required",
    )


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

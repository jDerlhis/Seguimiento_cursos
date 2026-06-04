"""Confirmación de correo vía Admin API (sin validación por enlace)."""

from infra.config.settings import PY_SUPABASE_AUTO_CONFIRM_EMAIL, PY_SUPABASE_SERVICE_ROLE_KEY
from infra.supabase.admin_client import get_admin_client
from shared.logger import get_logger

logger = get_logger(__name__)


def auto_confirm_enabled() -> bool:
    return PY_SUPABASE_AUTO_CONFIRM_EMAIL and bool(PY_SUPABASE_SERVICE_ROLE_KEY)


def is_email_not_confirmed_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "email not confirmed" in msg or "email_not_confirmed" in msg


def confirm_user_by_id(user_id: str) -> None:
    admin = get_admin_client()
    admin.auth.admin.update_user_by_id(user_id, {"email_confirm": True})


def confirm_user_by_email(email: str) -> str | None:
    admin = get_admin_client()
    normalized = email.strip().lower()
    page = 1
    per_page = 200

    while True:
        result = admin.auth.admin.list_users(page=page, per_page=per_page)
        users = getattr(result, "users", None) or []
        for user in users:
            user_email = (getattr(user, "email", None) or "").strip().lower()
            if user_email == normalized:
                user_id = getattr(user, "id", None)
                if not user_id:
                    return None
                confirm_user_by_id(str(user_id))
                logger.info("Correo confirmado automáticamente para %s", normalized)
                return str(user_id)
        if len(users) < per_page:
            break
        page += 1

    logger.warning("No se encontró usuario con email %s para confirmar", normalized)
    return None

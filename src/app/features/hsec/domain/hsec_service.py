from app.common.modules.hsec import LoginResult, SyncResult, login_hsec, sync_hsec
from app.common.modules.hsec.persistence import load_active_session
from infra.supabase.tenant import get_tenant_id


def get_session() -> dict | None:
    """Devuelve la sesión activa del tenant actual, o None si no existe."""
    return load_active_session(get_tenant_id())


def connect(mfa_code: str = "") -> LoginResult:
    """Inicia o reutiliza una sesión HSEC para el tenant actual."""
    return login_hsec(get_tenant_id(), mfa_code=mfa_code)


def sync(dnis: list[str]) -> list[SyncResult]:
    """Sincroniza personas y cursos HSEC para la lista de DNIs dada."""
    return sync_hsec(get_tenant_id(), dnis)

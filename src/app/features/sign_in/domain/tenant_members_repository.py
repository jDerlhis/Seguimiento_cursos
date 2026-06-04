from data import schema
from data.entities.tenant_member import TenantMember, TenantMemberRole
from infra.config.settings import PY_SUPABASE_TENANT_SLUG
from infra.supabase.client import get_client
from infra.supabase.tenant_resolve import resolve_tenant_id_by_slug
from shared.logger import get_logger

logger = get_logger(__name__)

_MEMBER_COLUMNS = "id, tenant_id, user_id, role, created_at, updated_at"


def _fetch_own_membership(client, tenant_id: str, user_id: str) -> TenantMember | None:
    try:
        response = (
            client.table(schema.TENANT_MEMBERS)
            .select(_MEMBER_COLUMNS)
            .eq("tenant_id", tenant_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return TenantMember.from_record(rows[0]) if rows else None
    except Exception as ex:
        logger.debug("fetch_own_membership: %s", ex)
        return None


def ensure_desktop_tenant_membership(user_id: str) -> TenantMember | None:
    """
    Vincula al usuario con el tenant pyflow-desktop (INSERT bajo RLS).
    Requiere políticas tenant_members_insert_self_pyflow_desktop y tenant_members_select_self.
    """
    client = get_client()
    tenant_id = resolve_tenant_id_by_slug(PY_SUPABASE_TENANT_SLUG)
    if not tenant_id:
        logger.warning("Tenant slug '%s' no encontrado", PY_SUPABASE_TENANT_SLUG)
        return None

    existing = _fetch_own_membership(client, tenant_id, user_id)
    if existing:
        return existing

    member = TenantMember(
        tenant_id=tenant_id,
        user_id=user_id,
        role=TenantMemberRole.MEMBER,
    )
    try:
        inserted = (
            client.table(schema.TENANT_MEMBERS)
            .insert(member.to_record())
            .select(_MEMBER_COLUMNS)
            .execute()
        )
        ins_rows = inserted.data or []
        if ins_rows:
            return TenantMember.from_record(ins_rows[0])
    except Exception as ex:
        err = str(ex).lower()
        if "duplicate" in err or "23505" in err or "already exists" in err:
            return _fetch_own_membership(client, tenant_id, user_id)
        logger.warning(
            "No se pudo insertar tenant_member: %s. "
            "Ejecuta en Supabase las migraciones 20260605000001 y 20260607000001.",
            ex,
        )
        return None

    return _fetch_own_membership(client, tenant_id, user_id)

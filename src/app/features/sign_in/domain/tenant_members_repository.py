from data import schema
from data.entities.tenant_member import TenantMember, TenantMemberRole
from infra.config.settings import PY_SUPABASE_TENANT_SLUG
from infra.supabase.client import get_client
from shared.logger import get_logger

logger = get_logger(__name__)


def _tenant_id_by_slug(slug: str) -> str | None:
    response = (
        get_client()
        .table(schema.TENANTS)
        .select("id")
        .eq("slug", slug)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0]["id"] if rows else None


def ensure_desktop_tenant_membership(user_id: str) -> TenantMember | None:
    """
    Vincula al usuario con el tenant pyflow-desktop (INSERT bajo RLS).
    """
    client = get_client()
    tenant_id = _tenant_id_by_slug(PY_SUPABASE_TENANT_SLUG)
    if not tenant_id:
        logger.warning("Tenant slug '%s' no encontrado", PY_SUPABASE_TENANT_SLUG)
        return None

    existing = (
        client.table(schema.TENANT_MEMBERS)
        .select("id, tenant_id, user_id, role, created_at, updated_at")
        .eq("tenant_id", tenant_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    rows = existing.data or []
    if rows:
        return TenantMember.from_record(rows[0])

    member = TenantMember(
        tenant_id=tenant_id,
        user_id=user_id,
        role=TenantMemberRole.MEMBER,
    )
    try:
        inserted = (
            client.table(schema.TENANT_MEMBERS)
            .insert(member.to_record())
            .select("id, tenant_id, user_id, role, created_at, updated_at")
            .execute()
        )
        ins_rows = inserted.data or []
        return TenantMember.from_record(ins_rows[0]) if ins_rows else None
    except Exception as ex:
        logger.warning("No se pudo insertar tenant_member: %s", ex)
        return None

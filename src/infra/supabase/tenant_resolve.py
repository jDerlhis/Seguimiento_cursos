from data import schema
from infra.config.settings import PY_SUPABASE_TENANT_ID, PY_SUPABASE_TENANT_SLUG
from infra.supabase.client import get_client
from infra.supabase.public_client import get_public_client
from shared.logger import get_logger

logger = get_logger(__name__)


def resolve_tenant_id_by_slug(slug: str) -> str | None:
    """
    Resuelve el UUID del tenant por slug.
    Usa PY_SUPABASE_TENANT_ID si coincide el slug por defecto, luego cliente anon
    (política tenants_pyflow_desktop_select) y por último el cliente con sesión.
    """
    if PY_SUPABASE_TENANT_ID and slug == PY_SUPABASE_TENANT_SLUG:
        return PY_SUPABASE_TENANT_ID

    for label, client in (
        ("anon", get_public_client()),
        ("authenticated", get_client()),
    ):
        try:
            response = (
                client.table(schema.TENANTS)
                .select("id")
                .eq("slug", slug)
                .limit(1)
                .execute()
            )
            rows = response.data or []
            if rows:
                return rows[0]["id"]
        except Exception as ex:
            logger.debug("resolve_tenant_id_by_slug (%s): %s", label, ex)

    return None

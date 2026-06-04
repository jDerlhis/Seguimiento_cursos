from functools import lru_cache

from data import schema
from infra.config.settings import PY_SUPABASE_TENANT_ID, PY_SUPABASE_TENANT_SLUG
from infra.supabase.client import get_client


@lru_cache(maxsize=1)
def get_tenant_id() -> str:
    if PY_SUPABASE_TENANT_ID:
        return PY_SUPABASE_TENANT_ID

    slug = PY_SUPABASE_TENANT_SLUG
    if not slug:
        raise RuntimeError(
            "Configura PY_SUPABASE_TENANT_ID o PY_SUPABASE_TENANT_SLUG en .env"
        )

    response = (
        get_client()
        .table(schema.TENANTS)
        .select("id")
        .eq("slug", slug)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    if not rows:
        raise RuntimeError(
            f"No existe tenant con slug '{slug}'. "
            "Aplica las migraciones de Supabase o define PY_SUPABASE_TENANT_ID."
        )
    return rows[0]["id"]

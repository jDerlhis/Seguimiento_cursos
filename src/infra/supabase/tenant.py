from functools import lru_cache

from infra.config.settings import PY_SUPABASE_TENANT_SLUG
from infra.supabase.tenant_resolve import resolve_tenant_id_by_slug


@lru_cache(maxsize=1)
def get_tenant_id() -> str:
    slug = PY_SUPABASE_TENANT_SLUG
    if not slug:
        raise RuntimeError(
            "Configura PY_SUPABASE_TENANT_ID o PY_SUPABASE_TENANT_SLUG en .env"
        )

    tenant_id = resolve_tenant_id_by_slug(slug)
    if not tenant_id:
        raise RuntimeError(
            f"No existe tenant con slug '{slug}'. "
            "Aplica las migraciones de Supabase o define PY_SUPABASE_TENANT_ID en .env."
        )
    return tenant_id

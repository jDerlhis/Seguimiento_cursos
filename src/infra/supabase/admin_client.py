from functools import lru_cache

from supabase import Client, create_client

from infra.config.settings import PY_SUPABASE_SERVICE_ROLE_KEY, PY_SUPABASE_URL


@lru_cache(maxsize=1)
def get_admin_client() -> Client:
    if not PY_SUPABASE_URL:
        raise RuntimeError("Configura PY_SUPABASE_URL en .env")
    if not PY_SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError(
            "Configura PY_SUPABASE_SERVICE_ROLE_KEY en .env para auto-confirmar correos."
        )
    return create_client(PY_SUPABASE_URL, PY_SUPABASE_SERVICE_ROLE_KEY)

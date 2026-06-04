"""Cliente Supabase sin sesión de usuario (rol anon) para lecturas públicas acotadas por RLS."""

from functools import lru_cache

from supabase import Client, create_client

from infra.config.settings import PY_SUPABASE_PUBLISHABLE_KEY, PY_SUPABASE_URL


@lru_cache(maxsize=1)
def get_public_client() -> Client:
    if not PY_SUPABASE_URL or not PY_SUPABASE_PUBLISHABLE_KEY:
        raise RuntimeError("Configura PY_SUPABASE_URL y PY_SUPABASE_PUBLISHABLE_KEY en .env")
    return create_client(PY_SUPABASE_URL, PY_SUPABASE_PUBLISHABLE_KEY)


def reset_public_client_cache() -> None:
    get_public_client.cache_clear()

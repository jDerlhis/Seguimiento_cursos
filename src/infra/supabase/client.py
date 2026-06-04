from functools import lru_cache

from supabase import Client, create_client

from infra.config.settings import (
    PY_SUPABASE_PUBLISHABLE_KEY,
    PY_SUPABASE_SERVICE_ROLE_KEY,
    PY_SUPABASE_URL,
)


def _api_key() -> str:
    if PY_SUPABASE_PUBLISHABLE_KEY:
        return PY_SUPABASE_PUBLISHABLE_KEY
    if PY_SUPABASE_SERVICE_ROLE_KEY:
        return PY_SUPABASE_SERVICE_ROLE_KEY
    raise RuntimeError(
        "Configura PY_SUPABASE_PUBLISHABLE_KEY (o PY_SUPABASE_SERVICE_ROLE_KEY) en .env"
    )


@lru_cache(maxsize=1)
def get_client() -> Client:
    if not PY_SUPABASE_URL:
        raise RuntimeError("Configura PY_SUPABASE_URL en .env")
    client = create_client(PY_SUPABASE_URL, _api_key())
    from infra.supabase.session import apply_persisted_session

    apply_persisted_session(client)
    return client


def reset_client_cache() -> None:
    get_client.cache_clear()
    from infra.supabase.public_client import reset_public_client_cache

    reset_public_client_cache()

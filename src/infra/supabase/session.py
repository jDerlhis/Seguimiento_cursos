from supabase import Client

_session_tokens: dict[str, str] | None = None


def apply_persisted_session(client: Client) -> bool:
    if not _session_tokens:
        return False
    try:
        client.auth.set_session(
            _session_tokens["access_token"],
            _session_tokens["refresh_token"],
        )
        return client.auth.get_session() is not None
    except Exception:
        _clear_tokens()
        return False


def persist_session_from_client(client: Client) -> None:
    global _session_tokens
    session = client.auth.get_session()
    if session and session.access_token and session.refresh_token:
        _session_tokens = {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
        }


def clear_persisted_session(client: Client) -> None:
    _clear_tokens()
    try:
        client.auth.sign_out()
    except Exception:
        pass


def _clear_tokens() -> None:
    global _session_tokens
    _session_tokens = None

from pathlib import Path

from infra.config.settings import HSEC_SESSION_FILE


def session_path() -> Path:
    return HSEC_SESSION_FILE


def has_saved_session() -> bool:
    path = session_path()
    return path.is_file() and path.stat().st_size > 0


def clear_session() -> None:
    path = session_path()
    if path.is_file():
        path.unlink()


def save_storage_state(context) -> None:
    path = session_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=str(path))

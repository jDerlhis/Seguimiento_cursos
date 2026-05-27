"""Prueba conexión IMAP y búsqueda de código MFA en el buzón."""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(ROOT))

from infra.auth.mfa_email_fetcher import is_mfa_email_configured, poll_mfa_code_once
from infra.config.settings import MFA_IMAP_HOST, MFA_IMAP_USER


def main() -> int:
    if not is_mfa_email_configured():
        print("Configura MFA_IMAP_USER y MFA_IMAP_PASSWORD en .env")
        return 1

    since = datetime.now(timezone.utc) - timedelta(hours=24)
    print(f"IMAP: {MFA_IMAP_USER} @ {MFA_IMAP_HOST}")
    print(f"Buscando códigos desde {since.isoformat()}...")

    code = poll_mfa_code_once(since=since)
    if code:
        print(f"Código encontrado: {code[:2]}****{code[-2:]}")
        return 0

    print("No se encontró código MFA reciente en el buzón.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

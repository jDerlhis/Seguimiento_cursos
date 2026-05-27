"""Prueba del flujo de login HSEC (sin UI Flet)."""
import sys
import threading  # noqa: F401 — usado en _stdin_mfa_handler
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(ROOT))

from infra.auth.mfa_coordinator import MfaRequest, mfa_coordinator
from infra.auth.session_store import clear_session, has_saved_session
from infra.scraping.hsec_scraper import login_hsec


def _stdin_reader() -> None:
    print("Comandos: 6 dígitos | 'r' = reenviar | Enter vacío = cancelar")
    while mfa_coordinator.is_session_active():
        value = input("MFA> ").strip()
        if not value:
            mfa_coordinator.cancel()
            return
        if value.lower() in ("r", "reenviar"):
            mfa_coordinator.request_resend()
            print("Reenvío solicitado…")
            continue
        if len(value) == 6 and value.isdigit():
            mfa_coordinator.submit_code(value)
            return
        print("Usa 6 dígitos, 'r' para reenviar o Enter para cancelar.")


def _stdin_mfa_handler(request: MfaRequest) -> None:
    print("\n--- MFA requerido ---")
    print(request.message)
    threading.Thread(target=_stdin_reader, daemon=True).start()


def main() -> int:
    print("=== Test login HSEC ===")
    print(f"Sesión guardada antes: {has_saved_session()}")

    mfa_coordinator.set_ui_handler(_stdin_mfa_handler)

    try:
        result = login_hsec()
        print(f"OK: {result.message}")
        print(f"  sesión reutilizada: {result.used_saved_session}")
        print(f"  MFA usado: {result.mfa_required}")
        print(f"Sesión guardada después: {has_saved_session()}")
        return 0
    except Exception as ex:
        print(f"FALLO: {ex}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

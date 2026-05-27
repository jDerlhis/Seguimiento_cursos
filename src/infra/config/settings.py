import os
from pathlib import Path

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_PROJECT_ROOT / ".env")

HSEC_BASE_URL = os.getenv(
    "HSEC_BASE_URL",
    "https://antapaccay.sam.glencore.net/hsec_web/",
).rstrip("/") + "/"

HSEC_DASHBOARD_URL = os.getenv(
    "HSEC_DASHBOARD_URL",
    f"{HSEC_BASE_URL}#/dashboard",
)

HSEC_USERNAME = os.getenv("HSEC_USERNAME", "")
HSEC_PASSWORD = os.getenv("HSEC_PASSWORD", "")

PYFLOW_WEBHOOK_URL = os.getenv("PYFLOW_WEBHOOK_URL", "").strip()

# Carpeta dedicada en el proyecto: Pyflow/sessions/
SESSIONS_DIR = Path(
    os.getenv(
        "PYFLOW_SESSIONS_DIR",
        str(_PROJECT_ROOT / "sessions"),
    )
)
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

HSEC_SESSION_FILE = SESSIONS_DIR / "hsec_storage_state.json"

PLAYWRIGHT_HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() in (
    "1",
    "true",
    "yes",
)

# 0 = esperar sin límite mientras el modal MFA esté abierto (recomendado)
MFA_WAIT_TIMEOUT_SEC = int(os.getenv("MFA_WAIT_TIMEOUT_SEC", "0"))

# Buzón donde llega el código MFA (lectura automática vía IMAP)
MFA_EMAIL_ENABLED = os.getenv("MFA_EMAIL_ENABLED", "true").lower() in (
    "1",
    "true",
    "yes",
)
MFA_IMAP_USER = os.getenv("MFA_IMAP_USER", "").strip()
MFA_IMAP_PASSWORD = os.getenv("MFA_IMAP_PASSWORD", "")
MFA_IMAP_HOST = os.getenv("MFA_IMAP_HOST", "sermull.com").strip()
MFA_IMAP_PORT = int(os.getenv("MFA_IMAP_PORT", "993"))
MFA_IMAP_FOLDER = os.getenv("MFA_IMAP_FOLDER", "INBOX")
MFA_POLL_INTERVAL_SEC = float(os.getenv("MFA_POLL_INTERVAL_SEC", "4"))
MFA_POLL_TIMEOUT_SEC = int(os.getenv("MFA_POLL_TIMEOUT_SEC", "180"))

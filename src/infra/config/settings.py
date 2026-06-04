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

PLAYWRIGHT_HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() in (
    "1",
    "true",
    "yes",
)

MFA_WAIT_TIMEOUT_SEC = int(os.getenv("MFA_WAIT_TIMEOUT_SEC", "0"))

MFA_EMAIL_ENABLED = os.getenv("MFA_EMAIL_ENABLED", "true").lower() in (
    "1",
    "true",
    "yes",
)

PY_SUPABASE_URL = os.getenv("PY_SUPABASE_URL", "").strip()
PY_SUPABASE_PUBLISHABLE_KEY = os.getenv("PY_SUPABASE_PUBLISHABLE_KEY", "").strip()
PY_SUPABASE_SERVICE_ROLE_KEY = os.getenv("PY_SUPABASE_SERVICE_ROLE_KEY", "").strip()
PY_SUPABASE_TENANT_ID = os.getenv("PY_SUPABASE_TENANT_ID", "").strip()
PY_SUPABASE_TENANT_SLUG = os.getenv("PY_SUPABASE_TENANT_SLUG", "pyflow-desktop").strip()

# Sin confirmación por enlace: confirma correos vía Admin API (requiere service role).
PY_SUPABASE_AUTO_CONFIRM_EMAIL = os.getenv(
    "PY_SUPABASE_AUTO_CONFIRM_EMAIL", "true"
).lower() in ("1", "true", "yes")

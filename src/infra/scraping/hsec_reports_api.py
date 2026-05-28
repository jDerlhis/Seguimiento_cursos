# src/infra/scraping/hsec_reports_api.py

import json
from io import BytesIO                    # ← para convertir bytes a archivo
import openpyxl                           # ← para leer el Excel
import httpx
from infra.auth.session_store import session_path, has_saved_session
from shared.logger import get_logger

logger = get_logger(__name__)


def download_training_report(cod_persona: str) -> list[dict]:
    if not has_saved_session():
        raise RuntimeError("No hay sesión activa. Inicia sesión en HSEC primero.")

    # --- leer token y cookies (igual que hsec_api.py) ---
    token = None
    cookies_dict = {}
    with open(session_path(), "r", encoding="utf-8") as f:
        state = json.load(f)
    for cookie in state.get("cookies", []):
        cookies_dict[cookie["name"]] = cookie["value"]
    for origin in state.get("origins", []):
        for item in origin.get("localStorage", []):
            if "eyJhbGciOi" in item.get("value", ""):
                token = item["value"].strip('"')
                break

    if not token:
        raise RuntimeError("No se encontró token JWT. Inicia sesión de nuevo.")

    # --- descargar el Excel desde SSRS ---
    url = (
        "https://antapaccay.sam.glencore.net/ReportViewer/Report.aspx"
        "?%2fPBI_Seguridad%2fHSEC%2fCapacitaciones%2fCursoReporteDetallado"
        "&rs%3aFormat=EXCELOPENXML"
        f"&CodPersona={cod_persona}"
        "&rs%3aParameterLanguage=en-us"
    )
    headers = {
        "authorization": f"Bearer {token}",
        "referer": "https://antapaccay.sam.glencore.net/hsec_web/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    }

    with httpx.Client(verify=False, follow_redirects=True) as client:
        logger.info(f"Descargando reporte de capacitaciones para {cod_persona}...")
        response = client.get(url, headers=headers, cookies=cookies_dict, timeout=60.0)
        if response.status_code == 401:
            raise RuntimeError("Sesión expirada (401). Inicia sesión de nuevo.")
        response.raise_for_status()

    # --- parsear el Excel con openpyxl ---      ← AQUÍ
    wb = openpyxl.load_workbook(BytesIO(response.content))
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    headers_row = rows[0]
    return [dict(zip(headers_row, row)) for row in rows[1:] if any(row)]
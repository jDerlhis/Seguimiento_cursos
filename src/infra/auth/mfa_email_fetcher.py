"""Obtiene el codigo MFA alfanumerico desde el buzon IMAP configurado en .env.

Formato del correo HSEC:
  Asunto : Antapaccay HSEC - Codigo de autenticacion (2FA)
  Remite : svc-tya-notificacion@glencore.com.pe
  Cuerpo : ... Aqui tiene su codigo de verificacion: H3LP41 ...
"""

from __future__ import annotations

import email
import imaplib
from shared.logger import get_logger
import re
import time
from datetime import datetime, timezone
from email.header import decode_header
from email.utils import parsedate_to_datetime

from infra.config.settings import (
    MFA_EMAIL_ENABLED,
    MFA_IMAP_FOLDER,
    MFA_IMAP_HOST,
    MFA_IMAP_PASSWORD,
    MFA_IMAP_PORT,
    MFA_IMAP_USER,
    MFA_POLL_INTERVAL_SEC,
    MFA_POLL_TIMEOUT_SEC,
)

logger = get_logger(__name__)

# Pistas en el asunto para priorizar correos HSEC
_SUBJECT_HINTS = (
    "antapaccay hsec",
    "hsec",
    "codigo de autenticacion",
    "autenticacion (2fa)",
    "2fa",
    "verific",
    "codigo",
    "glencore",
    "sam",
    "acceso",
    "doble factor",
    "one-time",
    "otp",
)

# Remitente esperado de HSEC (para priorizar, no filtrar)
_EXPECTED_SENDER = "glencore.com.pe"

# Patrones en orden de prioridad para extraer el codigo MFA alfanumerico
# El codigo HSEC es de 6 caracteres: letras mayusculas y/o digitos (ej: H3LP41, 94CTX2)
_CODE_PATTERNS = (
    # P1: despues de "codigo de verificacion:" (formato exacto del correo HSEC)
    re.compile(
        r"c[oó]digo\s+de\s+verificaci[oó]n\s*[:\-]?\s*([A-Z0-9]{6})\b",
        re.I,
    ),
    # P2: despues de cualquier mencion de codigo/code/verificacion
    re.compile(
        r"(?:c[oó]digo|code|verificaci[oó]n|contrase[nñ]a\s+temporal)"
        r"[^\w]{0,60}([A-Z0-9]{6})\b",
        re.I,
    ),
    # P3: codigo solo en su propia linea (tipico en HTML convertido a texto)
    re.compile(r"^\s*([A-Z0-9]{6})\s*$", re.I | re.MULTILINE),
    # P4: codigo entre espacios/saltos con al menos 1 letra y 1 digito (mezcla alfanumerica)
    re.compile(r"(?<!\w)([A-Z]{1,5}[0-9]{1,5}|[0-9]{1,5}[A-Z]{1,5})(?!\w)", re.I),
    # P5: fallback — cualquier bloque de exactamente 6 alfanumericos aislado
    re.compile(r"(?<![A-Z0-9])([A-Z0-9]{6})(?![A-Z0-9])", re.I),
)

# Tokens de 6 chars que NO son codigos MFA (falsos positivos comunes)
_IGNORE_TOKENS = {
    "000000", "CORREO", "HOLA", "HSECWB", "CODIGO", "VERIFY",
    "BEFORE", "USANDO", "DENTRO", "CUENTA", "CLAVES",
}


def is_mfa_email_configured() -> bool:
    return MFA_EMAIL_ENABLED and bool(MFA_IMAP_USER and MFA_IMAP_PASSWORD and MFA_IMAP_HOST)


def _decode_header_value(value: str | None) -> str:
    if not value:
        return ""
    parts: list[str] = []
    for chunk, enc in decode_header(value):
        if isinstance(chunk, bytes):
            parts.append(chunk.decode(enc or "utf-8", errors="replace"))
        else:
            parts.append(str(chunk))
    return "".join(parts)


def _message_datetime(msg: email.message.Message) -> datetime | None:
    raw = msg.get("Date")
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None


def _strip_html(html: str) -> str:
    """Elimina tags HTML y decodifica entidades basicas para dejar texto limpio."""
    # Reemplazar tags de bloque con salto de linea
    text = re.sub(r"<(?:br|p|div|td|tr|h\d)[^>]*>", "\n", html, flags=re.I)
    # Eliminar todos los tags restantes
    text = re.sub(r"<[^>]+>", " ", text)
    # Decodificar entidades HTML comunes
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = text.replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&#39;", "'").replace("&quot;", '"')
    # Colapsar espacios multiples pero conservar saltos de linea
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_text_parts(msg: email.message.Message) -> str:
    """Extrae texto plano del correo, convirtiendo HTML si es necesario."""
    plain_parts: list[str] = []
    html_parts: list[str] = []

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                continue
            ctype = part.get_content_type()
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            charset = part.get_content_charset() or "utf-8"
            decoded = payload.decode(charset, errors="replace")
            if ctype == "text/plain":
                plain_parts.append(decoded)
            elif ctype == "text/html":
                html_parts.append(_strip_html(decoded))
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            decoded = payload.decode(charset, errors="replace")
            ctype = msg.get_content_type()
            if ctype == "text/html":
                html_parts.append(_strip_html(decoded))
            else:
                plain_parts.append(decoded)

    # Priorizar texto plano; si no hay, usar HTML convertido
    parts = plain_parts if plain_parts else html_parts
    return "\n".join(parts)


def _subject_matches(subject: str) -> bool:
    lower = subject.lower()
    return any(hint in lower for hint in _SUBJECT_HINTS)


def _sender_matches(msg: email.message.Message) -> bool:
    sender = _decode_header_value(msg.get("From", "")).lower()
    return _EXPECTED_SENDER in sender


def _is_valid_mfa_code(code: str) -> bool:
    upper = code.upper()
    if len(upper) != 6:
        return False
    if upper in _IGNORE_TOKENS:
        return False
    if not re.match(r"^[A-Z0-9]{6}$", upper):
        return False
    return True


def _extract_code(text: str) -> str | None:
    """
    Extrae el codigo MFA alfanumerico de 6 caracteres del texto del correo.
    Ejemplos: H3LP41, 94CTX2, 123456, ABCDEF
    """
    for i, pattern in enumerate(_CODE_PATTERNS):
        for match in pattern.finditer(text):
            code = match.group(1).upper().strip()
            if _is_valid_mfa_code(code):
                logger.debug(
                    "Patron P%d encontro candidato: ****%s en contexto: %r",
                    i + 1,
                    code[-2:],
                    text[max(0, match.start()-20):match.end()+20],
                )
                return code
    return None


def _fetch_recent_messages(
    conn: imaplib.IMAP4_SSL,
    *,
    since: datetime,
    limit: int = 30,
) -> list[tuple[bytes, email.message.Message]]:
    since_str = since.strftime("%d-%b-%Y")
    typ, data = conn.search(None, f"(SINCE {since_str})")
    if typ != "OK" or not data or not data[0]:
        return []

    uids = data[0].split()
    uids = uids[-limit:]
    messages: list[tuple[bytes, email.message.Message]] = []

    for uid in reversed(uids):
        typ, fetched = conn.fetch(uid, "(RFC822)")
        if typ != "OK" or not fetched:
            continue
        for item in fetched:
            if not isinstance(item, tuple) or len(item) < 2:
                continue
            msg = email.message_from_bytes(item[1])
            msg_dt = _message_datetime(msg)
            # Margen de 60 segundos para diferencias de reloj entre servidores
            if msg_dt and (msg_dt.timestamp() + 60) < since.timestamp():
                continue
            messages.append((uid, msg))
    return messages


def poll_mfa_code_once(
    *,
    since: datetime,
    used_codes: set[str] | None = None,
) -> str | None:
    """Lee el buzon una vez y devuelve el codigo MFA mas reciente, si existe."""
    if not is_mfa_email_configured():
        return None

    used = {c.upper() for c in (used_codes or set())}
    conn: imaplib.IMAP4_SSL | None = None

    try:
        conn = imaplib.IMAP4_SSL(MFA_IMAP_HOST, MFA_IMAP_PORT, timeout=15)
        conn.login(MFA_IMAP_USER, MFA_IMAP_PASSWORD)
        typ, _ = conn.select(MFA_IMAP_FOLDER, readonly=True)
        if typ != "OK":
            logger.warning("No se pudo abrir carpeta IMAP: %s", MFA_IMAP_FOLDER)
            return None

        # priority: (es_remitente_glencore, es_asunto_hsec, fecha)
        candidates: list[tuple[bool, bool, datetime, str]] = []

        for _uid, msg in _fetch_recent_messages(conn, since=since):
            subject = _decode_header_value(msg.get("Subject", ""))
            body = _extract_text_parts(msg)
            combined = f"{subject}\n{body}"
            code = _extract_code(combined)
            if not code or code in used:
                continue
            msg_dt = _message_datetime(msg) or datetime.now(timezone.utc)
            candidates.append((
                _sender_matches(msg),
                _subject_matches(subject),
                msg_dt,
                code,
            ))

        if not candidates:
            return None

        # Ordenar: primero remitente glencore, luego asunto HSEC, luego mas reciente
        candidates.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
        best = candidates[0][3]
        logger.info("Codigo MFA obtenido del correo (****%s)", best[-2:])
        return best

    except imaplib.IMAP4.error as ex:
        logger.warning("Error IMAP al leer MFA: %s", ex)
        return None
    except OSError as ex:
        logger.warning("No se pudo conectar al servidor IMAP %s:%s — %s", MFA_IMAP_HOST, MFA_IMAP_PORT, ex)
        return None
    finally:
        if conn is not None:
            try:
                conn.logout()
            except imaplib.IMAP4.error:
                pass


def wait_for_mfa_code(
    *,
    since: datetime,
    timeout_sec: int | None = None,
    poll_interval_sec: float | None = None,
    used_codes: set[str] | None = None,
) -> str | None:
    """Hace polling del buzon hasta encontrar un codigo o agotar el tiempo."""
    if not is_mfa_email_configured():
        return None

    deadline = time.monotonic() + (timeout_sec or MFA_POLL_TIMEOUT_SEC)
    interval = poll_interval_sec if poll_interval_sec is not None else MFA_POLL_INTERVAL_SEC
    used = set(used_codes or set())

    while time.monotonic() < deadline:
        code = poll_mfa_code_once(since=since, used_codes=used)
        if code:
            return code
        time.sleep(interval)

    return None
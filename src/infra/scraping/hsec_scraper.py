import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

from infra.auth.mfa_coordinator import (
    MfaAction,
    MfaActionType,
    MfaStatus,
    mfa_coordinator,
)
from infra.auth.mfa_email_fetcher import (
    is_mfa_email_configured,
    poll_mfa_code_once,
)
from infra.auth.session_store import has_saved_session, save_storage_state, session_path
from infra.config.settings import (
    HSEC_DASHBOARD_URL,
    HSEC_PASSWORD,
    HSEC_USERNAME,
    PLAYWRIGHT_HEADLESS,
)
from infra.webhooks.notifier import notify_webhook

logger = logging.getLogger(__name__)

USERNAME_SELECTORS = (
    "input[placeholder='Usuario']",
    "input[placeholder*='usuario' i]",
    "input[name='username']",
    "input[name='loginfmt']",
    "input[type='email']",
    "input[id*='user' i]",
    "input[placeholder*='user' i]",
)

PASSWORD_SELECTORS = (
    "input[placeholder='Password']",
    "input[placeholder*='password' i]",
    "input[name='password']",
    "input[name='passwd']",
    "input[type='password']",
)

SUBMIT_SELECTORS = (
    "button:has-text('Ingresar')",
    "button[type='submit']",
    "input[type='submit']",
    "button:has-text('Sign in')",
    "button:has-text('Iniciar')",
    "button:has-text('Login')",
    "button:has-text('Entrar')",
    "#login-button",
)

MFA_INPUT_SELECTORS = (
    "input[placeholder*='6 dígitos' i]",
    "input[placeholder*='6 digitos' i]",
    "input[name='otc']",
    "input[name='code']",
    "input[name='verificationCode']",
    "input[type='tel']",
    "input[inputmode='numeric']",
    "input[autocomplete='one-time-code']",
    "input[placeholder*='código' i]",
    "input[placeholder*='code' i]",
)

MFA_SUBMIT_SELECTORS = (
    "button:has-text('Validar acceso')",
    "button[type='submit']",
    "button:has-text('Verify')",
    "button:has-text('Verificar')",
    "button:has-text('Continuar')",
    "button:has-text('Submit')",
    "input[type='submit']",
)

MFA_RESEND_SELECTORS = (
    "button:has-text('Reenviar código')",
    "button:has-text('Reenviar codigo')",
    "button.btn-link:has-text('Reenviar')",
)

MFA_COUNTDOWN_SELECTOR = "#countdown"


@dataclass(frozen=True)
class LoginResult:
    success: bool
    message: str
    used_saved_session: bool = False
    mfa_required: bool = False


def _first_visible(page: Page, selectors: tuple[str, ...], timeout_ms: int = 5000):
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            locator.wait_for(state="visible", timeout=timeout_ms)
            return locator
        except PlaywrightTimeout:
            continue
    return None


def _click_first(page: Page, selectors: tuple[str, ...]) -> bool:
    for selector in selectors:
        locator = page.locator(selector).first
        if locator.count() and locator.is_visible():
            locator.click()
            return True
    return False


def _is_login_page(page: Page) -> bool:
    url = page.url.lower()
    return "#/login" in url or "/login" in url


def _is_dashboard(page: Page) -> bool:
    if _is_login_page(page):
        return False
    url = page.url.lower()
    if "#/dashboard" in url:
        return True
    return False


def _page_has_mfa_prompt(page: Page) -> bool:
    body = page.locator("body").inner_text(timeout=5000).lower()
    patterns = (
        r"doble\s+factor",
        r"validación\s+de\s+acceso",
        r"validacion\s+de\s+acceso",
        r"código\s+enviado\s+al\s+correo",
        r"codigo\s+enviado\s+al\s+correo",
        r"verification\s+code",
        r"código\s+de\s+verificación",
        r"codigo\s+de\s+verificacion",
        r"enter\s+the\s+code",
        r"revisa\s+tu\s+correo",
        r"email.*code",
        r"one.?time",
    )
    if any(re.search(p, body) for p in patterns):
        return True
    return _first_visible(page, MFA_INPUT_SELECTORS, timeout_ms=2000) is not None


def _fill_credentials(page: Page) -> None:
    if not HSEC_USERNAME or not HSEC_PASSWORD:
        raise ValueError(
            "Configura HSEC_USERNAME y HSEC_PASSWORD en el archivo .env"
        )

    user_input = _first_visible(page, USERNAME_SELECTORS, timeout_ms=15000)
    if user_input is None:
        raise RuntimeError("No se encontró el campo de usuario en la página de login.")

    user_input.fill(HSEC_USERNAME)
    page.wait_for_timeout(300)

    pass_input = _first_visible(page, PASSWORD_SELECTORS, timeout_ms=10000)
    if pass_input is None:
        raise RuntimeError("No se encontró el campo de contraseña en la página de login.")

    pass_input.fill(HSEC_PASSWORD)
    page.wait_for_timeout(300)

    if not _click_first(page, SUBMIT_SELECTORS):
        pass_input.press("Enter")

    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(2000)


def _read_mfa_status(page: Page) -> MfaStatus:
    countdown = page.locator(MFA_COUNTDOWN_SELECTOR).first
    text: str | None = None
    expired = False

    try:
        if countdown.count() and countdown.is_visible():
            text = countdown.inner_text(timeout=2000).strip()
            expired = "expirado" in text.lower()
    except PlaywrightTimeout:
        pass

    return MfaStatus(countdown_text=text, expired=expired)


def _resend_mfa_code(page: Page) -> None:
    if not _click_first(page, MFA_RESEND_SELECTORS):
        raise RuntimeError("No se encontró el botón «Reenviar código».")

    page.wait_for_timeout(2500)
    notify_webhook(
        "hsec.mfa.resent",
        {"url": page.url, "countdown": _read_mfa_status(page).countdown_text},
    )


def _submit_mfa_code(page: Page, code: str) -> None:
    mfa_input = _first_visible(page, MFA_INPUT_SELECTORS, timeout_ms=15000)
    if mfa_input is None:
        raise RuntimeError("No se encontró el campo para el código de verificación.")

    mfa_input.fill("")
    mfa_input.fill(code)
    page.wait_for_timeout(300)

    if not _click_first(page, MFA_SUBMIT_SELECTORS):
        mfa_input.press("Enter")

    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(2500)


def _mfa_still_blocking(page: Page) -> bool:
    if not _page_has_mfa_prompt(page):
        return False
    status = _read_mfa_status(page)
    return status.expired or _first_visible(page, MFA_INPUT_SELECTORS, timeout_ms=1500) is not None


def _wait_for_mfa_action(
    *,
    since: datetime,
    used_codes: set[str],
) -> MfaAction:
    """Prioriza botones del modal; el correo IMAP se consulta entre esperas cortas."""
    ui_poll_sec = 1

    while True:
        try:
            return mfa_coordinator.wait_for_action(timeout_sec=ui_poll_sec)
        except TimeoutError:
            pass

        if is_mfa_email_configured():
            code = poll_mfa_code_once(since=since, used_codes=used_codes)
            if code:
                used_codes.add(code)
                return MfaAction(type=MfaActionType.CODE, code=code)


def _handle_mfa_if_needed(page: Page) -> bool:
    if not _page_has_mfa_prompt(page):
        return False

    notify_webhook(
        "hsec.mfa.required",
        {
            "url": page.url,
            "message": "Se requiere código de verificación enviado al correo.",
            "countdown": _read_mfa_status(page).countdown_text,
        },
    )

    mfa_coordinator.begin_session(
        resend_fn=lambda: _resend_mfa_code(page),
        status_fn=lambda: _read_mfa_status(page),
    )

    prompt_shown = False
    mfa_used = False
    expired_announced = False
    mfa_since = datetime.now(timezone.utc)
    used_codes: set[str] = set()

    try:
        while _page_has_mfa_prompt(page) or _mfa_still_blocking(page):
            status = _read_mfa_status(page)
            mfa_coordinator.update_status(status)

            if status.expired:
                if not expired_announced:
                    notify_webhook(
                        "hsec.mfa.expired",
                        {"url": page.url, "countdown": status.countdown_text},
                    )
                    expired_announced = True
            else:
                expired_announced = False

            if not prompt_shown:
                if is_mfa_email_configured():
                    msg = (
                        "Leyendo el código desde el correo configurado. "
                        "También puedes ingresarlo manualmente."
                    )
                else:
                    msg = "Revisa tu correo e ingresa el código de 6 caracteres."
                if status.countdown_text:
                    msg += f" Tiempo: {status.countdown_text}."
                if status.expired:
                    msg += " El código expiró; usa «Reenviar código»."
                mfa_coordinator.open_prompt(msg)
                prompt_shown = True

            action = _wait_for_mfa_action(since=mfa_since, used_codes=used_codes)

            if action.type == MfaActionType.CANCEL:
                raise RuntimeError(
                    "Inicio de sesión cancelado. Pulsa «Iniciar sesión» para intentar de nuevo."
                )

            if action.type == MfaActionType.RESEND:
                expired_announced = False
                mfa_since = datetime.now(timezone.utc)
                time.sleep(2)
                status = _read_mfa_status(page)
                mfa_coordinator.update_status(status)
                prompt_shown = True
                resend_msg = "Nuevo código enviado. "
                if is_mfa_email_configured():
                    resend_msg += "Buscando en el buzón..."
                else:
                    resend_msg += "Ingresa los 6 caracteres."
                mfa_coordinator.open_prompt(
                    resend_msg
                    + (
                        f" Tiempo: {status.countdown_text}."
                        if status.countdown_text
                        else ""
                    )
                )
                continue

            _submit_mfa_code(page, action.code)
            mfa_used = True

            if not _page_has_mfa_prompt(page) and not _mfa_still_blocking(page):
                break

            status = _read_mfa_status(page)
            if status.expired:
                mfa_coordinator.notify_error(
                    "El código expiró. Pulsa «Reenviar código» y usa el nuevo."
                )
                notify_webhook(
                    "hsec.mfa.expired",
                    {"url": page.url, "after_submit": True},
                )
            else:
                mfa_coordinator.notify_error(
                    "Código incorrecto o aún en validación. Revisa e intenta de nuevo."
                )
    finally:
        mfa_coordinator.end_session()

    return mfa_used


def _wait_for_authenticated(page: Page, timeout_ms: int = 60000) -> None:
    try:
        page.wait_for_function(
            """() => {
                const href = window.location.href.toLowerCase();
                if (href.includes('#/dashboard') || href.includes('/dashboard')) return true;
                const text = document.body?.innerText?.toLowerCase() || '';
                if (text.includes('dashboard') && !text.includes('sign in')) return true;
                return false;
            }""",
            timeout=timeout_ms,
        )
    except PlaywrightTimeout:
        if _page_has_mfa_prompt(page):
            return
        if not _is_dashboard(page):
            raise RuntimeError(
                "No se alcanzó el dashboard tras el login. Revisa credenciales o selectores."
            )


def _create_context(playwright):
    kwargs: dict = {}
    if has_saved_session():
        kwargs["storage_state"] = str(session_path())

    kwargs["user_agent"] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    kwargs["viewport"] = {"width": 1366, "height": 768}
    kwargs["locale"] = "es-PE"
    kwargs["timezone_id"] = "America/Lima"
    kwargs["ignore_https_errors"] = True

    browser = playwright.chromium.launch(
        headless=PLAYWRIGHT_HEADLESS,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
        ],
    )
    context = browser.new_context(**kwargs)
    context.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return browser, context


def _run_login_flow(page: Page, used_saved_session: bool) -> LoginResult:
    page.goto(HSEC_DASHBOARD_URL, wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(2000)

    if _is_dashboard(page) and not _page_has_mfa_prompt(page):
        save_storage_state(page.context)
        notify_webhook(
            "hsec.auth.success",
            {"used_saved_session": used_saved_session, "mfa": False},
        )
        return LoginResult(
            success=True,
            message="Sesión activa en el dashboard.",
            used_saved_session=used_saved_session,
        )

    needs_credentials = _first_visible(page, USERNAME_SELECTORS, timeout_ms=3000) is not None
    if needs_credentials:
        _fill_credentials(page)

    mfa_used = _handle_mfa_if_needed(page)

    _wait_for_authenticated(page)

    if not _is_dashboard(page) and not _page_has_mfa_prompt(page):
        page.wait_for_timeout(3000)

    save_storage_state(page.context)
    notify_webhook(
        "hsec.auth.success",
        {"used_saved_session": used_saved_session, "mfa": mfa_used},
    )

    return LoginResult(
        success=True,
        message="Inicio de sesión correcto. Sesión guardada.",
        used_saved_session=used_saved_session,
        mfa_required=mfa_used,
    )


def login_hsec() -> LoginResult:
    """Inicia sesión en HSEC Web y persiste cookies/localStorage para reutilizar."""
    used_saved = has_saved_session()

    with sync_playwright() as playwright:
        browser = None
        try:
            browser, context = _create_context(playwright)
            page = context.new_page()
            result = _run_login_flow(page, used_saved_session=used_saved)
            return result
        except Exception as ex:
            logger.exception("Error en login HSEC")
            notify_webhook(
                "hsec.auth.failed",
                {"error": str(ex), "used_saved_session": used_saved},
            )
            raise
        finally:
            if browser:
                browser.close()


def verify_session() -> LoginResult:
    """Comprueba si la sesión guardada sigue válida."""
    return login_hsec()
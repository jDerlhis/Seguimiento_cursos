"""
Inicio de sesión HSEC con persistencia en hsec_sessions.
Port de backend/scripts/hsec_login.ts
"""

from infra.config.settings import HSEC_DASHBOARD_URL
from app.common.modules.hsec.browser import hsec_browser, new_context
from app.common.modules.hsec.login_page import (
    fill_credentials,
    has_mfa_prompt,
    is_dashboard,
    is_login_page,
    submit_mfa_code,
)
from app.common.modules.hsec.persistence import (
    load_active_session,
    load_credentials,
    mark_session_error,
    save_session,
)
from app.common.modules.hsec.playwright_utils import first_visible_optional
from app.common.modules.hsec.selectors import USERNAME_SELECTORS
from app.common.modules.hsec.types import LoginResult
from shared.logger import get_logger

logger = get_logger(__name__)


def login_hsec(tenant_id: str, mfa_code: str = "") -> LoginResult:
    creds = load_credentials(tenant_id)
    if not creds:
        return LoginResult(
            success=False,
            message="No hay credenciales HSEC activas para este tenant.",
            used_saved_session=False,
            mfa_required=False,
        )

    mfa_was_used = False

    try:
        with hsec_browser(headless=True) as browser:
            saved = load_active_session(tenant_id)
            if saved:
                ctx = new_context(browser, storage_state=saved["state"])
                page = ctx.new_page()
                page.goto(HSEC_DASHBOARD_URL, wait_until="domcontentloaded", timeout=60_000)
                page.wait_for_timeout(2_000)

                if is_dashboard(page) and not has_mfa_prompt(page):
                    ctx.close()
                    return LoginResult(
                        success=True,
                        message="Sesión reutilizada correctamente.",
                        used_saved_session=True,
                        mfa_required=False,
                        session_id=saved["session_id"],
                    )
                ctx.close()

            ctx = new_context(browser, hide_webdriver=True)
            page = ctx.new_page()
            page.goto(HSEC_DASHBOARD_URL, wait_until="domcontentloaded", timeout=120_000)
            page.wait_for_timeout(2_000)

            if is_dashboard(page) and not has_mfa_prompt(page):
                state = ctx.storage_state()
                session_id = save_session(tenant_id, creds.id, state)
                ctx.close()
                return LoginResult(
                    success=True,
                    message="Sesión iniciada sin credenciales.",
                    used_saved_session=False,
                    mfa_required=False,
                    session_id=session_id,
                )

            if is_login_page(page) or first_visible_optional(page, USERNAME_SELECTORS, 3_000):
                fill_credentials(page, creds)

            if has_mfa_prompt(page):
                if not mfa_code:
                    ctx.close()
                    return LoginResult(
                        success=False,
                        message="Se requiere código MFA pero no fue proporcionado.",
                        used_saved_session=False,
                        mfa_required=True,
                    )
                submit_mfa_code(page, mfa_code)
                mfa_was_used = True

            try:
                page.wait_for_url("**#/dashboard**", timeout=20_000)
            except Exception:
                if not is_dashboard(page):
                    raise RuntimeError(
                        f"No se alcanzó el dashboard. URL actual: {page.url()}"
                    )

            state = ctx.storage_state()
            session_id = save_session(tenant_id, creds.id, state)
            ctx.close()

            return LoginResult(
                success=True,
                message="Inicio de sesión correcto. Sesión guardada.",
                used_saved_session=False,
                mfa_required=mfa_was_used,
                session_id=session_id,
            )

    except Exception as ex:
        msg = str(ex)
        logger.error("login_hsec: %s", msg)
        mark_session_error(tenant_id, msg)
        raise

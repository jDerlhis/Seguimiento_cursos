import re

from playwright.sync_api import Page

from app.common.modules.hsec.playwright_utils import (
    click_first_if_visible,
    first_visible,
    first_visible_optional,
)
from app.common.modules.hsec.selectors import (
    MFA_BODY_PATTERNS,
    MFA_INPUT_SELECTORS,
    MFA_SUBMIT_SELECTORS,
    PASSWORD_SELECTORS,
    SUBMIT_SELECTORS,
    USERNAME_SELECTORS,
)
from app.common.modules.hsec.types import HsecCredential


def is_login_page(page: Page) -> bool:
    url = page.url.lower()
    return "#/login" in url or "/login" in url


def is_dashboard(page: Page) -> bool:
    url = page.url.lower()
    return "#/dashboard" in url or "/dashboard" in url


def has_mfa_prompt(page: Page) -> bool:
    try:
        body = page.locator("body").inner_text(timeout=5_000)
        if any(re.search(p, body, re.IGNORECASE) for p in MFA_BODY_PATTERNS):
            return True
    except Exception:
        pass
    return first_visible_optional(page, MFA_INPUT_SELECTORS, 2_000) is not None


def fill_credentials(page: Page, creds: HsecCredential) -> None:
    user_input = first_visible(page, USERNAME_SELECTORS, 15_000)
    user_input.fill(creds.username)
    page.wait_for_timeout(300)

    pass_input = first_visible(page, PASSWORD_SELECTORS, 10_000)
    pass_input.fill(creds.password)
    page.wait_for_timeout(300)

    if not click_first_if_visible(page, SUBMIT_SELECTORS):
        pass_input.press("Enter")

    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(2_000)


def submit_mfa_code(page: Page, code: str) -> None:
    mfa_input = first_visible(page, MFA_INPUT_SELECTORS, 15_000)
    mfa_input.fill("")
    mfa_input.fill(code)
    page.wait_for_timeout(300)

    if not click_first_if_visible(page, MFA_SUBMIT_SELECTORS):
        mfa_input.press("Enter")

    page.wait_for_load_state("networkidle")

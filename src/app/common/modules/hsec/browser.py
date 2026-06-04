from contextlib import contextmanager
from typing import Iterator

from playwright.sync_api import Browser, BrowserContext, sync_playwright

from infra.config.settings import PLAYWRIGHT_HEADLESS

BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

CONTEXT_OPTIONS = {
    "user_agent": USER_AGENT,
    "locale": "es-PE",
    "timezone_id": "America/Lima",
    "ignore_https_errors": True,
}


@contextmanager
def hsec_browser(*, headless: bool | None = None) -> Iterator[Browser]:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=PLAYWRIGHT_HEADLESS if headless is None else headless,
            args=BROWSER_ARGS,
        )
        try:
            yield browser
        finally:
            browser.close()


def new_context(
    browser: Browser,
    *,
    storage_state: str | dict | None = None,
    hide_webdriver: bool = False,
) -> BrowserContext:
    kwargs = dict(CONTEXT_OPTIONS)
    if storage_state is not None:
        kwargs["storage_state"] = storage_state
    ctx = browser.new_context(**kwargs)
    if hide_webdriver:
        ctx.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
    return ctx

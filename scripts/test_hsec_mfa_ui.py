"""Verifica lectura de #countdown y botón Reenviar código tras login."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright

from infra.config.settings import HSEC_DASHBOARD_URL, HSEC_PASSWORD, HSEC_USERNAME
from infra.scraping import hsec_scraper


def main() -> int:
    with sync_playwright() as p:
        page = p.chromium.launch(headless=True).new_page()
        page.goto(HSEC_DASHBOARD_URL, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(2000)

        u = hsec_scraper._first_visible(page, hsec_scraper.USERNAME_SELECTORS)
        pw = hsec_scraper._first_visible(page, hsec_scraper.PASSWORD_SELECTORS)
        u.fill(HSEC_USERNAME)
        pw.fill(HSEC_PASSWORD)
        hsec_scraper._click_first(page, hsec_scraper.SUBMIT_SELECTORS)
        page.wait_for_timeout(5000)

        status = hsec_scraper._read_mfa_status(page)
        resend = page.locator("button:has-text('Reenviar código')").first

        print("countdown:", status.countdown_text)
        print("expired:", status.expired)
        print("resend visible:", resend.is_visible() if resend.count() else False)

        ok = bool(status.countdown_text) and resend.count() > 0
        print("OK" if ok else "FALLO")
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

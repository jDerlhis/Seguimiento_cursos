"""Prueba automatizada: carga login, credenciales y detección MFA (sin esperar código)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright

from infra.config.settings import HSEC_DASHBOARD_URL, HSEC_PASSWORD, HSEC_USERNAME
from infra.scraping import hsec_scraper

OUT = Path(__file__).resolve().parents[1] / "test" / "artifacts"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    assert HSEC_USERNAME and HSEC_PASSWORD, "Faltan credenciales en .env"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(HSEC_DASHBOARD_URL, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(2000)

        assert hsec_scraper._is_login_page(page), f"Se esperaba login, URL={page.url}"

        user = hsec_scraper._first_visible(page, hsec_scraper.USERNAME_SELECTORS)
        pwd = hsec_scraper._first_visible(page, hsec_scraper.PASSWORD_SELECTORS)
        assert user and pwd, "No se encontraron campos Usuario/Password"

        user.fill(HSEC_USERNAME)
        pwd.fill(HSEC_PASSWORD)
        assert hsec_scraper._click_first(page, hsec_scraper.SUBMIT_SELECTORS), "Botón Ingresar no encontrado"

        page.wait_for_timeout(5000)
        page.screenshot(path=str(OUT / "after_login_click.png"), full_page=True)

        mfa = hsec_scraper._page_has_mfa_prompt(page)
        dashboard = hsec_scraper._is_dashboard(page)

        print("URL tras login:", page.url)
        print("MFA detectado:", mfa)
        print("Dashboard:", dashboard)
        print("Captura:", OUT / "after_login_click.png")

        browser.close()

    if mfa:
        print("\nRESULTADO: Login OK — pendiente código MFA (flujo correcto).")
        return 0
    if dashboard:
        print("\nRESULTADO: Login OK — dashboard sin MFA.")
        return 0

    print("\nRESULTADO: Estado inesperado tras credenciales.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

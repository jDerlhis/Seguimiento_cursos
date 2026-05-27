"""Explora login Roundcube en cPanel (puerto 2096)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright

from infra.config.settings import MFA_IMAP_PASSWORD, MFA_IMAP_USER

URLS = (
    "https://sermull.com:2096/3rdparty/roundcube/",
    "https://sermull.com:2096/webmail",
    "https://sermull.com:2096/",
)


def main() -> int:
    out = Path(__file__).resolve().parents[1] / "test" / "artifacts"
    out.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(ignore_https_errors=True)

        for url in URLS:
            print("---", url)
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(3000)
                shot = out / f"rc_{URLS.index(url)}.png"
                page.screenshot(path=str(shot), full_page=True)
                print("URL final:", page.url)
                print("Title:", page.title())
                for sel in ("#rcmloginuser", "input[name='_user']", "input[type='email']"):
                    loc = page.locator(sel).first
                    if loc.count():
                        print("User field:", sel)
                        break
            except Exception as ex:
                print("Error:", ex)

        user = page.locator("input[name='_user'], #rcmloginuser").first
        pwd = page.locator("input[name='_pass'], #rcmloginpwd").first
        if user.count() and pwd.count():
            user.fill(MFA_IMAP_USER)
            pwd.fill(MFA_IMAP_PASSWORD)
            page.locator("button[type='submit'], #rcmloginsubmit, input[type='submit']").first.click()
            page.wait_for_timeout(5000)
            page.screenshot(path=str(out / "after_login.png"), full_page=True)
            print("Post-login URL:", page.url)
            print("Body snippet:", page.locator("body").inner_text()[:500])

        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

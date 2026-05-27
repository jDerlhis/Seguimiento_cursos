"""Explora la página de login HSEC y guarda captura + selectores detectados."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright

from infra.config.settings import HSEC_DASHBOARD_URL, HSEC_PASSWORD, HSEC_USERNAME

OUT = Path(__file__).resolve().parents[1] / "test" / "artifacts"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(HSEC_DASHBOARD_URL, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(5000)

        print("URL:", page.url)
        print("Title:", page.title())

        inputs = page.locator("input").all()
        print(f"\nInputs visibles ({len(inputs)}):")
        for i, inp in enumerate(inputs[:20]):
            try:
                visible = inp.is_visible()
            except Exception:
                visible = False
            if not visible:
                continue
            print(
                f"  [{i}] type={inp.get_attribute('type')!r} "
                f"name={inp.get_attribute('name')!r} "
                f"id={inp.get_attribute('id')!r} "
                f"placeholder={inp.get_attribute('placeholder')!r}"
            )

        buttons = page.locator("button").all()
        print(f"\nBotones visibles (max 15 de {len(buttons)}):")
        for i, btn in enumerate(buttons[:15]):
            try:
                if not btn.is_visible():
                    continue
                print(f"  [{i}] text={btn.inner_text()[:60]!r}")
            except Exception:
                pass

        snippet = page.locator("body").inner_text(timeout=10000)[:800]
        print("\nTexto body (primeros 800 chars):\n", snippet.replace("\n", " ")[:800])

        shot = OUT / "hsec_probe.png"
        page.screenshot(path=str(shot), full_page=True)
        print(f"\nCaptura: {shot}")
        browser.close()


if __name__ == "__main__":
    main()

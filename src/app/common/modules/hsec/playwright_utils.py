from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeout


def first_visible(
    page: Page,
    selectors: list[str],
    timeout_ms: int = 5_000,
) -> Locator:
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            loc.wait_for(state="visible", timeout=timeout_ms)
            return loc
        except PlaywrightTimeout:
            continue
    raise RuntimeError(f"Ningún selector visible: {', '.join(selectors)}")


def first_visible_optional(
    page: Page,
    selectors: list[str],
    timeout_ms: int = 5_000,
) -> Locator | None:
    try:
        return first_visible(page, selectors, timeout_ms)
    except RuntimeError:
        return None


def click_first(
    page: Page,
    selectors: list[str],
    timeout_ms: int = 5_000,
) -> None:
    first_visible(page, selectors, timeout_ms).click()


def click_first_if_visible(page: Page, selectors: list[str]) -> bool:
    for sel in selectors:
        loc = page.locator(sel).first
        if loc.count() > 0 and loc.is_visible():
            loc.click()
            return True
    return False

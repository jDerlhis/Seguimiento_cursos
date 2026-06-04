from playwright.sync_api import Page

from app.common.modules.hsec.playwright_utils import click_first, first_visible
from app.common.modules.hsec.selectors import (
    BUSCAR_SELECTORS,
    DNI_INPUT_SELECTORS,
    OPEN_MODAL_SELECTORS,
    REPORTE_URL,
    RESULT_ROW_SELECTOR,
    SELECCIONAR_SELECTORS,
)
from app.common.modules.hsec.types import ScrapedPerson


def scrape_person_by_dni(page: Page, dni: str) -> ScrapedPerson | None:
    """
    Busca una persona por DNI en ReportePersonalCapacitado.
    Port de backend/scripts/people_scraper.ts
    """
    page.goto(REPORTE_URL, wait_until="domcontentloaded", timeout=90_000)
    page.wait_for_timeout(2_000)

    click_first(page, OPEN_MODAL_SELECTORS)
    page.wait_for_selector(".k-dialog, [role='dialog']", timeout=10_000)
    page.wait_for_timeout(1_000)

    campo_dni = first_visible(page, DNI_INPUT_SELECTORS)
    campo_dni.fill("")
    campo_dni.fill(dni)
    click_first(page, BUSCAR_SELECTORS)
    page.wait_for_timeout(3_000)

    fila = page.locator(RESULT_ROW_SELECTOR).first
    if fila.count() == 0 or not fila.is_visible():
        cancelar = page.locator("button:has-text('Cancelar')").first
        if cancelar.is_visible():
            cancelar.click()
        return None

    celdas = fila.locator("td")
    persona = ScrapedPerson(
        tipo_documento=celdas.nth(0).inner_text().strip(),
        nro_documento=celdas.nth(1).inner_text().strip(),
        nombres=celdas.nth(2).inner_text().strip(),
        apellidos=celdas.nth(3).inner_text().strip(),
        empresa=celdas.nth(4).inner_text().strip(),
    )

    try:
        click_first(page, SELECCIONAR_SELECTORS)
        page.wait_for_timeout(1_500)
    except RuntimeError:
        pass

    return persona


def select_person_in_modal(page: Page, dni: str) -> bool:
    """Abre modal, busca DNI y pulsa Seleccionar. Retorna False si no hay fila."""
    page.goto(REPORTE_URL, wait_until="domcontentloaded", timeout=90_000)
    page.wait_for_timeout(2_000)
    click_first(page, OPEN_MODAL_SELECTORS)
    page.wait_for_selector(".k-dialog, [role='dialog']", timeout=10_000)
    page.wait_for_timeout(1_000)

    campo_dni = first_visible(page, DNI_INPUT_SELECTORS)
    campo_dni.fill("")
    campo_dni.fill(dni)
    click_first(page, BUSCAR_SELECTORS)
    page.wait_for_timeout(3_000)

    fila = page.locator(RESULT_ROW_SELECTOR).first
    if fila.count() == 0 or not fila.is_visible():
        cancelar = page.locator("button:has-text('Cancelar')").first
        if cancelar.is_visible():
            cancelar.click()
        return False

    try:
        click_first(page, SELECCIONAR_SELECTORS)
        page.wait_for_timeout(1_500)
    except RuntimeError:
        pass
    return True

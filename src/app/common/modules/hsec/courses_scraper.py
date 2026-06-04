import re
import unicodedata

from playwright.sync_api import Page

from app.common.modules.hsec.people_scraper import select_person_in_modal
from app.common.modules.hsec.playwright_utils import click_first
from app.common.modules.hsec.selectors import (
    EXPECTED_COURSE_HEADERS,
    REPORT_ROW_SELECTOR,
    VER_REPORTE_SELECTORS,
)
from app.common.modules.hsec.types import ScrapedCourse


def _normalize_header(text: str) -> str:
    t = text.strip().lower()
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"n[º°]", "n", t)
    return t


def _map_headers(cells: list[str]) -> dict[str, int]:
    return {_normalize_header(c): i for i, c in enumerate(cells)}


def _cell(cells: list[str], col: dict[str, int], name: str) -> str | None:
    idx = col.get(name)
    if idx is None or idx >= len(cells):
        return None
    val = cells[idx].strip()
    return val or None


def _extract_from_frames(page: Page, dni: str) -> list[ScrapedCourse]:
    cursos: list[ScrapedCourse] = []

    for frame in page.frames:
        try:
            filas = frame.locator(REPORT_ROW_SELECTOR).all()
            if len(filas) < 2:
                continue

            col: dict[str, int] | None = None

            for fila in filas:
                tags = fila.locator("td, th").all()
                celdas = [td.inner_text() for td in tags]
                if not celdas:
                    continue

                if col is None:
                    mapa = _map_headers(celdas)
                    hits = sum(1 for h in EXPECTED_COURSE_HEADERS if h in mapa)
                    if hits >= 3:
                        col = mapa
                    continue

                tema = _cell(celdas, col, "tema")
                if not tema:
                    continue

                cursos.append(
                    ScrapedCourse(
                        nro_documento=dni,
                        fecha=_cell(celdas, col, "fecha"),
                        duracion=_cell(celdas, col, "duracion"),
                        tema=tema,
                        area=_cell(celdas, col, "area"),
                        tipo=_cell(celdas, col, "tipo"),
                        nota=_cell(celdas, col, "nota"),
                        estado=_cell(celdas, col, "estado"),
                        vencimiento=_cell(celdas, col, "vencimiento"),
                    )
                )

            if cursos:
                break
        except Exception:
            continue

    return cursos


def scrape_courses_by_dni(page: Page, dni: str) -> list[ScrapedCourse]:
    """
    Persona + Ver reporte + extracción de tabla en iframes.
    Port de backend/scripts/cursos_scraper.ts
    """
    if not select_person_in_modal(page, dni):
        return []

    click_first(page, VER_REPORTE_SELECTORS)
    page.wait_for_timeout(5_000)

    return _extract_from_frames(page, dni)

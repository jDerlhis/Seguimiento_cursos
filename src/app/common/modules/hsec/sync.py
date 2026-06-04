"""
Sincronización persona + cursos por DNI.
Port de backend/scripts/sync_hsec.ts
"""

from playwright.sync_api import Page

from app.common.modules.hsec.browser import hsec_browser, new_context
from app.common.modules.hsec.courses_scraper import scrape_courses_by_dni
from app.common.modules.hsec.people_scraper import scrape_person_by_dni
from app.common.modules.hsec.persistence import (
    load_active_session,
    upsert_company,
    upsert_courses,
    upsert_person,
)
from app.common.modules.hsec.types import SyncResult
from shared.logger import get_logger

logger = get_logger(__name__)


def _sync_one_dni(page: Page, tenant_id: str, dni: str) -> SyncResult:
    try:
        logger.info("Scraping persona DNI=%s", dni)
        persona = scrape_person_by_dni(page, dni)
        if not persona:
            return SyncResult(
                dni=dni,
                persona_upserted=False,
                cursos_upserted=0,
                error="DNI no encontrado en el portal",
            )

        company_id = (
            upsert_company(tenant_id, persona.empresa) if persona.empresa else None
        )
        person_id = upsert_person(tenant_id, persona, company_id)
        if not person_id:
            return SyncResult(
                dni=dni,
                persona_upserted=False,
                cursos_upserted=0,
                error="Error guardando persona en DB",
            )

        logger.info("Scraping cursos DNI=%s", dni)
        cursos = scrape_courses_by_dni(page, dni)
        count = upsert_courses(tenant_id, person_id, cursos)

        return SyncResult(
            dni=dni,
            persona_upserted=True,
            cursos_upserted=count,
        )
    except Exception as ex:
        return SyncResult(
            dni=dni,
            persona_upserted=False,
            cursos_upserted=0,
            error=str(ex),
        )


def _resolve_storage_state(tenant_id: str) -> dict:
    session = load_active_session(tenant_id)
    if session:
        return session["state"]

    raise RuntimeError(
        "No hay sesión HSEC activa en Supabase. "
        "Inicia sesión en HSEC Web desde la app."
    )


def sync_hsec(tenant_id: str, dnis: list[str]) -> list[SyncResult]:
    storage_state = _resolve_storage_state(tenant_id)
    results: list[SyncResult] = []

    with hsec_browser(headless=True) as browser:
        ctx = new_context(browser, storage_state=storage_state)
        page = ctx.new_page()

        for dni in dnis:
            logger.info("[sync] DNI=%s", dni)
            result = _sync_one_dni(page, tenant_id, dni)
            results.append(result)
            ok = not result.error
            logger.info(
                "%s persona=%s cursos=%s%s",
                "✓" if ok else "✗",
                result.persona_upserted,
                result.cursos_upserted,
                f" error={result.error}" if result.error else "",
            )

        ctx.close()

    return results

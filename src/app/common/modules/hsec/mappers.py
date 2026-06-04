from datetime import datetime, timezone

from data.entities.hsec_course import HsecCourse
from data.entities.hsec_person import HsecPerson
from app.common.modules.hsec.types import ScrapedCourse, ScrapedPerson


def scraped_person_to_entity(
    scraped: ScrapedPerson,
    *,
    tenant_id: str | None = None,
    company_id: str | None = None,
) -> HsecPerson:
    return HsecPerson(
        tenant_id=tenant_id,
        tipo_documento=scraped.tipo_documento or "DNI",
        nro_documento=scraped.nro_documento,
        nombres=scraped.nombres,
        apellidos=scraped.apellidos,
        empresa=scraped.empresa or None,
        company_id=company_id,
        last_synced_at=datetime.now(timezone.utc).isoformat(),
    )


def scraped_course_to_entity(
    scraped: ScrapedCourse,
    *,
    tenant_id: str,
    person_id: str,
) -> HsecCourse:
    return HsecCourse(
        tenant_id=tenant_id,
        person_id=person_id,
        fecha=scraped.fecha,
        duracion=scraped.duracion,
        tema=scraped.tema,
        area=scraped.area,
        tipo=scraped.tipo,
        nota=scraped.nota,
        estado=scraped.estado,
        vencimiento=scraped.vencimiento,
        last_synced_at=datetime.now(timezone.utc).isoformat(),
    )

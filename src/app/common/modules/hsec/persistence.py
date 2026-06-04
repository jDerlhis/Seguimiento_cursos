"""Persistencia Supabase — lógica de backend/scripts/sync_hsec.ts y hsec_login.ts."""

from datetime import datetime, timezone
from typing import Any

from data import schema
from app.common.modules.hsec.types import HsecCredential, ScrapedCourse, ScrapedPerson
from infra.supabase.client import get_client
from shared.logger import get_logger

logger = get_logger(__name__)


def load_active_session(tenant_id: str) -> dict[str, Any] | None:
    response = (
        get_client()
        .table(schema.HSEC_SESSIONS)
        .select("id, storage_state")
        .eq("tenant_id", tenant_id)
        .eq("is_active", True)
        .order("updated_at", desc=True)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    if not rows:
        return None
    return {"session_id": rows[0]["id"], "state": rows[0]["storage_state"]}


def load_credentials(tenant_id: str) -> HsecCredential | None:
    response = (
        get_client()
        .table(schema.HSEC_CREDENTIALS)
        .select("id, username, vault_secret_id")
        .eq("tenant_id", tenant_id)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    if not rows:
        return None

    row = rows[0]
    try:
        secret = (
            get_client()
            .schema("vault")
            .from_("decrypted_secrets")
            .select("decrypted_secret")
            .eq("id", row["vault_secret_id"])
            .limit(1)
            .execute()
        )
    except Exception as ex:
        logger.warning("No se pudo leer vault.decrypted_secrets: %s", ex)
        return None
    secret_rows = secret.data or []
    password = secret_rows[0].get("decrypted_secret") if secret_rows else None
    if not password:
        return None

    return HsecCredential(
        id=row["id"],
        username=row["username"],
        password=password,
    )


def save_session(
    tenant_id: str,
    credential_id: str,
    storage_state: dict,
) -> str:
    client = get_client()
    client.table(schema.HSEC_SESSIONS).update({"is_active": False}).eq(
        "tenant_id", tenant_id
    ).eq("is_active", True).execute()

    response = (
        client.table(schema.HSEC_SESSIONS)
        .insert(
            {
                "tenant_id": tenant_id,
                "credential_id": credential_id,
                "storage_state": storage_state,
                "is_active": True,
                "last_verified_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .select("id")
        .execute()
    )
    rows = response.data or []
    if not rows:
        raise RuntimeError("Error guardando sesión HSEC en Supabase")
    return rows[0]["id"]


def mark_session_error(tenant_id: str, error_msg: str) -> None:
    get_client().table(schema.HSEC_SESSIONS).update(
        {"is_active": False, "error": error_msg}
    ).eq("tenant_id", tenant_id).eq("is_active", True).execute()


def upsert_company(tenant_id: str, empresa: str) -> str | None:
    response = get_client().rpc(
        "upsert_company_for_tenant",
        {"p_tenant_id": tenant_id, "p_name": empresa},
    ).execute()
    if response.data is None:
        logger.warning("upsert_company_for_tenant sin resultado para %s", empresa)
        return None
    return str(response.data)


def upsert_person(
    tenant_id: str,
    persona: ScrapedPerson,
    company_id: str | None,
) -> str | None:
    now = datetime.now(timezone.utc).isoformat()
    response = (
        get_client()
        .table(schema.HSEC_PEOPLE)
        .upsert(
            {
                "tenant_id": tenant_id,
                "tipo_documento": persona.tipo_documento,
                "nro_documento": persona.nro_documento,
                "nombres": persona.nombres,
                "apellidos": persona.apellidos,
                "empresa": persona.empresa or None,
                "company_id": company_id,
                "last_synced_at": now,
            },
            on_conflict="tenant_id,nro_documento",
        )
        .select("id")
        .execute()
    )
    rows = response.data or []
    if not rows:
        logger.warning("upsert_persona falló para DNI %s", persona.nro_documento)
        return None
    return rows[0]["id"]


def upsert_courses(
    tenant_id: str,
    person_id: str,
    cursos: list[ScrapedCourse],
) -> int:
    if not cursos:
        return 0

    now = datetime.now(timezone.utc).isoformat()
    rows = [
        {
            "tenant_id": tenant_id,
            "person_id": person_id,
            "fecha": c.fecha,
            "duracion": c.duracion,
            "tema": c.tema,
            "area": c.area,
            "tipo": c.tipo,
            "nota": c.nota,
            "estado": c.estado,
            "vencimiento": c.vencimiento,
            "last_synced_at": now,
        }
        for c in cursos
    ]

    response = (
        get_client()
        .table(schema.HSEC_COURSES)
        .upsert(rows, on_conflict="tenant_id,person_id,tema,fecha", count="exact")
        .execute()
    )
    if response.count is not None:
        return response.count
    return len(cursos)

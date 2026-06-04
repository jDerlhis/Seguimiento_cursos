from dataclasses import dataclass

from data.entities._base import str_timestamp


@dataclass
class HsecPerson:
    """public.hsec_people — 20260530000006, company_id en 009."""

    tipo_documento: str
    nro_documento: str
    nombres: str
    apellidos: str
    id: str | None = None
    tenant_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    last_synced_at: str | None = None
    empresa: str | None = None
    company_id: str | None = None

    @classmethod
    def from_record(cls, record: dict) -> "HsecPerson":
        return cls(
            id=record.get("id"),
            tenant_id=record.get("tenant_id"),
            created_at=str_timestamp(record.get("created_at")),
            updated_at=str_timestamp(record.get("updated_at")),
            last_synced_at=str_timestamp(record.get("last_synced_at")),
            tipo_documento=record.get("tipo_documento") or "DNI",
            nro_documento=record.get("nro_documento") or "",
            nombres=record.get("nombres") or "",
            apellidos=record.get("apellidos") or "",
            empresa=record.get("empresa"),
            company_id=record.get("company_id"),
        )

    def to_record(self) -> dict:
        row = {
            "tipo_documento": self.tipo_documento,
            "nro_documento": self.nro_documento,
            "nombres": self.nombres,
            "apellidos": self.apellidos,
            "empresa": self.empresa,
            "company_id": self.company_id,
            "last_synced_at": self.last_synced_at,
        }
        if self.tenant_id is not None:
            row["tenant_id"] = self.tenant_id
        return row

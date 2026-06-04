from dataclasses import dataclass

from data.entities._base import str_timestamp


@dataclass
class HsecCourse:
    """public.hsec_courses — 20260530000007."""

    tema: str
    id: str | None = None
    tenant_id: str | None = None
    person_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    last_synced_at: str | None = None
    fecha: str | None = None
    duracion: str | None = None
    area: str | None = None
    tipo: str | None = None
    nota: str | None = None
    estado: str | None = None
    vencimiento: str | None = None

    @classmethod
    def from_record(cls, record: dict) -> "HsecCourse":
        return cls(
            id=record.get("id"),
            tenant_id=record.get("tenant_id"),
            person_id=record.get("person_id"),
            created_at=str_timestamp(record.get("created_at")),
            updated_at=str_timestamp(record.get("updated_at")),
            last_synced_at=str_timestamp(record.get("last_synced_at")),
            fecha=record.get("fecha"),
            duracion=record.get("duracion"),
            tema=record.get("tema") or "",
            area=record.get("area"),
            tipo=record.get("tipo"),
            nota=record.get("nota"),
            estado=record.get("estado"),
            vencimiento=record.get("vencimiento"),
        )

    def to_record(self) -> dict:
        row = {
            "fecha": self.fecha,
            "duracion": self.duracion,
            "tema": self.tema,
            "area": self.area,
            "tipo": self.tipo,
            "nota": self.nota,
            "estado": self.estado,
            "vencimiento": self.vencimiento,
            "last_synced_at": self.last_synced_at,
        }
        if self.tenant_id is not None:
            row["tenant_id"] = self.tenant_id
        if self.person_id is not None:
            row["person_id"] = self.person_id
        return row

from dataclasses import dataclass

from data.entities._base import str_timestamp


@dataclass
class Company:
    """public.companies — 20260530000009."""

    tenant_id: str
    name: str
    id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    is_active: bool = True

    @classmethod
    def from_record(cls, record: dict) -> "Company":
        return cls(
            id=record.get("id"),
            tenant_id=record.get("tenant_id") or "",
            name=record.get("name") or "",
            created_at=str_timestamp(record.get("created_at")),
            updated_at=str_timestamp(record.get("updated_at")),
            is_active=bool(record.get("is_active", True)),
        )

    def to_record(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "is_active": self.is_active,
        }

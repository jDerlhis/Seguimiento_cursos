from dataclasses import dataclass

from data.entities._base import str_timestamp


@dataclass
class Tenant:
    """public.tenants — 20260530000001, slug en 004."""

    name: str
    id: str | None = None
    slug: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    is_active: bool = True

    @classmethod
    def from_record(cls, record: dict) -> "Tenant":
        return cls(
            id=record.get("id"),
            name=record.get("name") or "",
            slug=record.get("slug"),
            created_at=str_timestamp(record.get("created_at")),
            updated_at=str_timestamp(record.get("updated_at")),
            is_active=bool(record.get("is_active", True)),
        )

    def to_record(self) -> dict:
        row: dict = {
            "name": self.name,
            "is_active": self.is_active,
        }
        if self.slug is not None:
            row["slug"] = self.slug
        return row

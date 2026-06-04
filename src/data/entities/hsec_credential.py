from dataclasses import dataclass

from data.entities._base import str_timestamp


@dataclass
class HsecCredential:
    """public.hsec_credentials — 20260530000002."""

    tenant_id: str
    username: str
    vault_secret_id: str
    id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    is_active: bool = True

    @classmethod
    def from_record(cls, record: dict) -> "HsecCredential":
        return cls(
            id=record.get("id"),
            tenant_id=record.get("tenant_id") or "",
            username=record.get("username") or "",
            vault_secret_id=record.get("vault_secret_id") or "",
            created_at=str_timestamp(record.get("created_at")),
            updated_at=str_timestamp(record.get("updated_at")),
            is_active=bool(record.get("is_active", True)),
        )

    def to_record(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "username": self.username,
            "vault_secret_id": self.vault_secret_id,
            "is_active": self.is_active,
        }

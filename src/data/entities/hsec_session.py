from dataclasses import dataclass
from typing import Any

from data.entities._base import str_timestamp


@dataclass
class HsecSession:
    """public.hsec_sessions — 20260530000003."""

    tenant_id: str
    credential_id: str
    storage_state: dict[str, Any]
    id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    is_active: bool = True
    last_verified_at: str | None = None
    error: str | None = None

    @classmethod
    def from_record(cls, record: dict) -> "HsecSession":
        state = record.get("storage_state")
        return cls(
            id=record.get("id"),
            tenant_id=record.get("tenant_id") or "",
            credential_id=record.get("credential_id") or "",
            storage_state=state if isinstance(state, dict) else {},
            created_at=str_timestamp(record.get("created_at")),
            updated_at=str_timestamp(record.get("updated_at")),
            is_active=bool(record.get("is_active", True)),
            last_verified_at=str_timestamp(record.get("last_verified_at")),
            error=record.get("error"),
        )

    def to_record(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "credential_id": self.credential_id,
            "storage_state": self.storage_state,
            "is_active": self.is_active,
            "last_verified_at": self.last_verified_at,
            "error": self.error,
        }

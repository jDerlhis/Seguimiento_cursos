from dataclasses import dataclass
from enum import Enum

from data.entities._base import str_timestamp


class TenantMemberRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


@dataclass
class TenantMember:
    """public.tenant_members — 20260530000005."""

    tenant_id: str
    user_id: str
    role: TenantMemberRole = TenantMemberRole.MEMBER
    id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    @classmethod
    def from_record(cls, record: dict) -> "TenantMember":
        raw_role = record.get("role") or "member"
        return cls(
            id=record.get("id"),
            tenant_id=record.get("tenant_id") or "",
            user_id=record.get("user_id") or "",
            role=TenantMemberRole(raw_role),
            created_at=str_timestamp(record.get("created_at")),
            updated_at=str_timestamp(record.get("updated_at")),
        )

    def to_record(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "role": self.role.value,
        }

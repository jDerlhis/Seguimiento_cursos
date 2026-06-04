"""Capa transversal: entidades y esquema (sin acceso a BD ni repositorios)."""

from data import schema
from data.entities import (
    AuthUser,
    Company,
    HsecCourse,
    HsecCredential,
    HsecPerson,
    HsecSession,
    Tenant,
    TenantMember,
    TenantMemberRole,
)

__all__ = [
    "AuthUser",
    "Company",
    "HsecCourse",
    "HsecCredential",
    "HsecPerson",
    "HsecSession",
    "Tenant",
    "TenantMember",
    "TenantMemberRole",
    "schema",
]

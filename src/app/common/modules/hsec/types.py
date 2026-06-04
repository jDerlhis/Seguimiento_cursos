from dataclasses import dataclass, field
from typing import Any


@dataclass
class StorageState:
    """Estado de sesión Playwright (cookies + localStorage)."""

    cookies: list[dict[str, Any]] = field(default_factory=list)
    origins: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class HsecCredential:
    id: str
    username: str
    password: str


@dataclass
class LoginResult:
    success: bool
    message: str
    used_saved_session: bool
    mfa_required: bool
    session_id: str | None = None


@dataclass
class ScrapedPerson:
    """Resultado del modal de personas en ReportePersonalCapacitado."""

    tipo_documento: str
    nro_documento: str
    nombres: str
    apellidos: str
    empresa: str


@dataclass
class ScrapedCourse:
    """Fila de capacitación del reporte embebido."""

    nro_documento: str
    tema: str
    fecha: str | None = None
    duracion: str | None = None
    area: str | None = None
    tipo: str | None = None
    nota: str | None = None
    estado: str | None = None
    vencimiento: str | None = None


@dataclass
class SyncResult:
    dni: str
    persona_upserted: bool
    cursos_upserted: int
    error: str | None = None

import json
from dataclasses import dataclass, field
from datetime import datetime



@dataclass
class Person:
    id: int | None
    cod_persona: str
    nombres: str
    apellido_paterno: str
    apellido_materno: str | None
    cod_proveedor: str | None
    empresa: str | None
    cod_cargo: str | None
    cargo: str | None
    flag_persistente: str | None
    cod_tipo_persona: int | None
    nro_documento: str
    tipo_documento: str | None
    created_at: str | None = None

    @classmethod
    def from_row(cls, row: tuple) -> "Person":
        return cls(
            id=row[0],
            cod_persona=row[1],
            nombres=row[2],
            apellido_paterno=row[3],
            apellido_materno=row[4],
            cod_proveedor=row[5],
            empresa=row[6],
            cod_cargo=row[7],
            cargo=row[8],
            flag_persistente=row[9],
            cod_tipo_persona=row[10],
            nro_documento=row[11],
            tipo_documento=row[12],
            created_at=row[13]
        )

    @classmethod
    def from_api_dict(cls, data: dict) -> "Person":
        return cls(
            id=None,
            cod_persona=data.get("codPersona", ""),
            nombres=data.get("nombres", ""),
            apellido_paterno=data.get("apellidoPaterno", ""),
            apellido_materno=data.get("apellidoMaterno", ""),
            cod_proveedor=data.get("codProveedor", ""),
            empresa=data.get("empresa", ""),
            cod_cargo=data.get("codCargo", ""),
            cargo=data.get("cargo", ""),
            flag_persistente=data.get("flagPersistente", ""),
            cod_tipo_persona=data.get("codTipoPersona", None),
            nro_documento=data.get("nroDocumento", ""),
            tipo_documento=data.get("tipoDocumento", "")
        )



from dataclasses import dataclass
from typing import Optional

@dataclass
class Course:
    id: Optional[int]
    dni: str
    fecha: str
    duracion: str
    descripcion: str
    area: str
    estado: str
    nota: str
    minimo_aprobado: str
    fecha_vencimiento: str
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: tuple) -> "Course":
        return cls(
            id=row[0],
            dni=row[1],
            fecha=row[2],
            duracion=row[3],
            descripcion=row[4],
            area=row[5],
            estado=row[6],
            nota=row[7],
            minimo_aprobado=row[8],
            fecha_vencimiento=row[9],
            created_at=row[10]
        )

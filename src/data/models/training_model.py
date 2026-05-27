from dataclasses import dataclass


@dataclass
class Training:
    id: int | None
    cod_persona: str
    nombre_persona: str
    curso: str
    fecha_finalizacion: str
    duracion: str | None
    nota: float | None
    created_at: str | None = None

    @classmethod
    def from_row(cls, row: tuple) -> "Training":
        return cls(
            id=row[0],
            cod_persona=row[1],
            nombre_persona=row[2],
            curso=row[3],
            fecha_finalizacion=row[4],
            duracion=row[5],
            nota=row[6],
            created_at=row[7],
        )

    @classmethod
    def from_excel_row(cls, row: dict, cod_persona: str) -> "Training":
        nota_raw = row.get("Nota")
        try:
            nota = float(nota_raw) if nota_raw is not None else None
        except (ValueError, TypeError):
            nota = None
        return cls(
            id=None,
            cod_persona=cod_persona,
            nombre_persona=str(row.get("Nombres") or ""),
            curso=str(row.get("Curso") or ""),
            fecha_finalizacion=str(row.get("Fecha Finalización") or ""),
            duracion=str(row.get("Duración") or ""),
            nota=nota,
        )
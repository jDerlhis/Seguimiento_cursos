from data.database import get_connection, init_db
from data.models.person_model import Person


def ensure_schema() -> None:
    init_db()


def get_person_by_dni(dni: str) -> Person | None:
    ensure_schema()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                id, cod_persona, nombres, apellido_paterno, apellido_materno,
                cod_proveedor, empresa, cod_cargo, cargo, flag_persistente,
                cod_tipo_persona, nro_documento, tipo_documento, created_at
            FROM people
            WHERE nro_documento = ?
            """,
            (dni,),
        ).fetchone()

    return Person.from_row(tuple(row)) if row else None


def insert_person(person: Person) -> None:
    ensure_schema()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO people (
                cod_persona, nombres, apellido_paterno, apellido_materno,
                cod_proveedor, empresa, cod_cargo, cargo, flag_persistente,
                cod_tipo_persona, nro_documento, tipo_documento
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                person.cod_persona,
                person.nombres,
                person.apellido_paterno,
                person.apellido_materno,
                person.cod_proveedor,
                person.empresa,
                person.cod_cargo,
                person.cargo,
                person.flag_persistente,
                person.cod_tipo_persona,
                person.nro_documento,
                person.tipo_documento,
            ),
        )
        conn.commit()


def list_people() -> list[Person]:
    ensure_schema()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                id, cod_persona, nombres, apellido_paterno, apellido_materno,
                cod_proveedor, empresa, cod_cargo, cargo, flag_persistente,
                cod_tipo_persona, nro_documento, tipo_documento, created_at
            FROM people
            ORDER BY created_at DESC
            """
        ).fetchall()

    return [Person.from_row(tuple(row)) for row in rows]


def delete_person(dni: str) -> None:
    ensure_schema()
    with get_connection() as conn:
        conn.execute("DELETE FROM people WHERE nro_documento = ?", (dni,))
        conn.commit()

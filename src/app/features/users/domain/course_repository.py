from data.database import get_connection, init_db
from data.models.course_model import Course
from typing import List


def ensure_schema() -> None:
    init_db()


def insert_courses(courses: List[Course]) -> None:
    ensure_schema()
    with get_connection() as conn:
        for course in courses:
            conn.execute(
                """
                INSERT OR IGNORE INTO courses (
                    dni, fecha, duracion, descripcion, area,
                    estado, nota, minimo_aprobado, fecha_vencimiento
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    course.dni,
                    course.fecha,
                    course.duracion,
                    course.descripcion,
                    course.area,
                    course.estado,
                    course.nota,
                    course.minimo_aprobado,
                    course.fecha_vencimiento
                ),
            )
        conn.commit()


def get_courses_by_dni(dni: str) -> List[Course]:
    ensure_schema()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                id, dni, fecha, duracion, descripcion, area,
                estado, nota, minimo_aprobado, fecha_vencimiento, created_at
            FROM courses
            WHERE dni = ?
            ORDER BY fecha DESC
            """,
            (dni,),
        ).fetchall()

    return [Course.from_row(tuple(row)) for row in rows]

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "pyflow.db"

_SCHEMA = """

CREATE TABLE IF NOT EXISTS people (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cod_persona TEXT UNIQUE,
    nombres TEXT NOT NULL,
    apellido_paterno TEXT NOT NULL,
    apellido_materno TEXT,
    cod_proveedor TEXT,
    empresa TEXT,
    cod_cargo TEXT,
    cargo TEXT,
    flag_persistente TEXT,
    cod_tipo_persona INTEGER,
    nro_documento TEXT NOT NULL UNIQUE,
    tipo_documento TEXT,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dni TEXT NOT NULL,
    fecha TEXT,
    duracion TEXT,
    descripcion TEXT,
    area TEXT,
    estado TEXT,
    nota TEXT,
    minimo_aprobado TEXT,
    fecha_vencimiento TEXT,
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    UNIQUE(dni, descripcion, fecha)
);
"""


def _migrate(conn: sqlite3.Connection) -> None:
    columns = {row[1] for row in conn.execute("PRAGMA table_info(products)")}
    if not columns:
        return

    if "source_id" not in columns:
        conn.execute("ALTER TABLE products ADD COLUMN source_id TEXT")
    if "image_urls" not in columns:
        conn.execute(
            "ALTER TABLE products ADD COLUMN image_urls TEXT NOT NULL DEFAULT '[]'"
        )
    if "detail_url" not in columns:
        conn.execute(
            "ALTER TABLE products ADD COLUMN detail_url TEXT NOT NULL DEFAULT ''"
        )


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(_SCHEMA)
        _migrate(conn)
        conn.commit()

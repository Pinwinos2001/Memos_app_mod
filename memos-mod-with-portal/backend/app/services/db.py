import sqlite3
from pathlib import Path
from typing import Any, Tuple, Iterable

from ..core.config import DB_PATH

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS memos(
    id TEXT PRIMARY KEY,
    memo_id TEXT,
    corr_id TEXT,
    created_at TEXT,
    solicitante_email TEXT,
    area_sol TEXT,
    dni TEXT,
    nombre TEXT,
    area TEXT,
    cargo TEXT,
    equipo TEXT,
    jefe_email TEXT,
    inciso_num INTEGER,
    inciso_texto TEXT,
    hecho_que TEXT,
    hecho_cuando TEXT,
    hecho_donde TEXT,
    tipo TEXT,
    fecha_limite TEXT,
    estado TEXT,
    legal_aprobado TEXT,
    legal_comentario TEXT,
    edit_count INTEGER DEFAULT 0,
    last_edited TEXT,
    edit_history TEXT,
    docx_path TEXT,
    pdf_path TEXT,
    evid_dir TEXT
);
"""

WANTED_COLUMNS = {
    "id", "memo_id", "corr_id", "created_at", "solicitante_email", "area_sol",
    "dni", "nombre", "area", "cargo", "equipo", "jefe_email", "inciso_num",
    "inciso_texto", "hecho_que", "hecho_cuando", "hecho_donde", "tipo",
    "fecha_limite", "estado", "legal_aprobado", "legal_comentario",
    "edit_count", "last_edited", "edit_history", "docx_path",
    "pdf_path", "evid_dir"
}


def _get_connection() -> sqlite3.Connection:
    db_path = Path(DB_PATH)

    if not db_path.parent.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)

    # Sin row_factory especial: devolvemos filas como tuplas
    con = sqlite3.connect(str(db_path))
    return con


def db_init() -> None:
    con = _get_connection()
    try:
        cur = con.cursor()

        cur.executescript(SCHEMA_SQL)

        cur.execute("PRAGMA table_info(memos)")
        existing_cols = {row[1] for row in cur.fetchall()}

        missing = WANTED_COLUMNS - existing_cols
        for col in missing:
            if col == "edit_count":
                cur.execute(
                    "ALTER TABLE memos "
                    "ADD COLUMN edit_count INTEGER DEFAULT 0"
                )
            elif col == "inciso_num":
                cur.execute(
                    "ALTER TABLE memos "
                    "ADD COLUMN inciso_num INTEGER"
                )
            else:
                cur.execute(
                    f"ALTER TABLE memos "
                    f"ADD COLUMN {col} TEXT"
                )

        con.commit()
    finally:
        con.close()


def db_exec(q: str, args: Tuple[Any, ...] = ()) -> None:
    con = _get_connection()
    try:
        cur = con.cursor()
        cur.execute(q, args)
        con.commit()
    finally:
        con.close()


def db_exec_many(q: str, seq_of_args: Iterable[Tuple[Any, ...]]) -> None:
    con = _get_connection()
    try:
        cur = con.cursor()
        cur.executemany(q, seq_of_args)
        con.commit()
    finally:
        con.close()


def db_one(q: str, args: Tuple[Any, ...] = ()):
    con = _get_connection()
    try:
        cur = con.cursor()
        cur.execute(q, args)
        row = cur.fetchone()
        return row  # tuple or None
    finally:
        con.close()


def db_all(q: str, args: Tuple[Any, ...] = ()):
    con = _get_connection()
    try:
        cur = con.cursor()
        cur.execute(q, args)
        rows = cur.fetchall()
        return rows  # list[tuple]
    finally:
        con.close()

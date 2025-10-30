import sqlite3
from typing import Any, Tuple
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

def db_init():
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.cursor()
        cur.executescript(SCHEMA_SQL)
        # Backfill columns if schema evolved
        cur.execute("PRAGMA table_info(memos)")
        cols = {row[1] for row in cur.fetchall()}
        wanted = {
            "id","memo_id","corr_id","created_at","solicitante_email","area_sol",
            "dni","nombre","area","cargo","equipo","jefe_email","inciso_num",
            "inciso_texto","hecho_que","hecho_cuando","hecho_donde","tipo","fecha_limite",
            "estado","legal_aprobado","legal_comentario","edit_count","last_edited",
            "edit_history","docx_path","pdf_path","evid_dir"
        }
        missing = wanted - cols
        for c in missing:
            if c == "edit_count":
                cur.execute("ALTER TABLE memos ADD COLUMN edit_count INTEGER DEFAULT 0")
            else:
                cur.execute(f"ALTER TABLE memos ADD COLUMN {c} TEXT")
        con.commit()
    finally:
        con.close()

def db_exec(q: str, args: Tuple[Any,...]=()):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(q, args)
    con.commit()
    con.close()

def db_one(q: str, args: Tuple[Any,...]=()):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(q, args)
    row = cur.fetchone()
    con.close()
    return row
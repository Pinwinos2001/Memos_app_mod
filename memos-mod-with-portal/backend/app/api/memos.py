# backend/app/api/memos.py
from datetime import datetime
from pathlib import Path
from typing import List
import uuid
import json

from fastapi import APIRouter, Form, UploadFile, File, HTTPException, Header

from ..api.auth import require_auth
from ..services.db import db_exec, db_one, db_all
from ..services.memo import (
    validar_dni, validar_email, es_email_heineken, sanitizar_texto,
    previos_from_db, business_days_from, next_running_number,
    INCISO_TEXTO, tipo_por_historial
)
from ..services.documents import generate_doc_from_template, try_export_pdf
from ..services.mail import send_mail, get_legal_email, get_rrhh_emails
from ..core.config import OUT_DIR, BASE_URL

router = APIRouter()


def _sanitize_common(nombre, area, cargo, hecho_que, hecho_cuando, hecho_donde):
    nombre = sanitizar_texto(nombre)
    area = sanitizar_texto(area)
    cargo = sanitizar_texto(cargo)
    hecho_que = sanitizar_texto(hecho_que)
    hecho_cuando = sanitizar_texto(hecho_cuando)
    hecho_donde = sanitizar_texto(hecho_donde)
    return nombre, area, cargo, hecho_que, hecho_cuando, hecho_donde


@router.post("/submit")
async def submit(
    solicitante_email: str = Form(...),
    area_sol: str = Form(""),
    dni: str = Form(...),
    nombre: str = Form(...),
    area: str = Form(""),
    cargo: str = Form(""),
    equipo: str = Form(...),
    jefe_email: str = Form(...),
    inciso_num: int = Form(...),
    hecho_que: str = Form(...),
    hecho_cuando: str = Form(""),
    hecho_donde: str = Form(""),
    evidencias: List[UploadFile] = File(None),
):
    # Validaciones
    if not validar_dni(dni):
        raise HTTPException(400, "DNI debe tener 8 dígitos.")
    if not validar_email(solicitante_email):
        raise HTTPException(400, "Email del solicitante inválido.")
    if not validar_email(jefe_email):
        raise HTTPException(400, "Email del jefe directo inválido.")
    if not es_email_heineken(solicitante_email):
        raise HTTPException(400, "Email del solicitante debe ser de dominio Heineken.")
    if not es_email_heineken(jefe_email):
        raise HTTPException(400, "Email del jefe directo debe ser de dominio Heineken.")

    nombre, area, cargo, hecho_que, hecho_cuando, hecho_donde = _sanitize_common(
        nombre, area, cargo, hecho_que, hecho_cuando, hecho_donde
    )

    previos_db = previos_from_db(dni)
    tipo = tipo_por_historial(previos_db)

    memo_id = next_running_number("MEM")
    corr_id = next_running_number("CS")
    fecha_limite = business_days_from(datetime.now(), 3).strftime("%d/%m/%Y")
    uid = str(uuid.uuid4())

    folder = OUT_DIR / datetime.now().strftime("%Y/%m") / memo_id
    folder.mkdir(parents=True, exist_ok=True)

    evid_dir = folder / "evidencias"
    evid_paths: List[Path] = []
    if evidencias:
        evid_dir.mkdir(exist_ok=True)
        for f in evidencias:
            if not f.filename:
                continue
            ext = (f.filename or "").lower()
            if not (ext.endswith(".png") or ext.endswith(".jpg") or ext.endswith(".jpeg")):
                continue
            dest = evid_dir / f.filename
            with dest.open("wb") as w:
                w.write(await f.read())
            evid_paths.append(dest)

    inciso_texto = INCISO_TEXTO.get(int(inciso_num), "Inciso del Art. 35")
    ctx = {
        "a_nombre": nombre,
        "a_cargo": cargo or "",
        "memo_id": memo_id,
        "tipo": tipo,
        "fecha": datetime.now().strftime("%d/%m/%Y"),
        "asunto": f"Incumplimiento Art. 35 inciso {inciso_num}",
        "art_texto": inciso_texto,
        "hecho_que": hecho_que,
        "hecho_cuando": hecho_cuando,
        "hecho_donde": hecho_donde,
        "fecha_limite": fecha_limite,
        "num": inciso_num,
    }

    docx_path = folder / f"{memo_id}.docx"
    out_doc = generate_doc_from_template(ctx, evid_paths, docx_path)
    docx_path = docx_path if out_doc.suffix == ".docx" else out_doc
    pdf_path = try_export_pdf(docx_path) if docx_path.suffix == ".docx" else None
    pdf_str = str(pdf_path) if pdf_path else ""

    db_exec(
        """
        INSERT INTO memos(
            id, memo_id, corr_id, created_at, solicitante_email, area_sol, dni, nombre, area, cargo, equipo,
            jefe_email, inciso_num, inciso_texto, hecho_que, hecho_cuando, hecho_donde,
            tipo, fecha_limite, estado, legal_aprobado, docx_path, pdf_path, evid_dir
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            uid,
            memo_id,
            corr_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            solicitante_email,
            area_sol,
            dni,
            nombre,
            area,
            cargo,
            equipo,
            jefe_email,
            int(inciso_num),
            inciso_texto,
            hecho_que,
            hecho_cuando,
            hecho_donde,
            tipo,
            fecha_limite,
            "En revisión Legal",
            "",
            str(docx_path),
            pdf_str,
            str(evid_dir if evid_paths else ""),
        ),
    )

    # Emails
    legal_review_link = f"{BASE_URL}/apps/memos/legal/review.html?id={uid}"
    html_mail = f"""
    <p>Solicitud de memo <b>{memo_id}</b> ({tipo}).</p>
    <p>Trabajador: <b>{nombre}</b> (DNI {dni}) - {area} / {cargo}</p>
    <p><b>Art. 35, inciso:</b> {inciso_num} — {inciso_texto}</p>
    <p><b>Hechos:</b> {hecho_que}<br>
    <b>Cuándo:</b> {hecho_cuando} &nbsp;|&nbsp; <b>Dónde:</b> {hecho_donde}</p>
    <p>Revisar y aprobar: <a href="{legal_review_link}">{legal_review_link}</a></p>
    """
    atts = [docx_path] + ([pdf_path] if pdf_path else [])
    legal_email = get_legal_email()
    if legal_email:
        cc_list = [jefe_email] if jefe_email else []
        cc_list.extend(get_rrhh_emails())
        send_mail(
            [legal_email],
            f"[Revisión Legal] {memo_id} - {nombre}",
            html_mail,
            attachments=atts,
            cc=cc_list,
        )

    if solicitante_email:
        notif_html = f"""
        <p>Su solicitud de memo <b>{memo_id}</b> ha sido enviada a Legal para revisión.</p>
        <p>Trabajador: <b>{nombre}</b> (DNI {dni}) - {area} / {cargo}</p>
        """
        send_mail(
            [solicitante_email],
            f"[Solicitud enviada] {memo_id} - {nombre}",
            notif_html,
            attachments=None,
            cc=None,
        )

    created_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf_or_docx_url = f"{BASE_URL}/file?path={pdf_str}" if pdf_str else f"{BASE_URL}/file?path={docx_path}"

    # 👉 Sin forzar redirects de frontend. El HTML decide qué hacer.
    return {
        "ok": True,
        "id": uid,
        "memo_id": memo_id,
        "corr_id": corr_id,
        "created_at": created_str,
        "status": "Legal para revisión",
        "pdf_url": pdf_or_docx_url,
    }


@router.post("/update/{id}")
async def update_memo(
    id: str,
    solicitante_email: str = Form(...),
    area_sol: str = Form(""),
    dni: str = Form(...),
    nombre: str = Form(...),
    area: str = Form(""),
    cargo: str = Form(""),
    equipo: str = Form(...),
    jefe_email: str = Form(...),
    inciso_num: int = Form(...),
    hecho_que: str = Form(...),
    hecho_cuando: str = Form(""),
    hecho_donde: str = Form(""),
    evidencias: List[UploadFile] = File(None),
):
    if not validar_dni(dni):
        raise HTTPException(400, "DNI debe tener 8 dígitos.")
    if not validar_email(solicitante_email):
        raise HTTPException(400, "Email del solicitante inválido.")
    if not validar_email(jefe_email):
        raise HTTPException(400, "Email del jefe directo inválido.")
    if not es_email_heineken(solicitante_email):
        raise HTTPException(400, "Email del solicitante debe ser de dominio Heineken.")
    if not es_email_heineken(jefe_email):
        raise HTTPException(400, "Email del jefe directo debe ser de dominio Heineken.")

    nombre, area, cargo, hecho_que, hecho_cuando, hecho_donde = _sanitize_common(
        nombre, area, cargo, hecho_que, hecho_cuando, hecho_donde
    )

    current_row = db_one(
        "SELECT memo_id, docx_path, pdf_path, evid_dir, edit_count FROM memos WHERE id=?",
        (id,),
    )
    if not current_row:
        raise HTTPException(404, "Memo no encontrado.")

    memo_id, current_docx_path, current_pdf_path, current_evid_dir, edit_count = current_row
    new_edit_count = (edit_count or 0) + 1

    previos_db = previos_from_db(dni)
    tipo = tipo_por_historial(previos_db)

    fecha_limite = business_days_from(datetime.now(), 3).strftime("%d/%m/%Y")

    evid_paths: List[Path] = []
    if evidencias:
        evid_dir = Path(current_evid_dir) if current_evid_dir else None
        if evid_dir and evid_dir.exists():
            for f in evid_dir.glob("*"):
                if f.is_file():
                    f.unlink()
        else:
            folder = OUT_DIR / datetime.now().strftime("%Y/%m") / memo_id
            evid_dir = folder / "evidencias"
            evid_dir.mkdir(parents=True, exist_ok=True)

        for f in evidencias:
            if not f.filename:
                continue
            ext = (f.filename or "").lower()
            if not (ext.endswith(".png") or ext.endswith(".jpg") or ext.endswith(".jpeg")):
                continue
            dest = evid_dir / f.filename
            with dest.open("wb") as w:
                w.write(await f.read())
            evid_paths.append(dest)
    else:
        evid_dir = Path(current_evid_dir) if current_evid_dir else None

    inciso_texto = INCISO_TEXTO.get(int(inciso_num), "Inciso del Art. 35")
    ctx = {
        "a_nombre": nombre,
        "a_cargo": cargo or "",
        "memo_id": memo_id,
        "tipo": tipo,
        "fecha": datetime.now().strftime("%d/%m/%Y"),
        "asunto": f"Incumplimiento Art. 35 inciso {inciso_num}",
        "art_texto": inciso_texto,
        "hecho_que": hecho_que,
        "hecho_cuando": hecho_cuando,
        "hecho_donde": hecho_donde,
        "fecha_limite": fecha_limite,
        "num": inciso_num,
    }

    docx_path = Path(current_docx_path) if current_docx_path else (
        OUT_DIR / datetime.now().strftime("%Y/%m") / memo_id / f"{memo_id}.docx"
    )
    out_doc = generate_doc_from_template(ctx, evid_paths, docx_path)
    docx_path = docx_path if out_doc.suffix == ".docx" else out_doc
    pdf_path = try_export_pdf(docx_path) if docx_path.suffix == ".docx" else None
    pdf_str = str(pdf_path) if pdf_path else ""

    edit_history = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "changes": {
            "nombre": nombre,
            "dni": dni,
            "equipo": equipo,
            "inciso_num": inciso_num,
            "hecho_que": hecho_que,
            "hecho_cuando": hecho_cuando,
            "hecho_donde": hecho_donde,
        },
    }

    db_exec(
        """
        UPDATE memos SET
            solicitante_email=?, area_sol=?, dni=?, nombre=?, area=?, cargo=?, equipo=?,
            jefe_email=?, inciso_num=?, inciso_texto=?, hecho_que=?, hecho_cuando=?, hecho_donde=?,
            tipo=?, fecha_limite=?, estado=?, legal_aprobado=?, legal_comentario=?,
            edit_count=?, last_edited=?, edit_history=?, docx_path=?, pdf_path=?, evid_dir=?
        WHERE id=?
        """,
        (
            solicitante_email,
            area_sol,
            dni,
            nombre,
            area,
            cargo,
            equipo,
            jefe_email,
            str(inciso_num),
            inciso_texto,
            hecho_que,
            hecho_cuando,
            hecho_donde,
            tipo,
            fecha_limite,
            "En revisión Legal",
            "",
            "",
            new_edit_count,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            json.dumps(edit_history),
            str(docx_path),
            pdf_str,
            str(evid_dir) if evid_dir else "",
            id,
        ),
    )

    # Avisos
    legal_review_link = f"{BASE_URL}/legal/review.html?id={id}"
    html = f"""
    <p>Memo <b>{memo_id}</b> ha sido actualizado y requiere nueva revisión.</p>
    <p>Trabajador: <b>{nombre}</b> (DNI {dni}) - {area} / {cargo}</p>
    <p><b>Art. 35, inciso:</b> {inciso_num} — {inciso_texto}</p>
    <p><b>Hechos:</b> {hecho_que}<br>
    <b>Cuándo:</b> {hecho_cuando} &nbsp;|&nbsp; <b>Dónde:</b> {hecho_donde}</p>
    <p>Revisar y aprobar: <a href="{legal_review_link}">{legal_review_link}</a></p>
    <p><small>Este memo ha sido editado {new_edit_count} vez(es).</small></p>
    """
    atts = [docx_path] + ([pdf_path] if pdf_path else [])
    legal_email = get_legal_email()
    if legal_email:
        cc_list = [jefe_email] if jefe_email else []
        cc_list.extend(get_rrhh_emails())
        send_mail(
            [legal_email],
            f"[Memo actualizado] {memo_id} - {nombre}",
            html,
            attachments=atts,
            cc=cc_list,
        )

    if solicitante_email:
        notif_html = """
        <p>Su memo ha sido actualizado y reenviado a Legal para revisión.</p>
        """
        send_mail(
            [solicitante_email],
            f"[Memo actualizado] {memo_id} - {nombre}",
            notif_html,
            attachments=None,
            cc=None,
        )

    return {"ok": True, "id": id, "memo_id": memo_id}


@router.get("/{id}")
def api_get_memo(id: str, Authorization: str | None = Header(None)):
    # legal/rrhh/dash
    require_auth(Authorization, ["legal", "rrhh", "dash"])
    row = db_one(
        """
        SELECT id, memo_id, corr_id, created_at, solicitante_email, area_sol, dni, nombre, area, cargo, equipo,
               jefe_email, inciso_num, inciso_texto, hecho_que, hecho_cuando, hecho_donde, tipo, fecha_limite,
               estado, legal_aprobado, legal_comentario, docx_path, pdf_path
        FROM memos WHERE id=?
        """,
        (id,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Memo no encontrado")

    keys = [
        "id","memo_id","corr_id","created_at","solicitante_email","area_sol","dni","nombre","area","cargo","equipo",
        "jefe_email","inciso_num","inciso_texto","hecho_que","hecho_cuando","hecho_donde","tipo","fecha_limite",
        "estado","legal_aprobado","legal_comentario","docx_path","pdf_path"
    ]
    return {k: v for k, v in zip(keys, row)}


@router.get("")
def api_memos(
    buscar: str = "",
    estado: str = "",
    limit: int = 50,
    Authorization: str | None = Header(None),
):
    require_auth(Authorization, ["dash", "rrhh", "legal"])

    from ..core.config import DB_PATH
    import sqlite3

    con = sqlite3.connect(str(DB_PATH))
    cur = con.cursor()

    where = []
    params = []
    if buscar:
        where.append("(dni LIKE ? OR nombre LIKE ? OR memo_id LIKE ?)")
        s = f"%{buscar}%"
        params.extend([s, s, s])
    if estado:
        where.append("estado = ?")
        params.append(estado)

    where_clause = ("WHERE " + " AND ".join(where)) if where else ""
    cur.execute(
        f"""
        SELECT memo_id, dni, nombre, area, cargo, equipo, tipo, estado,
               legal_aprobado, created_at, fecha_limite, id
        FROM memos {where_clause}
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (*params, limit),
    )
    rows = cur.fetchall()
    con.close()

    memos = [
        {
            "memo_id": r[0],
            "dni": r[1],
            "nombre": r[2],
            "area": r[3],
            "cargo": r[4],
            "equipo": r[5],
            "tipo": r[6],
            "estado": r[7],
            "legal_aprobado": r[8],
            "created_at": r[9],
            "fecha_limite": r[10],
            "id": r[11],
        }
        for r in rows
    ]
    return {"memos": memos, "total": len(memos)}


@router.get("/metrics")
def api_metrics(Authorization: str | None = Header(None)):
    # Solo dashboard o roles internos autorizados
    require_auth(Authorization, ["dash", "legal", "rrhh"])

    from ..core.config import DB_PATH
    import sqlite3

    con = sqlite3.connect(str(DB_PATH))
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) FROM memos")
    total_memos = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM memos WHERE estado LIKE '%revisión%' OR estado LIKE '%Pendiente%'")
    pendientes = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM memos WHERE estado LIKE '%Aprobado%'")
    aprobados = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM memos WHERE estado = 'Emitido'")
    emitidos = cur.fetchone()[0]

    cur.execute("""
        SELECT strftime('%Y-%m', created_at) as mes, COUNT(*) as cantidad
        FROM memos 
        WHERE created_at >= date('now', '-6 months')
        GROUP BY strftime('%Y-%m', created_at)
        ORDER BY mes
    """)
    memos_por_mes = [{"mes": row[0], "cantidad": row[1]} for row in cur.fetchall()]

    cur.execute("""
        SELECT equipo, COUNT(*) as cantidad
        FROM memos 
        WHERE equipo IS NOT NULL AND equipo != ''
        GROUP BY equipo
        ORDER BY cantidad DESC
    """)
    memos_por_equipo = [{"equipo": row[0], "cantidad": row[1]} for row in cur.fetchall()]

    cur.execute("""
        SELECT inciso_num, COUNT(*) as cantidad
        FROM memos 
        WHERE inciso_num IS NOT NULL
        GROUP BY inciso_num
        ORDER BY cantidad DESC
        LIMIT 5
    """)
    incisos_comunes = [{"inciso": row[0], "cantidad": row[1]} for row in cur.fetchall()]

    cur.execute("""
        SELECT tipo, COUNT(*) as cantidad
        FROM memos 
        WHERE tipo IS NOT NULL
        GROUP BY tipo
        ORDER BY cantidad DESC
    """)
    memos_por_tipo = [{"tipo": row[0], "cantidad": row[1]} for row in cur.fetchall()]

    cur.execute("""
        SELECT strftime('%Y-%W', created_at) as semana, COUNT(*) as cantidad
        FROM memos 
        WHERE created_at >= date('now', '-4 weeks')
        GROUP BY strftime('%Y-%W', created_at)
        ORDER BY semana
    """)
    tendencia_semanal = [{"semana": row[0], "cantidad": row[1]} for row in cur.fetchall()]

    con.close()

    return {
        "metricas_basicas": {
            "total_memos": total_memos,
            "pendientes": pendientes,
            "aprobados": aprobados,
            "emitidos": emitidos,
        },
        "memos_por_mes": memos_por_mes,
        "memos_por_equipo": memos_por_equipo,
        "incisos_comunes": incisos_comunes,
        "memos_por_tipo": memos_por_tipo,
        "tendencia_semanal": tendencia_semanal,
    }


@router.get("/summary")
def api_summary(role: str, Authorization: str = Header(None)):
    role = (role or "").lower()
    if role not in ("legal", "rrhh"):
        raise HTTPException(status_code=400, detail="Rol inválido")

    # permite consultar al propio rol o al dashboard
    require_auth(Authorization, [role, "dash"])

    if role == "legal":
        approved = db_one("SELECT COUNT(*) FROM memos WHERE UPPER(legal_aprobado)='APROBADO'")[0]
        not_appr = db_one("SELECT COUNT(*) FROM memos WHERE UPPER(legal_aprobado)='OBSERVADO'")[0]
        pending = db_one("""
            SELECT COUNT(*) FROM memos
            WHERE COALESCE(legal_aprobado,'')=''
              AND estado NOT IN ('Observado Legal','Emitido','Aprobado RRHH','Observado RRHH')
        """)[0]

        pending_rows = db_all("""
            SELECT id, memo_id, dni, nombre, equipo, created_at
            FROM memos
            WHERE COALESCE(legal_aprobado,'')=''
              AND estado NOT IN ('Observado Legal','Emitido','Aprobado RRHH','Observado RRHH')
            ORDER BY datetime(created_at) ASC
            LIMIT 50
        """)
        approved_rows = db_all("""
            SELECT id, memo_id, dni, nombre, equipo, created_at
            FROM memos
            WHERE UPPER(legal_aprobado)='APROBADO'
            ORDER BY datetime(created_at) DESC
            LIMIT 50
        """)
        rejected_rows = db_all("""
            SELECT id, memo_id, dni, nombre, equipo, created_at
            FROM memos
            WHERE UPPER(legal_aprobado)='OBSERVADO'
            ORDER BY datetime(created_at) DESC
            LIMIT 50
        """)
    else:
        approved = db_one("""
            SELECT COUNT(*) FROM memos
            WHERE estado IN ('Emitido','Aprobado RRHH')
        """)[0]
        not_appr = db_one("""
            SELECT COUNT(*) FROM memos
            WHERE estado='Observado RRHH'
        """)[0]
        pending = db_one("""
            SELECT COUNT(*) FROM memos
            WHERE legal_aprobado='APROBADO'
              AND estado NOT IN ('Emitido','Aprobado RRHH','Observado RRHH')
        """)[0]

        pending_rows = db_all("""
            SELECT id, memo_id, dni, nombre, equipo, created_at
            FROM memos
            WHERE legal_aprobado='APROBADO'
              AND estado NOT IN ('Emitido','Aprobado RRHH','Observado RRHH')
            ORDER BY datetime(created_at) ASC
            LIMIT 50
        """)
        approved_rows = db_all("""
            SELECT id, memo_id, dni, nombre, equipo, created_at
            FROM memos
            WHERE estado IN ('Emitido','Aprobado RRHH')
            ORDER BY datetime(created_at) DESC
            LIMIT 50
        """)
        rejected_rows = db_all("""
            SELECT id, memo_id, dni, nombre, equipo, created_at
            FROM memos
            WHERE estado='Observado RRHH'
            ORDER BY datetime(created_at) DESC
            LIMIT 50
        """)

    def pack(rows):
        return [
            {
                "id": r[0],
                "memo_id": r[1],
                "dni": r[2],
                "nombre": r[3],
                "equipo": r[4],
                "created_at": r[5],
            }
            for r in rows
        ]

    return {
        "role": role,
        "counts": {"approved": approved, "pending": pending, "not_approved": not_appr},
        "pending": pack(pending_rows),
        "approved_list": pack(approved_rows),
        "not_approved_list": pack(rejected_rows),
    }

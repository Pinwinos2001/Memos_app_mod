from pathlib import Path
from fastapi import APIRouter, Form, HTTPException, Header
from ..api.auth import require_auth
from ..services.db import db_exec, db_one
from ..services.mail import send_mail, get_legal_email, get_rrhh_emails
from ..core.config import BASE_URL

router = APIRouter()

@router.post("/legal_approve")
def legal_approve(id: str = Form(...), decision: str = Form(...), comentario: str = Form(""), Authorization: str | None = Header(None)):  # requires role=legal
    require_auth(Authorization, ["legal"])
    require_auth(Authorization, ["rrhh"])
    row = db_one(
        "SELECT memo_id,dni,nombre,solicitante_email,jefe_email,docx_path,pdf_path FROM memos WHERE id=?",
        (id,),
    )
    if not row:
        raise HTTPException(404, "No existe el memo.")
    memo_id, dni, nombre, solicitante_email, jefe_email, docx_path, pdf_path = row

    if decision == "APROBAR":
        db_exec("UPDATE memos SET legal_aprobado='APROBADO', estado='Aprobado Legal - Pendiente RRHH' WHERE id=?", (id,))
        review_link = f"{BASE_URL}/rrhh/review.html?id={id}"
        html_rrhh = f"""
        <p>Memo <b>{memo_id}</b> aprobado por Legal.</p>
        <p>Trabajador: <b>{nombre}</b> (DNI {dni})</p>
        <p>Revisar y aprobar: <a href="{review_link}">{review_link}</a></p>
        """
        atts = [Path(docx_path)] + ([Path(pdf_path)] if pdf_path else [])
        rrhh_emails = get_rrhh_emails()
        if rrhh_emails:
            cc_list = [jefe_email] if jefe_email else []
            send_mail(rrhh_emails, f"[Aprobado Legal] {memo_id} - {nombre}", html_rrhh, attachments=atts, cc=cc_list)

        if solicitante_email:
            notif_html = f"""
            <p>Su solicitud de memo <b>{memo_id}</b> fue aprobada por Legal.</p>
            <p>Ahora RRHH lo revisará para la aprobación final.</p>
            """
            send_mail([solicitante_email], f"[Aprobado por Legal] {memo_id} - {nombre}", notif_html, attachments=None, cc=None)

        return {"ok": True, "status": "Pendiente revisión de RRHH", "memo_id": memo_id}

    db_exec(
        "UPDATE memos SET legal_aprobado='OBSERVADO', legal_comentario=?, estado='Observado Legal' WHERE id=?",
        (comentario, id),
    )
    edit_link = f"{BASE_URL}/edit/index.html?id={id}"
    html_obs = f"""
    <p>Su solicitud de memo <b>{memo_id}</b> ha sido observada por Legal.</p>
    <p><b>Observaciones:</b></p>
    <p>{(comentario or '(sin comentario específico)')}</p>
    <p>Por favor, revise y corrija la información según las observaciones.</p>
    <p><a href="{edit_link}">Editar Memo</a></p>
    """
    if solicitante_email:
        cc_list = get_rrhh_emails()
        send_mail([solicitante_email], f"[Observado Legal] {memo_id}", html_obs, attachments=None, cc=cc_list)

    return {"ok": True, "status": "Observado por Legal", "memo_id": memo_id}

@router.post("/approve")
def approve(id: str = Form(...), decision: str = Form(...), comentario: str = Form(""), Authorization: str | None = Header(None)):  # requires role=rrhh
    row = db_one(
        "SELECT memo_id,dni,nombre,area,cargo,solicitante_email,jefe_email,docx_path,pdf_path,legal_aprobado FROM memos WHERE id=?",
        (id,),
    )
    if not row:
        raise HTTPException(404, "No existe el memo.")
    memo_id, dni, nombre, area, cargo, solicitante_email, jefe_email, docx_path, pdf_path, legal_aprobado = row

    if legal_aprobado != "APROBADO":
        raise HTTPException(403, "Este memo debe ser aprobado por Legal primero.")

    edit_link = f"{BASE_URL}/edit/index.html?id={id}"
    if decision == "APROBAR":
        # Marcar aprobado por RRHH + emitido
        db_exec("UPDATE memos SET estado='Aprobado RRHH' WHERE id=?", (id,))
        html = f"""
        <p>Memorándum <b>{memo_id}</b> aprobado por el equipo de RRHH y Legal.</p>
        <p>Por favor, hacer saber al colaborador y coordinar los descargos (3 días hábiles).</p>
        <p>Trabajador: <b>{nombre}</b> (DNI {dni}) - {area} / {cargo}</p>
        """
        atts = [Path(docx_path)] + ([Path(pdf_path)] if pdf_path else [])
        to_list = [jefe_email] if jefe_email else []
        cc_list = [solicitante_email] if solicitante_email else []
        from ..services.mail import get_rrhh_emails, get_legal_email
        cc_list.extend(get_rrhh_emails())
        legal_email = get_legal_email()
        if legal_email:
            cc_list.append(legal_email)
        if to_list:
            send_mail(to_list, f"[Memo aprobado] {memo_id} - {nombre}", html, attachments=atts, cc=cc_list)

        db_exec("UPDATE memos SET estado='Emitido' WHERE id=?", (id,))
        return {"ok": True, "status": "Emitido", "memo_id": memo_id, "dashboard": "/dashboard/index.html"}

    # Observado RRHH
    db_exec("UPDATE memos SET estado='Observado RRHH' WHERE id=?", (id,))
    html_obs = f"""
    <p>Su solicitud de memo <b>{memo_id}</b> ha sido observada por RRHH.</p>
    <p><b>Observaciones:</b></p>
    <p>{(comentario or '(sin comentario específico)')}</p>
    <p>Por favor, revise y corrija la información según las observaciones.</p>
    <p><a href="{edit_link}">Editar Memo</a></p>
    """
    if solicitante_email:
        cc_list = get_rrhh_emails()
        send_mail([solicitante_email], f"[Observado RRHH] {memo_id}", html_obs, attachments=None, cc=cc_list)

    return {"ok": True, "status": "Observado por RRHH", "memo_id": memo_id}

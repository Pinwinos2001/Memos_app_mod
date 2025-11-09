from pathlib import Path
from typing import List
import platform
from datetime import datetime
from ..core.config import RRHH_JEFE_EMAIL, RRHH_EQUIPO_EMAIL, LEGAL_JEFE_EMAIL, LEGAL_EQUIPO_EMAIL, LEGAL_EMAIL, RRHH_EMAIL, OUT_DIR
import base64
import json
import os
import pathlib
import mimetypes
import requests
from typing import Iterable, List, Optional, Union
from ..core.config import DEBUG

FLOW_URL = os.getenv("MAIL_FLOW_URL")  # Pon aquí la URL de tu flujo Power Automate en .env
API_KEY = os.getenv("MAIL_API_KEY")    # Opcional, si tu flujo valida API Key


PathLike = Union[str, pathlib.Path]


def file_to_base64(path: PathLike) -> str:
    p = pathlib.Path(path)
    with p.open("rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _infer_content_type(path: PathLike) -> str:
    """
    Intenta deducir el tipo MIME a partir de la extensión.
    Si no se puede, usa 'application/octet-stream'.
    """
    p = pathlib.Path(path)
    ctype, _ = mimetypes.guess_type(str(p))
    return ctype or "application/octet-stream"


def build_attachments(paths: Iterable[PathLike]) -> List[dict]:
    """
    Recibe una lista de rutas (str o Path) y devuelve la estructura
    que espera el flujo de Power Automate:
    [
      { "fileName": "...", "contentBytes": "...", "contentType": "..." },
      ...
    ]
    """
    atts: List[dict] = []
    for path in paths:
        p = pathlib.Path(path)
        if not p.is_file():
            continue
        atts.append({
            "fileName": p.name,
            "contentBytes": file_to_base64(p),
            "contentType": _infer_content_type(p),
        })
    return atts


def send_mail(
    to: List[str],
    subject: str,
    body: str,
    attachments: Optional[Iterable[PathLike]] = None,
    cc: Optional[Iterable[str]] = None,
) -> None:
    """
    Envía un correo usando el flujo de Power Automate.

    - to: lista de destinatarios.
    - subject: asunto.
    - body: HTML.
    - attachments: paths de archivos (opcional).
    - cc: lista de CC (opcional).
    """

    if not FLOW_URL:
        # Si no está configurado, en producción tal vez quieras lanzar error.
        if DEBUG:
            print("[send_mail] FLOW_URL no configurado. Correo no enviado.")
            print("TO:", to, "SUBJECT:", subject)
        return

    to_list = [e for e in (to or []) if e]
    cc_list = [e for e in (cc or []) if e]

    if not to_list:
        if DEBUG:
            print("[send_mail] Sin destinatarios. Correo no enviado.")
        return
    
    att_list = build_attachments(attachments or [])

    payload = {
        "to": to_list,
        "cc": cc_list,               # siempre presente (vacía o con datos)
        "subject": subject,
        "body": body,
        "attachments": att_list,     # siempre presente (vacía o con datos)
    }

    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["X-API-Key"] = API_KEY

    try:
        resp = requests.post(FLOW_URL, headers=headers, data=json.dumps(payload), timeout=60)
        
        print("[send_mail] Status:", resp.status_code)
        try:
            print("[send_mail] Body:", resp.json())
        except Exception:
            print("[send_mail] Body (raw):", resp.text)

        # Si quieres ser estricto:
        # if resp.status_code >= 400:
        #     raise RuntimeError(f"Error enviando correo: {resp.status_code} {resp.text}")

    except Exception as e:
        # En producción: loguea; no revientes toda la API por fallo de correo
        print("[send_mail] EXCEPTION:", repr(e))

def send_mail_preview(to, subject, html, attachments=None, cc=None):
    prev_dir = OUT_DIR / "mails"
    prev_dir.mkdir(parents=True, exist_ok=True)
    f = prev_dir / f"preview_{datetime.now():%Y%m%d_%H%M%S}.html"
    body = f"""
    <p><b>TO</b>: {', '.join(to or [])}<br>
    <b>CC</b>: {', '.join(cc or [])}</p>
    <hr>{html}
    <p>Adjuntos: {', '.join([Path(a).name for a in (attachments or [])])}</p>
    """
    f.write_text(body, encoding="utf-8")

def get_legal_email() -> str:
    if LEGAL_JEFE_EMAIL:
        return LEGAL_JEFE_EMAIL
    elif LEGAL_EMAIL:
        return LEGAL_EMAIL
    return ""

def get_rrhh_emails() -> List[str]:
    emails: List[str] = []
    if RRHH_JEFE_EMAIL:
        emails.append(RRHH_JEFE_EMAIL)
    elif RRHH_EMAIL:
        emails.append(RRHH_EMAIL)
    if RRHH_EQUIPO_EMAIL:
        emails.append(RRHH_EQUIPO_EMAIL)
    elif LEGAL_EQUIPO_EMAIL:
        emails.append(LEGAL_EQUIPO_EMAIL)
    return emails
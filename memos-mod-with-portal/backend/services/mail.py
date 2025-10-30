from pathlib import Path
from typing import List
import platform
from datetime import datetime
from ..core.config import OUTLOOK, RRHH_JEFE_EMAIL, RRHH_EQUIPO_EMAIL, LEGAL_JEFE_EMAIL, LEGAL_EQUIPO_EMAIL, LEGAL_EMAIL, RRHH_EMAIL, OUT_DIR
from ..core.compat import win32, pythoncom

def send_mail_outlook(to, subject, html, attachments=None, cc=None):
    if platform.system() != "Windows" or win32 is None:
        raise RuntimeError("Outlook no disponible.")
    if pythoncom:
        pythoncom.CoInitialize()
    try:
        ol = win32.Dispatch("Outlook.Application")
        mail = ol.CreateItem(0)
        mail.To = ";".join(to or [])
        if cc: mail.CC = ";".join(cc)
        mail.Subject = subject
        mail.HTMLBody = html
        for att in attachments or []:
            p = Path(att)
            if p.exists():
                mail.Attachments.Add(str(p))
        mail.Send()
    finally:
        if pythoncom:
            pythoncom.CoUninitialize()

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

def send_mail(to, subject, html, attachments=None, cc=None):
    if OUTLOOK:
        try:
            return send_mail_outlook(to, subject, html, attachments, cc)
        except Exception:
            pass
    return send_mail_preview(to, subject, html, attachments, cc)
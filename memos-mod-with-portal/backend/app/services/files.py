from app.services.db import db_one
from ..api.auth import require_auth
from pathlib import Path
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import FileResponse
from ..core.config import OUT_DIR

router = APIRouter()


def ensure_dir(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

@router.get("/file")
def get_file(path: str, Authorization: str | None = Header(None)):  # any authenticated role
    # Restrict served files to OUT_DIR for safety
    require_auth(Authorization, ["legal","rrhh","dash"])  # gate download
    p = Path(path)
    try:
        p = p.resolve()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path")
    if not str(p).startswith(str(OUT_DIR.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(p))


@router.get("/memo_file/{id}")
def get_memo_file(id: str):
    row = db_one("SELECT pdf_path, docx_path FROM memos WHERE id=?", (id,))
    if not row:
        raise HTTPException(404, "Memo no encontrado")

    pdf_rel, docx_rel = row

    # Priorizar PDF; si no hay, usar DOCX
    rel_path = pdf_rel or docx_rel
    if not rel_path:
        raise HTTPException(404, "Archivo no disponible")

    file_path = (OUT_DIR / rel_path).resolve()

    # Seguridad: evitar path traversal
    if not str(file_path).startswith(str(OUT_DIR)) or not file_path.exists():
        raise HTTPException(404, "Archivo no encontrado")

    # Detectar tipo MIME básico
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        media_type = "application/pdf"
    elif ext == ".docx":
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        media_type = "application/octet-stream"

    # inline para que se abra en el navegador si puede
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=file_path.name
    )

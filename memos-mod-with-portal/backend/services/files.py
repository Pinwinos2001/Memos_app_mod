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

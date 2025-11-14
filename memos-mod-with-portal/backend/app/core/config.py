from dotenv import load_dotenv
import os
from pathlib import Path

def parse_emails(env_value: str | None) -> list[str]:
    if not env_value:
        return []
    return [e.strip() for e in env_value.split(",") if e.strip()]

load_dotenv()

# ================================
# 1 — ÚNICA VARIABLE DE ENTORNO
# ================================
APP_ENV = os.getenv("APP_ENV", "test").lower()   # test por defecto (seguro)

# ================================
# 2 — RUTAS BASE DEL PROYECTO
# ================================
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

TEMPLATES_DIR = PROJECT_ROOT / "templates"
STATIC_DIR    = PROJECT_ROOT / "static"

# ================================
# 3 — BASE DE DATOS SEGÚN ENTORNO
# ================================
if APP_ENV == "prod":
    DB_FILENAME = "memos-prod.db"
else:
    DB_FILENAME = "memos.db"

DB_PATH = PROJECT_ROOT / "data" /DB_FILENAME

# ================================
# 4 — CARPETAS DE SALIDA out/prod o out/test
# ================================
OUT_ROOT = PROJECT_ROOT / "out"

if APP_ENV == "prod":
    OUT_DIR = OUT_ROOT / "prod"
else:
    OUT_DIR = OUT_ROOT / "test"


OUT_DIR.mkdir(parents=True, exist_ok=True)

TEMPLATE_PATH = TEMPLATES_DIR / "memo_formato.docx"

BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")
BACK_URL = os.getenv("BACK_URL", "http://localhost:8000")

LEGAL_MAILS = parse_emails(os.getenv("LEGAL_MAILS"))
RRHH_MAILS  = parse_emails(os.getenv("RRHH_MAILS"))

AUTH_SECRET = os.getenv("AUTH_SECRET", "dev-secret-change-me")
LEGAL_KEY   = os.getenv("LEGAL_KEY", "legal123")
RRHH_KEY    = os.getenv("RRHH_KEY", "rrhh123")
DASH_KEY    = os.getenv("DASH_KEY", "dash123")

DEBUG = os.getenv("DEBUG", "0") == "1"
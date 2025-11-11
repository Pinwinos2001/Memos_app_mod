from dotenv import load_dotenv
import os
from pathlib import Path

def parse_emails(env_value: str | None) -> list[str]:
    if not env_value:
        return []
    return [e.strip() for e in env_value.split(",") if e.strip()]

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
OUT_DIR = BASE_DIR / "out"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = PROJECT_ROOT / "memos.db"
TEMPLATE_PATH = TEMPLATES_DIR / "memo_formato.docx"

# URLs públicas
BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")      # frontend
BACK_URL = os.getenv("BACK_URL", "http://localhost:8000")      # backend (si lo necesitas)

LEGAL_MAILS = parse_emails(os.getenv("LEGAL_MAILS"))
RRHH_MAILS = parse_emails(os.getenv("RRHH_MAILS"))

# Auth
AUTH_SECRET = os.getenv("AUTH_SECRET", "dev-secret-change-me")
LEGAL_KEY   = os.getenv("LEGAL_KEY", "legal123")
RRHH_KEY    = os.getenv("RRHH_KEY", "rrhh123")
DASH_KEY    = os.getenv("DASH_KEY", "dash123")

DEBUG = os.getenv("DEBUG", "0") == "1"

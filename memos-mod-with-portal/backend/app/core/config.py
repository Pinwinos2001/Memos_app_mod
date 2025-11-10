import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

# Folders
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
OUT_DIR = BASE_DIR / "out"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = PROJECT_ROOT / "memos.db"
TEMPLATE_PATH = TEMPLATES_DIR / "memo_formato.docx"

# Environment
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8080")
BACK_URL = os.getenv("BACK_URL", "http://127.0.0.1:8000")
RRHH_JEFE_EMAIL   = os.getenv("RRHH_JEFE_EMAIL", "")
RRHH_EQUIPO_EMAIL = os.getenv("RRHH_EQUIPO_EMAIL", "")
LEGAL_JEFE_EMAIL  = os.getenv("LEGAL_JEFE_EMAIL", "")
LEGAL_EQUIPO_EMAIL= os.getenv("LEGAL_EQUIPO_EMAIL", "")
RRHH_EMAIL  = os.getenv("RRHH_EMAIL", "")
LEGAL_EMAIL = os.getenv("LEGAL_EMAIL", "")

DEBUG = os.getenv("DEBUG","0") == "1"

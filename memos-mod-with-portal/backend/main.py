from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .api.public import router as public_router
from .api.memos import router as memos_router
from .api.review import router as review_router
from .api.pages import router as pages_router
from .api.auth import router as auth_router
from .services.files import router as files_router
from .core.config import STATIC_DIR
from .services.db import db_init

app = FastAPI(title="Memos RRHH – API (modular)")

# CORS for decoupled frontend (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(public_router)
app.include_router(memos_router)
app.include_router(review_router)
app.include_router(files_router)
app.include_router(pages_router)
app.include_router(auth_router)

# Static hosting
FRONT_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(FRONT_DIR), html=True), name="frontend")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Ensure DB exists on startup
@app.on_event("startup")
def _startup():
    db_init()

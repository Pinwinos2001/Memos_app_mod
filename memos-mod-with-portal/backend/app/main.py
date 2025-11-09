from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .api.public import router as public_router
from .api.memos import router as memos_router
from .api.review import router as review_router
from .api.auth import router as auth_router
from .services.files import router as files_router
from .core.config import STATIC_DIR
from .services.db import db_init

API_PREFIX = "/api"

app = FastAPI(title="Memos RRHH – API (modular)")

ALLOWED_ORIGINS = [
    "*"
    # agrega aquí tu dominio real de frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(public_router, prefix=f"{API_PREFIX}/public", tags=["public"])
app.include_router(memos_router, prefix=f"{API_PREFIX}/memos", tags=["memos"])
app.include_router(review_router, prefix=f"{API_PREFIX}/review", tags=["review"])
app.include_router(files_router, prefix=f"{API_PREFIX}/files", tags=["files"])
app.include_router(auth_router, prefix=f"{API_PREFIX}/auth", tags=["auth"])

@app.get(f"{API_PREFIX}/health", tags=["health"])
async def health():
    return {"status": "ok"}

if STATIC_DIR:
    static_path = Path(str(STATIC_DIR))
    if static_path.is_dir():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

@app.on_event("startup")
def on_startup():
    db_init()
    print("Base de datos inicializada.")
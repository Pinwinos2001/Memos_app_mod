from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import time, hmac, hashlib
from typing import List, Tuple

router = APIRouter()

AUTH_SECRET = os.getenv("AUTH_SECRET", "dev-secret-change-me")
LEGAL_KEY = os.getenv("LEGAL_KEY", "nokey")
RRHH_KEY  = os.getenv("RRHH_KEY", "nokey")
DASH_KEY  = os.getenv("DASH_KEY", "nokey")

ROLE_TO_KEY = {"legal": LEGAL_KEY, "rrhh": RRHH_KEY, "dash": DASH_KEY}


def _sign(data: str) -> str:
    return hmac.new(AUTH_SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()


def make_token(role: str, minutes: int = 240) -> str:
    exp = int(time.time() + minutes * 60)
    payload = f"{role}|{exp}"
    sig = _sign(payload)
    return f"{payload}|{sig}"


def verify_token(token: str, allowed_roles: List[str]) -> Tuple[str, int]:
    try:
        role, exp_s, sig = token.split("|", 2)
        exp = int(exp_s)
    except Exception:
        raise HTTPException(401, "Token inválido")

    if role not in allowed_roles:
        raise HTTPException(403, "Rol no autorizado")

    payload = f"{role}|{exp}"
    if not hmac.compare_digest(sig, _sign(payload)):
        raise HTTPException(401, "Firma inválida")

    if exp < int(time.time()):
        raise HTTPException(401, "Token expirado")

    return role, exp


class LoginBody(BaseModel):
    role: str
    key: str


@router.post("/login")
def key_login(body: LoginBody):
    role = (body.role or "").lower()

    if role not in ROLE_TO_KEY:
        raise HTTPException(400, "Rol inválido")

    expected = ROLE_TO_KEY[role]
    if not expected or body.key != expected:
        raise HTTPException(401, "Clave incorrecta")

    token = make_token(role)

    return {
        "ok": True,
        "token": token,
        "role": role,
    }


def require_auth(auth_header: str | None, allowed_roles: List[str]):
    if not auth_header:
        raise HTTPException(401, "Falta Authorization")

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(401, "Formato de Authorization inválido")

    token = parts[1]
    return verify_token(token, allowed_roles)

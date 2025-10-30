from fastapi import APIRouter, Query
from ..services.memo import INCISOS_VENTAS, previos_from_db, tipo_por_historial

router = APIRouter()

@router.get("/incisos_json")
def incisos_json():
    return INCISOS_VENTAS

@router.get("/lookup_json")
def lookup_json(dni: str = Query(..., min_length=8, max_length=8)):
    prev = previos_from_db(dni)
    orden = min(prev + 1, 3)
    tipo = tipo_por_historial(prev)
    return {"previos": prev, "orden": orden, "tipo": tipo}
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Set
from ..services.db import db_one

# Business constants & helpers

FERIADOS: Set[str] = set()  # If you want, populate 'YYYY-MM-DD' dates

INCISOS_VENTAS: List[Dict[str, Any]] = [
    
    {"id": 1,
        "titulo": "Honestidad y buena fe",
        "ejemplos": [
            "Registró visitas en clientes inexistentes.",
            "Reportó ventas/pedidos que nunca ocurrieron.",
            "Colocó o declaró punto de venta en su domicilio."
        ]
    },
    {
        "id": 2,
        "titulo": "Obedecer órdenes e instrucciones",
        "ejemplos": [
            "No siguió la ruta asignada.",
            "No cumplió los Indicadores de Disciplina Operativa (IDO).",
            "No entregó material promocional pese a la orden."
        ]
    },
    {
        "id": 3,
        "titulo": "Desempeño con responsabilidad",
        "ejemplos": [
            "Reutilizó fotos de exhibición para varios clientes.",
            "Realizó un compromiso con el cliente sin autorización del jefe.",
            "Envío de reportes incompletos de la ruta."
        ]
    },
    {
        "id": 5,
        "titulo": "Cuidado de bienes de la empresa",
        "ejemplos": [
            "Uso no autorizado del celular/línea corporativa.",
            "Pérdida o mal uso de materiales de trade.",
            "Prestar herramientas a terceros sin permiso."
        ]
    },
    {
        "id": 10,
        "titulo": "Conducta en los negocios",
        "ejemplos": [
            "Cliente reporta pedido que nunca hizo.",
            "Cobro indebido o beneficio personal con cliente.",
            "Negociación fuera de políticas comerciales."
        ]
    },
    {
        "id": 12,
        "titulo": "Respeto y consideración",
        "ejemplos": [
            "Trato irrespetuoso a bodeguero/cliente.",
            "Comentarios despectivos en punto de venta.",
            "Discusión agresiva con compañero de ruta."
        ]
    },
    {
        "id": 18,
        "titulo": "Puntualidad",
        "ejemplos": [
            "Retraso frecuente en el inicio de ruta.",
            "Llegó fuera de los minutos de tolerancia (15 minutos) a la matinal.",
            "Ausencia parcial sin aviso durante la jornada."
        ]
    }
]

INCISO_TEXTO = {
    1: "Actuar con honestidad, lealtad, fidelidad, diligencia y buena fe en todas las labores e instrucciones del jefe inmediato.",
    2: "Obedecer órdenes e instrucciones referidas a sus labores y acatar las disposiciones de sus superiores jerárquicos.",
    3: "Desempeñar sus funciones con dedicación y responsabilidad procurando eficiencia y eficacia.",
    5: "Cautelar y responder por el uso de los bienes de la empresa asignados a su cargo.",
    9: "Cumplir con las normas de asistencia y registro de ingresos y salidas; reportar incidencias oportunamente.",
    10:"Cumplir con los estándares de conducta en los negocios de la empresa.",
    12:"Guardar respeto y consideración a jefes, compañeros, clientes y terceros.",
    18:"Presentarse a tiempo y cumplir con los horarios y turnos establecidos por la empresa."
}

def validar_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email or "") is not None

def es_email_heineken(email: str) -> bool:
    dominios = ['@heineken.com', '@heinekeninternational.com']
    return any((email or "").lower().endswith(dom) for dom in dominios)

def sanitizar_texto(texto: str) -> str:
    import html
    if not texto:
        return ""
    texto = html.escape(texto)
    return " ".join(texto.split()).strip()

def validar_dni(dni: str) -> bool:
    return re.match(r'^\d{8}$', dni or "") is not None

def business_days_from(start: datetime, days: int) -> datetime:
    d = start
    added = 0
    while added < days:
        d += timedelta(days=1)
        if d.weekday() < 5 and d.strftime("%Y-%m-%d") not in FERIADOS:
            added += 1
    return d

def next_running_number(prefix: str) -> str:
    year = datetime.now().year
    row = db_one("SELECT COUNT(*) FROM memos WHERE created_at LIKE ?", (f"{year}%",))
    n = (row[0] if row else 0) + 1
    return f"{prefix}-{year}-{n:04d}"

def previos_from_db(dni: str) -> int:
    row = db_one("SELECT COUNT(*) FROM memos WHERE dni=?", (dni,))
    return int(row[0] if row else 0)

def tipo_por_historial(previos: int) -> str:
    orden = min(int(previos) + 1, 3)
    return ["Llamado de atención formal", "Licencia sin goce (1 día)", "Despido"][orden-1]
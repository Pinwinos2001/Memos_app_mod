# Memos RRHH — Separación Backend / Frontend

## Estructura
```
backend/
  core/ (config & compat)
  services/ (db, memo rules, docs, mail, files)
  api/ (public, memos, review, pages)
  static/ (assets que sirve el backend)
  templates/ (memo_formato.docx)
  out/ (archivos generados)
frontend/
  form/, edit/, dashboard/, legal/, rrhh/, result/ + assets/
memos.db (se crea al correr)
```

## Correr (dev)
1) Crear entorno + instalar dependencias:
```
pip install fastapi uvicorn python-dotenv python-docx docx2pdf
```
2) Exportar variables opcionales en `.env` (ver `backend/core/config.py`).
3) Ejecutar:
```
uvicorn backend.main:app --reload
```
4) Abrir: http://127.0.0.1:8000

> **Nota:** Coloca tu plantilla `memo_formato.docx` en `backend/templates/`. Si no está o `python-docx` no está instalado, se generará un `.txt` de placeholder.

## Endpoints principales
- `GET /incisos_json`
- `GET /lookup_json?dni=...`
- `POST /submit` (multipart)
- `POST /update/{id}` (multipart)
- `POST /legal_approve`
- `POST /approve`
- `GET /api/memo/{id}`
- `GET /api/memos`
- `GET /api/metrics`
- `GET /file?path=...` (restringido a `backend/out/`)

## Frontend
El frontend es 100% estático y usa `fetch` contra los endpoints anteriores. Las rutas HTML están bajo `/form/`, `/edit/`, `/dashboard/`, `/legal/`, `/rrhh/`, `/result/`.

## Acceso con clave (sin usuarios)
- Claves por rol vía variables de entorno: `LEGAL_KEY`, `RRHH_KEY`, `DASH_KEY`.  
- Se emite un token firmado (HMAC) con `AUTH_SECRET` usando `/auth/login`.
- Frontend guarda el token en `sessionStorage` y lo envía en `Authorization: Bearer <token>`.
- Páginas protegidas:
  - **Dashboard** (`/dashboard`): rol `dash`.
  - **Revisión Legal** (`/legal/review.html?id=...`): rol `legal`.
  - **Revisión RRHH** (`/rrhh/review.html?id=...`): rol `rrhh`.
- Portal central en `/portal/` con tarjetas para cada sección.
// __AUTH_INJECTED__
(function () {
  const role = 'legal';
  const token = sessionStorage.getItem('memo_token_' + role);
  if (!token) {
    const here = encodeURIComponent(location.href);
    location.href = `/apps/memos/auth/key.html?role=${role}&next=${here}`;
  } else {
    window.__AUTH_TOKEN__ = token;
  }
})();

const API_BASE = window.APP_CONFIG?.API_BASE_URL || "";

async function authFetch(url, options) {
  options = options || {};
  options.headers = Object.assign({}, options.headers || {}, {
    'Authorization': 'Bearer ' + (window.__AUTH_TOKEN__ || '')
  });
  return fetch(url, options);
}

function qs(k) { return new URLSearchParams(location.search).get(k); }

const id        = qs('id');
const memoDiv   = document.getElementById('memo');
const downloads = document.getElementById('downloads');
const form      = document.getElementById('legalForm');

// Asegura que el hidden "id" tenga valor
if (form && id) {
  const hid = form.querySelector('input[name="id"]');
  if (hid) hid.value = id;
}

async function load() {
  if (!id) {
    memoDiv.textContent = "Falta id";
    if (form) form.style.display = "none";
    return;
  }

  const r = await authFetch(`${API_BASE}/api/memos/${encodeURIComponent(id)}`);
  if (!r.ok) {
    memoDiv.textContent = "No encontrado";
    if (form) form.style.display = "none";
    return;
  }

  const d = await r.json();

  const estado = d.estado || "-";
  const legalAprobado = (d.legal_aprobado || "").trim().toUpperCase();

  // Info principal
  memoDiv.innerHTML = `
    <p><b>${d.nombre || "-"}</b> (DNI ${d.dni || "-"}) — ${d.area || ""} / ${
    d.cargo || ""
  }</p>
    <p><b>Tipo:</b> ${d.tipo || "-"}<br>
       <b>Inciso:</b> ${d.inciso_num || "-"} — ${d.inciso_texto || ""}</p>
    <p><b>Hechos:</b> ${d.hecho_que || "-"}<br>
       <b>Cuándo:</b> ${d.hecho_cuando || "-"} &nbsp;|&nbsp; <b>Dónde:</b> ${
    d.hecho_donde || "-"
  }</p>
    <p><b>Estado actual:</b> ${estado}</p>
  `;

  // Botón de descarga PDF (siempre que exista archivo en backend)
  downloads.innerHTML = `
    <button id="btnDownloadPDF" class="btn btn-outline">Descargar PDF</button>
    <button id="btnBack" class="btn btn-muted">Volver al inicio</button>
  `;
  document
    .getElementById("btnDownloadPDF")
    .addEventListener("click", () => downloadPDF(id, d.memo_id));

  document.getElementById("btnBack").addEventListener("click", () => goPortal());

  // ---- CONTROL DE DOBLE APROBACIÓN ----
  // Solo se permite aprobar/observar si:
  // - Estado es exactamente "En revisión Legal"
  // - Y Legal aún no marcó APROBADO/OBSERVADO
  const canReview =
    estado === "En revisión Legal";

  if (!canReview) {
    // Deshabilitar el formulario de decisiones
    if (form) {
      form.style.display = "none";
    }

    // Mensaje informativo para que el usuario sepa por qué
    const msg = document.createElement("div");
    msg.className = "alert-info";
    msg.style.marginTop = "16px";
    msg.style.padding = "10px 12px";
    msg.style.borderRadius = "6px";
    msg.style.background = "#f1f5f9";
    msg.style.color = "#0f172a";
    msg.textContent = `Este memo ya fue procesado por Legal. Estado actual: ${estado}. No es posible registrar otra decisión.`;

    memoDiv.appendChild(msg);
  }
}

// Redirección uniforme al Portal (y notificación al listado si está abierto)
function goPortal(nextUrlFromServer) {
  try { if (window.opener) window.opener.postMessage({ t: 'memos:refresh' }, '*'); } catch (e) {}
  const next = '/apps/memos/portal/';
  location.replace(next); // evita volver con "Atrás"
}

async function downloadPDF(memoId, memoCode = "documento") {
  const url = `${API_BASE}/api/files/memo_file/${encodeURIComponent(memoId)}`;

  try {
    const resp = await fetch(url, { method: "GET" });
    if (!resp.ok) {
      alert("No se pudo obtener el documento. Código: " + resp.status);
      return;
    }

    // Convertir a blob y forzar descarga con nombre
    const blob = await resp.blob();
    const blobUrl = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = blobUrl;
    a.download = `${memoCode}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();

    setTimeout(() => URL.revokeObjectURL(blobUrl), 60000);
  } catch (err) {
    console.error("Error al descargar PDF:", err);
    alert("Ocurrió un error al intentar descargar el documento.");
  }
}

// Envío del form: usa el botón que disparó el submit para setear 'decision'
if (form) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Qué botón disparó el submit (APROBAR / OBSERVAR)
    const submitter = e.submitter; // <button name="decision" value="...">
    const decision = (submitter && submitter.name === 'decision')
      ? (submitter.value || 'APROBAR')
      : 'APROBAR';

    const fd = new FormData(form);
    // asegura que 'decision' viaje aunque FormData no incluya el submitter
    fd.set('decision', decision);

    // (Opcional) si observa sin comentario, pedir confirmación
    if (decision === 'OBSERVAR') {
      const txt = (fd.get('comentario') || '').trim();
      if (!txt) {
        const ok = confirm('Estás observando sin comentario. ¿Deseas continuar?');
        if (!ok) return;
      }
    }

    try {
      const r = await authFetch(
        `${API_BASE}/api/review/legal_approve`,
        { method: "POST", body: fd }
      );
      const d = await r.json().catch(() => ({}));
      if (r.ok && d && d.ok) {
        goPortal(d.next_url);
      } else {
        // si backend dice que ya no se puede, también mandamos al portal
        alert(d?.detail || "No fue posible registrar la decisión.");
        goPortal(d && d.next_url);
      }
    } catch (err) {
      console.error(err);
      goPortal();
    }
  });
}

load();

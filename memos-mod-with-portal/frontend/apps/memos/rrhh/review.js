// __AUTH_INJECTED__
(function () {
  const role = 'rrhh';
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

const id = qs('id');
const memoDiv = document.getElementById('memo');
const downloads = document.getElementById('downloads');
const form = document.getElementById('rrhhForm');

if (form && id) {
  const hid = form.querySelector('input[name="id"]');
  if (hid) hid.value = id;
}

async function load() {

  if (!id) { memoDiv.textContent = 'Falta id'; return; }
  const r = await authFetch(`${API_BASE}/api/memos/` + encodeURIComponent(id));
  if (!r.ok) { memoDiv.textContent = 'No encontrado'; return; }

  const d = await r.json();

  const estado = d.estado || "-";

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

  // Solo muestra el botón si existe el PDF en BD
  downloads.innerHTML = `
    <button id="btnDownloadPDF" class="btn btn-outline">Descargar PDF</button>
    <button id="btnBack" class="btn btn-muted">Volver al inicio</button>
  `;
  document
    .getElementById("btnDownloadPDF")
    .addEventListener("click", () => downloadPDF(id, d.memo_id));
  document.getElementById("btnBack").addEventListener("click", () => goPortal());

  const canReview =
    estado === "Aprobado Legal - Pendiente RRHH";

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
    msg.textContent = `Este memo ya fue procesado por RRHH. Estado actual: ${estado}. No es posible registrar otra decisión.`;

    memoDiv.appendChild(msg);
  }
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

function goPortal(nextUrlFromServer) {
  try { if (window.opener) window.opener.postMessage({ t: 'memos:refresh' }, '*'); } catch (e) {}
  const next = '/apps/memos/portal/';
  location.replace(next);
}

if (form) {
  form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const submitter = e.submitter;
  const decision =
    submitter && submitter.name === "decision"
      ? submitter.value || "APROBAR"
      : "APROBAR";

  const fd = new FormData(form);

  // Aseguramos que viaje 'decision'
  fd.set("decision", decision);

  // Aseguramos que viaje 'id'
  if (!fd.get("id") && idFromUrl) {
    fd.set("id", idFromUrl);
  }

  const resp = await authFetch(`${API_BASE}/api/review/approve`, {
    method: "POST",
    body: fd, // 👈 Esto genera multipart/form-data, perfecto para Form(...)
  });

  const data = await resp.json().catch(() => ({}));

  if (resp.ok && data.ok) {
    goPortal(data.next_url);
  } else {
    console.error("Error approve:", data);
    alert("No se pudo procesar la aprobación.");
  }
});
}

load();


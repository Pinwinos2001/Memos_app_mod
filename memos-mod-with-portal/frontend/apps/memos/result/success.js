// Función para obtener parámetros de la URL
function qs(k) {
  return new URLSearchParams(location.search).get(k);
}

// Asignar datos básicos
document.getElementById("chipMemo").textContent = qs("memo_id") || "—";
document.getElementById("chipCorr").textContent = qs("corr_id") || "—";
document.getElementById("email").textContent = qs("email") || "—";

const API_BASE = window.APP_CONFIG?.API_BASE_URL || "";

// Obtener el ID del memo desde la URL (?pdf=id)
const memoId = qs("pdf");
const btn = document.getElementById("aPDF");

if (!memoId) {
  // Si no hay ID, ocultamos botón y mostramos aviso
  btn.style.display = "none";
  const actions = document.querySelector(".actions");
  if (actions) {
    const msg = document.createElement("p");
    msg.textContent = "El documento aún no está disponible para descarga.";
    msg.style.opacity = "0.7";
    msg.style.marginTop = "8px";
    actions.appendChild(msg);
  }
} else {
  btn.addEventListener("click", async (e) => {
    e.preventDefault();

    const pdfUrl = `${API_BASE}/api/files/memo_file/${memoId}`;

    try {
      const resp = await fetch(pdfUrl, { method: "GET" });

      if (!resp.ok) {
        alert("No se pudo obtener el documento. Código: " + resp.status);
        return;
      }

      // Convertir a blob y abrir en nueva pestaña
      const blob = await resp.blob();
      const blobUrl = URL.createObjectURL(blob);

      // Crear enlace temporal para descarga con nombre personalizado
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = `${qs("memo_id") || "documento"}.pdf`; // usa memo_id como nombre de archivo
      document.body.appendChild(a);
      a.click();
      a.remove();

      // Liberar memoria
      setTimeout(() => URL.revokeObjectURL(blobUrl), 60000);
    } catch (err) {
      console.error("Error al descargar/ver el PDF:", err);
      alert("Ocurrió un error al intentar abrir el documento.");
    }
  });
}

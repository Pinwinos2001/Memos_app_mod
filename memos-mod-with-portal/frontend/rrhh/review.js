// __AUTH_INJECTED__
(function () {
  const role = 'rrhh';
  const token = sessionStorage.getItem('memo_token_' + role);
  if (!token) {
    const here = encodeURIComponent(location.href);
    location.href = `/auth/key.html?role=${role}&next=${here}`;
  } else {
    window.__AUTH_TOKEN__ = token;
  }
})();

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
const form      = document.getElementById('rrhhForm');

// Asegura que el hidden "id" tenga valor
if (form && id) {
  const hid = form.querySelector('input[name="id"]');
  if (hid) hid.value = id;
}

async function load() {
  if (!id) { memoDiv.textContent = 'Falta id'; return; }
  const r = await authFetch('/api/memo/' + encodeURIComponent(id));
  if (!r.ok) { memoDiv.textContent = 'No encontrado'; return; }
  const d = await r.json();
  
  memoDiv.innerHTML = `
    <p><b>${d.nombre || '-'}</b> (DNI ${d.dni || '-'}) — ${d.area || ''} / ${d.cargo || ''}</p>
    <p><b>Tipo:</b> ${d.tipo || '-'}<br>
       <b>Inciso:</b> ${d.inciso_num || '-'} — ${d.inciso_texto || ''}</p>
    <p><b>Hechos:</b> ${d.hecho_que || '-'}<br>
       <b>Cuándo:</b> ${d.hecho_cuando || '-'} &nbsp;|&nbsp; <b>Dónde:</b> ${d.hecho_donde || '-'}</p>
  `;
  
  const docx = d.docx_path ? `/file?path=${encodeURIComponent(d.docx_path)}` : '';
  const pdf  = d.pdf_path  ? `/file?path=${encodeURIComponent(d.pdf_path)}`  : '';
  downloads.innerHTML =
    (docx ? `<a href="${docx}" target="_blank">Word: descargar</a>` : '') +
    (pdf  ? ` &nbsp;|&nbsp; <a href="${pdf}" target="_blank">PDF: descargar</a>` : '');
}

// Redirige al portal y avisa al listado para refrescarse
function goPortal(nextUrlFromServer) {
  try { if (window.opener) window.opener.postMessage({ t: 'memos:refresh' }, '*'); } catch (e) {}
  const next = nextUrlFromServer || '/portal/index.html';
  location.replace(next);
}

// Envío del form usando el botón submitter para fijar 'decision'
if (form) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Qué botón disparó el submit (APROBAR / OBSERVAR)
    const submitter = e.submitter;
    const decision = (submitter && submitter.name === 'decision')
      ? (submitter.value || 'APROBAR')
      : 'APROBAR';
    
    const fd = new FormData(form);
    fd.set('decision', decision);
    
    // (Opcional) confirmación si observas sin comentario
    if (decision === 'OBSERVAR') {
      const txt = (fd.get('comentario') || '').trim();
      if (!txt) {
        const ok = confirm('Estás observando sin comentario. ¿Deseas continuar?');
        if (!ok) return;
      }
    }
    
    // MOSTRAR LOADER con mensaje según decisión
    if(window.HnkLoader) {
      const msg = decision === 'APROBAR' 
        ? 'Emitiendo memo...' 
        : 'Registrando observación...';
      const sub = decision === 'APROBAR'
        ? 'Actualizando sistema y notificando'
        : 'Notificando al solicitante y Legal';
      HnkLoader.show(msg, sub);
    }
    
    try {
      const r = await authFetch('/approve', { method: 'POST', body: fd }); // endpoint de RRHH
      const d = await r.json().catch(() => ({}));
      
      if (r.ok && d && d.ok) {
        // Éxito - el loader se ocultará cuando redirija
        goPortal(d.next_url);
      } else {
        // Error del servidor
        if(window.HnkLoader) HnkLoader.hide();
        alert('Hubo un problema al procesar la decisión. Serás redirigido al portal.');
        goPortal(d && d.next_url);
      }
    } catch (err) {
      // Error de red
      if(window.HnkLoader) HnkLoader.hide();
      console.error(err);
      alert('Error de conexión. Serás redirigido al portal.');
      goPortal();
    }
  });
}

load();
//__AUTH_INJECTED__
(function(){
  const role = 'legal';
  const token = sessionStorage.getItem('memo_token_'+role);
  if(!token){
    const here = encodeURIComponent(location.href);
    location.href = `/auth/key.html?role=${role}&next=${here}`;
  } else {
    window.__AUTH_TOKEN__ = token;
  }
})();

async function authFetch(url, options){
  options = options || {};
  options.headers = Object.assign({}, options.headers||{}, { 'Authorization':'Bearer '+(window.__AUTH_TOKEN__||'') });
  return fetch(url, options);
}
function qs(k){ return new URLSearchParams(location.search).get(k); }
const id = qs('id');
const memoDiv = document.getElementById('memo');
const downloads = document.getElementById('downloads');
const form = document.getElementById('legalForm');
form.querySelector('input[name="id"]').value = id;

async function load(){
  if(!id){ memoDiv.textContent = 'Falta id'; return; }
  const r = await authFetch('/api/memo/'+encodeURIComponent(id));
  if(!r.ok){ memoDiv.textContent='No encontrado'; return; }
  const d = await r.json();
  memoDiv.innerHTML = `<p><b>${d.nombre}</b> (DNI ${d.dni}) - ${d.area||''} / ${d.cargo||''}</p>
    <p><b>Tipo:</b> ${d.tipo} <br><b>Inciso:</b> ${d.inciso_num} — ${d.inciso_texto||''}</p>
    <p><b>Hechos:</b> ${d.hecho_que||'-'}<br><b>Cuándo:</b> ${d.hecho_cuando||'-'} &nbsp;|&nbsp; <b>Dónde:</b> ${d.hecho_donde||'-'}</p>`;
  const docx = d.docx_path ? `/file?path=${encodeURIComponent(d.docx_path)}` : '';
  const pdf = d.pdf_path ? `/file?path=${encodeURIComponent(d.pdf_path)}` : '';
  downloads.innerHTML = (docx?`<a href="${docx}" target="_blank">Word: descargar</a>`:'') + (pdf?` &nbsp;|&nbsp; <a href="${pdf}" target="_blank">PDF: descargar</a>`:'')
}
form.addEventListener('submit', async (e)=>{
  e.preventDefault();
  const fd = new FormData(form);
  const r = await authFetch('/legal_approve', { method:'POST', body: fd });
  const d = await r.json();
  if(d && d.ok){ alert('Guardado: '+d.status); location.href = '/dashboard/index.html'; }
  else{ alert('Guardado.'); location.href = '/dashboard/index.html'; }
});
load();

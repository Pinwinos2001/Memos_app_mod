async function cargarIncisos(){
  const r = await fetch('/incisos_json');
  const data = await r.json();
  const sel = document.getElementById('inciso_select');
  const current = sel.dataset.current || '';
  sel.innerHTML = '';
  data.forEach(it=>{
    const opt = document.createElement('option');
    opt.value = it.id;
    opt.textContent = `Inciso ${it.id} — ${it.titulo}`;
    opt.dataset.examples = JSON.stringify(it.ejemplos||[]);
    if(String(it.id) === current) opt.selected = true;
    sel.appendChild(opt);
  });
  sel.dispatchEvent(new Event('change'));
}
document.addEventListener('change', e=>{
  if(e.target && e.target.id === 'inciso_select'){
    const opt = e.target.selectedOptions[0];
    const examples = JSON.parse(opt.dataset.examples || '[]');
    const box = document.getElementById('inciso_examples');
    const ul = document.getElementById('ex_ul');
    ul.innerHTML = '';
    examples.forEach(t=>{ const li=document.createElement('li'); li.textContent=t; ul.appendChild(li); });
    box.style.display = examples.length ? 'block' : 'none';
  }
});

function qs(key){ return new URLSearchParams(location.search).get(key); }
const id = qs('id');
const form = document.getElementById('editForm');
const info = document.getElementById('dni_info');
const dniInput = form.querySelector('input[name="dni"]');

async function loadMemo(){
  if(!id){ alert('Falta id'); return; }
  const r = await fetch('/api/memo/'+encodeURIComponent(id));
  if(!r.ok){ alert('No encontrado'); return; }
  const d = await r.json();
  for(const k of ['solicitante_email','area_sol','dni','nombre','area','cargo','jefe_email','hecho_que','hecho_cuando','hecho_donde']){
    const el = form.querySelector(`[name="${k}"]`); if(el) el.value = d[k] || '';
  }
  form.querySelector('[name="equipo"]').value = d.equipo || '';
  document.getElementById('inciso_select').dataset.current = d.inciso_num || '';
  await cargarIncisos();
}
async function checkDNI(){
  const v = (dniInput.value||'').trim();
  if(/^\d{8}$/.test(v)){
    try{
      const r = await fetch('/lookup_json?dni='+v);
      const d = await r.json();
      info.textContent = `Historial: ${d.previos} previo(s) – Orden #${d.orden} (${d.tipo})`;
    }catch{ info.textContent=''; }
  }else{ info.textContent=''; }
}
dniInput.addEventListener('input', checkDNI);
dniInput.addEventListener('blur', checkDNI);

form.addEventListener('submit', async (e)=>{
  e.preventDefault();
  const fd = new FormData(form);
  const r = await fetch('/update/'+encodeURIComponent(id), { method:'POST', body: fd });
  const d = await r.json();
  if(d && d.ok && d.review_url){
    location.href = d.review_url;
  }else{
    alert('Actualizado. Si no te redirige, revisa el dashboard.');
  }
});

window.addEventListener('DOMContentLoaded', loadMemo);
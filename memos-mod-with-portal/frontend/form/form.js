async function cargarIncisos(){
  const r = await fetch('/incisos_json');
  const data = await r.json();
  const sel = document.getElementById('inciso_select');
  sel.innerHTML = '';
  data.forEach(it=>{
    const opt = document.createElement('option');
    opt.value = it.id;
    opt.textContent = `Inciso ${it.id} — ${it.titulo}`;
    opt.dataset.examples = JSON.stringify(it.ejemplos||[]);
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
    examples.forEach(t=>{
      const li = document.createElement('li'); li.textContent = t; ul.appendChild(li);
    });
    box.style.display = examples.length ? 'block' : 'none';
  }
});

const form = document.getElementById('memoForm');
const submitBtn = document.getElementById('submitBtn');
const progressFill = document.getElementById('progressFill');
const info = document.getElementById('dni_info');
const dniInput = form.querySelector('input[name="dni"]');

async function checkDNI(){
  const v = (dniInput.value||'').trim();
  if(/^\d{8}$/.test(v)){
    try{
      const r = await fetch('/lookup_json?dni='+v);
      const d = await r.json();
      info.innerHTML = `Historial: <b>${d.previos}</b> previo(s) <span class="legend-status">Orden #${d.orden} – ${d.tipo}</span>`;
    }catch{ info.textContent=''; }
  }else{ info.textContent=''; }
}
dniInput.addEventListener('input', checkDNI);
dniInput.addEventListener('blur', checkDNI);

const sections = {
  A: ['[name="solicitante_email"]','[name="area_sol"]'],
  B: ['[name="dni"]','[name="nombre"]','[name="equipo"]','[name="jefe_email"]'],
  C: ['#inciso_select'],
  D: ['[name="hecho_que"]','[name="hecho_cuando"]']
};
const statusEls = {
  A: document.getElementById('statusA'),
  B: document.getElementById('statusB'),
  C: document.getElementById('statusC'),
  D: document.getElementById('statusD')
};
function pct(v,t){ return Math.round((v/Math.max(t,1))*100); }
function computeProgress(){
  const allReq = [...form.querySelectorAll('[required]')];
  let validCount = 0;
  allReq.forEach(el=>{
    if(el.type==='file') return;
    if(el.checkValidity() && (el.value||'').toString().trim()!=='') validCount++;
  });
  const globalPct = pct(validCount, allReq.length);
  progressFill.style.width = globalPct + '%';
  submitBtn.disabled = !form.checkValidity();
  Object.entries(sections).forEach(([key, sels])=>{
    let t=0,v=0;
    sels.forEach(sel=>{
      const el = form.querySelector(sel); if(!el) return;
      t++;
      if(el.checkValidity() && (el.value||'').toString().trim()!=='') v++;
    });
    const p = pct(v,t);
    if(statusEls[key]) statusEls[key].textContent = p + '%';
  });
}
form.addEventListener('input', computeProgress);
form.addEventListener('change', computeProgress);

form.addEventListener('submit', async (e)=>{
  e.preventDefault();
  submitBtn.disabled = true;
  const fd = new FormData(form);
  const r = await fetch('/submit', { method: 'POST', body: fd });
  const data = await r.json();
  if(data && data.success_url){
    window.location.href = data.success_url;
  }else if(data && data.ok){
    window.location.href = `/result/success.html?memo_id=${encodeURIComponent(data.memo_id)}&corr_id=${encodeURIComponent(data.corr_id)}&email=${encodeURIComponent(fd.get('solicitante_email')||'')}&pdf=${encodeURIComponent(data.pdf_url||'')}`;
  }else{
    alert('Enviado. Si no te redirige, revisa el correo de confirmación.');
  }
});

window.addEventListener('DOMContentLoaded', async ()=>{
  await cargarIncisos();
  computeProgress();
});
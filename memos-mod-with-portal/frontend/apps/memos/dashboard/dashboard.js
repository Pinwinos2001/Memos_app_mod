//__AUTH_INJECTED__
(function(){
  const role = 'dash';
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
let memosData = [];
let metricsData = {};

function $(sel){ return document.querySelector(sel); }
function $all(sel){ return [...document.querySelectorAll(sel)]; }

$all('.tab').forEach(btn=>{
  btn.addEventListener('click',()=>{
    $all('.tab').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    const t = btn.dataset.tab;
    $all('.panel').forEach(p=>p.style.display='none');
    document.getElementById(t).style.display='block';
    if(t==='overview' || t==='analytics') cargarMetricas();
    if(t==='memos') cargarMemos();
  });
});

async function cargarMetricas(){
  try{
    const r = await authFetch('/api/metrics');
    metricsData = await r.json();
    const mb = metricsData.metricas_basicas || {};
    $('#total-memos').textContent = mb.total_memos ?? 0;
    $('#pendientes').textContent = mb.pendientes ?? 0;
    $('#aprobados').textContent = mb.aprobados ?? 0;
    $('#emitidos').textContent = mb.emitidos ?? 0;
    drawCharts();
  }catch(e){ console.error(e); }
}

let charts = {};
function destroy(id){ if(charts[id]){ charts[id].destroy(); charts[id]=null; } }
function drawCharts(){
  const cm = document.getElementById('chartMeses');
  if(cm){
    destroy('meses');
    const labels = (metricsData.memos_por_mes||[]).map(m=>m.mes);
    const data = (metricsData.memos_por_mes||[]).map(m=>m.cantidad);
    charts['meses'] = new Chart(cm,{ type:'line', data:{ labels, datasets:[{ label:'Memos', data }]}, options:{ plugins:{legend:{display:false}}, tension:.35 } });
  }
  const ce = document.getElementById('chartEquipos');
  if(ce){
    destroy('equipos');
    charts['equipos'] = new Chart(ce,{ type:'doughnut',
      data:{ labels:(metricsData.memos_por_equipo||[]).map(e=>e.equipo), datasets:[{ data:(metricsData.memos_por_equipo||[]).map(e=>e.cantidad) }] },
      options:{ plugins:{legend:{position:'bottom'}} }});
  }
  const ci = document.getElementById('chartIncisos');
  if(ci){
    destroy('incisos');
    charts['incisos'] = new Chart(ci,{ type:'bar',
      data:{ labels:(metricsData.incisos_comunes||[]).map(i=>'Inciso '+i.inciso), datasets:[{ data:(metricsData.incisos_comunes||[]).map(i=>i.cantidad), label:'Cantidad' }]},
      options:{ plugins:{legend:{display:false}} }});
  }
  const ct = document.getElementById('chartTipos');
  if(ct){
    destroy('tipos');
    charts['tipos'] = new Chart(ct,{ type:'pie',
      data:{ labels:(metricsData.memos_por_tipo||[]).map(t=>t.tipo), datasets:[{ data:(metricsData.memos_por_tipo||[]).map(t=>t.cantidad) }] },
      options:{ plugins:{legend:{position:'bottom'}} }});
  }
  const ctw = document.getElementById('chartTendencia');
  if(ctw){
    destroy('tend');
    charts['tend'] = new Chart(ctw,{ type:'line',
      data:{ labels:(metricsData.tendencia_semanal||[]).map(t=>t.semana), datasets:[{ data:(metricsData.tendencia_semanal||[]).map(t=>t.cantidad), label:'Memos/semana' }]},
      options:{ plugins:{legend:{display:false}}, tension:.35 }});
  }
}

function estadoPill(txt){
  if(!txt) return '<span class="status">–</span>';
  let cls = 'st-pend';
  if(txt.includes('Aprobado')) cls='st-apr';
  else if(txt.includes('Emitido')) cls='st-emi';
  else if(txt.includes('Observado')) cls='st-obs';
  return `<span class="status ${cls}">${txt}</span>`;
}
function fmtFecha(s){
  if(!s) return '';
  const d = new Date(s);
  return d.toLocaleDateString('es-PE')+' '+d.toLocaleTimeString('es-PE',{hour:'2-digit',minute:'2-digit'});
}

async function cargarMemos(){
  const q = encodeURIComponent($('#search').value||'');
  const e = encodeURIComponent($('#estado-filter').value||'');
  const tbody = document.getElementById('memos-table');
  tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:#64748b; padding:28px">Cargando memos…</td></tr>`;
  try{
    const r = await authFetch(`/api/memos?buscar=${q}&estado=${e}`);
    const data = await r.json();
    memosData = data.memos||[];
    if(memosData.length===0){
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:#64748b; padding:28px">No se encontraron memos</td></tr>`;
      return;
    }
    tbody.innerHTML = memosData.map(m=>`
      <tr>
        <td><strong>${m.memo_id}</strong></td>
        <td>${m.dni||''}</td>
        <td>${m.nombre||''}</td>
        <td>${m.equipo||'-'}</td>
        <td>${m.tipo||'-'}</td>
        <td>${estadoPill(m.estado||'')}</td>
        <td>${fmtFecha(m.created_at)}</td>
      </tr>
    `).join('');
  }catch(err){
    console.error(err);
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:#ef4444; padding:28px">Error al cargar memos</td></tr>`;
  }
}

function exportCSV(){
  if(!memosData || !memosData.length){ alert('No hay datos para exportar'); return; }
  const headers = ['Memo ID','DNI','Nombre','Equipo','Tipo','Estado','Fecha'];
  const rows = memosData.map(m=>[
    m.memo_id, m.dni||'', `"${(m.nombre||'').replace(/"/g,'""')}"`,
    m.equipo||'', `"${(m.tipo||'').replace(/"/g,'""')}"`,
    `"${(m.estado||'').replace(/"/g,'""')}"`, fmtFecha(m.created_at)
  ].join(','));
  const csv = [headers.join(','), ...rows].join('\n');
  const blob = new Blob([csv],{type:'text/csv;charset=utf-8;'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'memos_'+new Date().toISOString().slice(0,10)+'.csv';
  a.click();
}

cargarMetricas();
cargarMemos();
document.getElementById('search').addEventListener('keypress', (e)=>{ if(e.key==='Enter') cargarMemos(); });
document.getElementById('estado-filter').addEventListener('change', cargarMemos);

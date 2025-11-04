// Gate por clave (rol=legal)
(function(){
  const role = 'legal';
  const token = sessionStorage.getItem('memo_token_'+role);
  if(!token){
    const here = encodeURIComponent(location.href);
    location.href = `/auth/key.html?role=${role}&next=${here}`;
  } else { window.__AUTH_TOKEN__ = token; }
})();

async function authFetch(url, options){
  options = options || {};
  options.headers = Object.assign({}, options.headers||{}, { 'Authorization':'Bearer '+(window.__AUTH_TOKEN__||'') });
  return fetch(url, options);
}

const tbody = document.getElementById('tbodyLegal');
const nPending = document.getElementById('nPending');
const nApproved = document.getElementById('nApproved');
const nObserved = document.getElementById('nObserved');

function fmtFecha(s){
  if(!s) return '';
  const d = new Date(s);
  return d.toLocaleDateString('es-PE')+' '+d.toLocaleTimeString('es-PE',{hour:'2-digit',minute:'2-digit'});
}

async function cargar(){
  document.getElementById('btnRefresh').disabled = true;
  try{
    const r = await authFetch('/api/summary?role=legal');
    const data = await r.json();

    nPending.textContent  = data.counts?.pending ?? 0;
    nApproved.textContent = data.counts?.approved ?? 0;
    nObserved.textContent = data.counts?.not_approved ?? 0;

    const rows = data.pending || [];
    if(rows.length===0){
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:#64748b;padding:28px">Sin memos por aprobar</td></tr>`;
      return;
    }
    tbody.innerHTML = rows.map(m=>`
      <tr>
        <td><b>${m.memo_id}</b></td>
        <td>${m.dni||''}</td>
        <td>${m.nombre||''}</td>
        <td>${m.equipo||'-'}</td>
        <td>${fmtFecha(m.created_at)}</td>
        <td class="row-actions">
          <a class="btn btn-primary" href="/legal/review.html?id=${encodeURIComponent(m.id)}" target="_blank">Revisar</a>
        </td>
      </tr>
    `).join('');
  }catch(e){
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:#ef4444;padding:28px">Error al cargar</td></tr>`;
  }finally{
    document.getElementById('btnRefresh').disabled = false;
  }
}

document.getElementById('btnRefresh').addEventListener('click', cargar);
window.addEventListener('focus', cargar); // refresca al volver de la pestaña de revisión
cargar();

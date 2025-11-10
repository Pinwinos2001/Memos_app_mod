(function(){
  var role = 'legal';
  var token = sessionStorage.getItem('memo_token_'+role);
  if(!token){
    var here = encodeURIComponent(location.href);
    location.href = '/apps/memos/auth/key.html?role='+role+'&next='+here;
  } else { window.__AUTH_TOKEN__ = token; }
})();

const API_BASE = window.APP_CONFIG?.API_BASE_URL || "";

function authFetch(url, options){
  options = options || {};
  options.headers = options.headers || {};
  console.log('Using auth token:', window.__AUTH_TOKEN__);
  options.headers['Authorization'] = 'Bearer ' + (window.__AUTH_TOKEN__||'');
  return fetch(url, options);
}

var tbody = document.getElementById('tbodyLegal');
var nPending = document.getElementById('nPending');
var nApproved = document.getElementById('nApproved');
var nObserved = document.getElementById('nObserved');

function fmtFecha(s){
  if(!s) return '';
  var d = new Date(s);
  return d.toLocaleDateString('es-PE')+' '+d.toLocaleTimeString('es-PE',{hour:'2-digit',minute:'2-digit'});
}

function cargar(){
  document.getElementById('btnRefresh').disabled = true;
  authFetch(`${API_BASE}/api/memos/summary?role=legal`)
    .then(function(r){ return r.json(); })
    .then(function(data){
      var counts = data.counts || {};
      nPending.textContent  = counts.pending  != null ? counts.pending  : 0;
      nApproved.textContent = counts.approved != null ? counts.approved : 0;
      nObserved.textContent = counts.not_approved != null ? counts.not_approved : 0;

      var rows = data.pending || [];
      if(rows.length===0){
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#64748b;padding:28px">Sin memos por aprobar</td></tr>';
        return;
      }
      tbody.innerHTML = rows.map(function(m){
        return '<tr>'
          + '<td><b>'+m.memo_id+'</b></td>'
          + '<td>'+(m.dni||'')+'</td>'
          + '<td>'+(m.nombre||'')+'</td>'
          + '<td>'+(m.equipo||'-')+'</td>'
          + '<td>'+fmtFecha(m.created_at)+'</td>'
          + '<td class="row-actions"><a class="btn btn-primary" href="./review.html?id='+encodeURIComponent(m.id)+'" target="_blank">Revisar</a></td>'
          + '</tr>';
      }).join('');
    })
    .catch(function(){
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#ef4444;padding:28px">Error al cargar</td></tr>';
    })
    .finally(function(){
      document.getElementById('btnRefresh').disabled = false;
    });
}
document.getElementById('btnRefresh').addEventListener('click', cargar);
window.addEventListener('focus', cargar);
cargar();
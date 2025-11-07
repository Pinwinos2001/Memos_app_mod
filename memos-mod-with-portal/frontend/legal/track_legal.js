// Auth mínima
(function(){
  var role = 'legal';
  var token = sessionStorage.getItem('memo_token_'+role);
  if(!token){
    var here = encodeURIComponent(location.href);
    location.href = '/auth/key.html?role='+role+'&next='+here;
  } else { window.__AUTH_TOKEN__ = token; }
})();

function authFetch(url, options){
  options = options || {};
  options.headers = options.headers || {};
  options.headers['Authorization'] = 'Bearer ' + (window.__AUTH_TOKEN__||'');
  return fetch(url, options);
}

// Refs
var tbody      = document.getElementById('tbodyLegal');
var nPending   = document.getElementById('nPending');
var nApproved  = document.getElementById('nApproved');
var nObserved  = document.getElementById('nObserved');
var thAcc      = document.getElementById('thAcc');

var cards = {
  pending:  document.getElementById('cardPending'),
  approved: document.getElementById('cardApproved'),
  rejected: document.getElementById('cardRejected')
};

var currentView = 'pending';
var cache = { pending:[], approved:[], rejected:[] };

function fmtFecha(s){
  if(!s) return '';
  var d = new Date(s);
  return d.toLocaleDateString('es-PE')+' '+d.toLocaleTimeString('es-PE',{hour:'2-digit',minute:'2-digit'});
}

function emptyRow(msg){
  return '<tr><td class="empty" colspan="6">'+(msg||'Sin datos')+'</td></tr>';
}

function setActive(view){
  currentView = view;
  // Remover clase active de todas las cards
  Object.keys(cards).forEach(function(k){
    if(cards[k]) cards[k].classList.remove('active');
  });
  // Agregar active a la vista actual
  if(cards[view]) cards[view].classList.add('active');
  
  render();
}

function render(){
  var rows = currentView==='pending' ? cache.pending
           : currentView==='approved' ? cache.approved
           : cache.rejected;

  // Solo Pendientes muestra "Acciones"
  thAcc.style.visibility = (currentView==='pending') ? 'visible' : 'hidden';

  if(!rows || rows.length===0){
    var msg = currentView==='pending' ? 'Sin memos por aprobar' 
            : currentView==='approved' ? 'Sin memos aprobados'
            : 'Sin memos observados';
    tbody.innerHTML = emptyRow(msg);
    return;
  }

  tbody.innerHTML = rows.map(function(m){
    var acc = '';
    if(currentView==='pending'){
      acc = '<a class="btn btn-primary" href="/legal/review.html?id='+encodeURIComponent(m.id)+'" target="_blank">Revisar</a>';
    }
    return '<tr>'
      + '<td><b>'+(m.memo_id||'')+'</b></td>'
      + '<td>'+(m.dni||'')+'</td>'
      + '<td>'+(m.nombre||'')+'</td>'
      + '<td>'+(m.equipo||'-')+'</td>'
      + '<td>'+fmtFecha(m.created_at)+'</td>'
      + '<td class="row-actions">'+(acc||'')+'</td>'
      + '</tr>';
  }).join('');
}

function cargar(){
  var btn = document.getElementById('btnRefresh');
  if(btn) btn.disabled = true;
  
  authFetch('/api/summary?role=legal')
    .then(function(r){
      if(r.status===401){
        var here = encodeURIComponent(location.href);
        location.href = '/auth/key.html?role=legal&next='+here;
        throw new Error('401');
      }
      if(!r.ok){
        throw new Error('HTTP '+r.status);
      }
      return r.json();
    })
    .then(function(data){
      console.log('API Response:', data); // Debug
      
      // Actualizar contadores
      var counts = data && data.counts ? data.counts : {};
      nPending.textContent  = counts.pending  != null ? counts.pending  : 0;
      nApproved.textContent = counts.approved != null ? counts.approved : 0;
      nObserved.textContent = counts.not_approved != null ? counts.not_approved : 0;

      // Cargar listas (acepta varios nombres de claves)
      var pend = data.pending || data.pending_list || [];
      var appr = data.approved_list || data.approved || [];
      var rej  = data.not_approved_list || data.rejected_list || data.observed_list || [];

      cache.pending  = Array.isArray(pend) ? pend : [];
      cache.approved = Array.isArray(appr) ? appr : [];
      cache.rejected = Array.isArray(rej)  ? rej  : [];

      console.log('Cache actualizado:', cache); // Debug
      render();
    })
    .catch(function(err){
      if(String(err) !== 'Error: 401'){
        tbody.innerHTML = emptyRow('Error al cargar datos');
        console.error('Error en cargar():', err);
      }
    })
    .finally(function(){
      if(btn) btn.disabled = false;
    });
}

// Event listeners para las cards
if(cards.pending) {
  cards.pending.addEventListener('click', function(){ setActive('pending'); });
}
if(cards.approved) {
  cards.approved.addEventListener('click', function(){ setActive('approved'); });
}
if(cards.rejected) {
  cards.rejected.addEventListener('click', function(){ setActive('rejected'); });
}

// Botón refrescar
var btnRef = document.getElementById('btnRefresh');
if(btnRef) {
  btnRef.addEventListener('click', cargar);
}

// Auto-refresh
window.addEventListener('focus', cargar);
window.addEventListener('message', function(e){ 
  if(e && e.data && e.data.t==='memos:refresh') cargar(); 
});

// Iniciar
cargar();
(function () {
  var role = 'rrhh';
  var token = sessionStorage.getItem('memo_token_' + role);
  if (!token) {
    var here = encodeURIComponent(location.href);
    location.href = '/auth/key.html?role=' + role + '&next=' + here;
  } else {
    window.__AUTH_TOKEN__ = token;
  }
})();

function authFetch(url, options) {
  options = options || {};
  options.headers = options.headers || {};
  options.headers['Authorization'] = 'Bearer ' + (window.__AUTH_TOKEN__ || '');
  return fetch(url, options);
}

var tbody = document.getElementById('tbodyRRHH');
var nPending = document.getElementById('nPending');
var nApproved = document.getElementById('nApproved');
var nObserved = document.getElementById('nObserved');

function fmtFecha(s) {
  if (!s) return '';
  var d = new Date(s);
  return d.toLocaleDateString('es-PE') + ' ' +
         d.toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit' });
}

function pintarVacio(msg) {
  tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#64748b;padding:28px">'
    + (msg || 'Sin memos por aprobar') + '</td></tr>';
}

function cargar() {
  document.getElementById('btnRefresh').disabled = true;

  authFetch('/api/summary?role=rrhh')
    .then(function (r) {
      if (r.status === 401) {
        var here = encodeURIComponent(location.href);
        location.href = '/auth/key.html?role=rrhh&next=' + here;
        return Promise.reject('401');
      }
      return r.json();
    })
    .then(function (data) {
      var counts = data && data.counts ? data.counts : {};
      nPending.textContent  = counts.pending != null ? counts.pending : 0;
      nApproved.textContent = counts.approved != null ? counts.approved : 0;
      nObserved.textContent = counts.not_approved != null ? counts.not_approved : 0;

      var rows = (data && data.pending) || [];
      if (rows.length === 0) { pintarVacio(); return; }

      tbody.innerHTML = rows.map(function (m) {
        return '<tr>'
          + '<td><b>' + (m.memo_id || '') + '</b></td>'
          + '<td>' + (m.dni || '') + '</td>'
          + '<td>' + (m.nombre || '') + '</td>'
          + '<td>' + (m.equipo || '-') + '</td>'
          + '<td>' + fmtFecha(m.created_at) + '</td>'
          + '<td class="row-actions">'
          +   '<a class="btn btn-primary" href="/rrhh/review.html?id=' + encodeURIComponent(m.id) + '" target="_blank">Revisar</a>'
          + '</td>'
          + '</tr>';
      }).join('');
    })
    .catch(function (err) {
      if (err !== '401') {
        pintarVacio('Error al cargar');
        console.error(err);
      }
    })
    .finally(function () {
      document.getElementById('btnRefresh').disabled = false;
    });
}

document.getElementById('btnRefresh').addEventListener('click', cargar);
window.addEventListener('focus', cargar);

// Se refresca cuando la ventana de review manda el postMessage
window.addEventListener('message', function (e) {
  if (e && e.data && e.data.t === 'memos:refresh') cargar();
});

cargar();


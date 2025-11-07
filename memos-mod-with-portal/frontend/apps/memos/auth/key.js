function qs(k){ return new URLSearchParams(location.search).get(k); }
const role = (qs('role')||'').toLowerCase() || 'dash';
const nextUrl = qs('next') || '';
document.getElementById('desc').textContent = `Ingresa la clave de ${role.toUpperCase()}.`;
document.getElementById('btn').addEventListener('click', async ()=>{
  const key = document.getElementById('key').value.trim();
  if(!key){ return; }
  try{
    const r = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type':'application/json' },
      body: JSON.stringify({ role, key })
    });
    const d = await r.json();
    if(!r.ok || !d.ok){ throw new Error(d.detail || 'Clave inválida'); }
    sessionStorage.setItem('memo_token_'+role, d.token);
    const target = nextUrl || d.redirect || '/portal/index.html';
    location.href = target;
  }catch(e){
    document.getElementById('msg').textContent = e.message || 'Error de acceso';
  }
});
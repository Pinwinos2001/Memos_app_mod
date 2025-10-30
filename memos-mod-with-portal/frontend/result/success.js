function qs(k){ return new URLSearchParams(location.search).get(k); }
document.getElementById('chipMemo').textContent = qs('memo_id') || '—';
document.getElementById('chipCorr').textContent = qs('corr_id') || '—';
document.getElementById('email').textContent = qs('email') || '—';
const pdf = qs('pdf') || '#';
document.getElementById('aPDF').href = pdf;
/* Parti comuni alle maschere: icone, formattazione, avvisi, griglia e attesa durante il caricamento.
   Ogni pagina definisce la propria funzione api(path, params, signal), usata da Caricamento. */
document.body.insertAdjacentHTML('afterbegin', `<svg width="0" height="0" style="position:absolute">
 <defs>
  <symbol id="i-doc" viewBox="0 0 32 32"><path d="M7 3h12l6 6v20H7z" fill="#fff" stroke="#6b6b6b"/><path d="M19 3v6h6" fill="#eee" stroke="#6b6b6b"/><path d="M10 14h12M10 18h12M10 22h9" stroke="#9aa" stroke-width="1"/></symbol>
  <symbol id="i-new" viewBox="0 0 32 32"><use href="#i-doc"/><circle cx="23" cy="23" r="6" fill="#f6c343" stroke="#b88a00"/><path d="M23 19v8M19 23h8" stroke="#fff" stroke-width="2"/></symbol>
  <symbol id="i-dup" viewBox="0 0 32 32"><path d="M4 7h11l5 5v17H4z" fill="#fff" stroke="#6b6b6b"/><path d="M11 2h11l6 6v16H20" fill="#fff" stroke="#6b6b6b"/></symbol>
  <symbol id="i-ai" viewBox="0 0 32 32"><use href="#i-doc"/><path d="M23 15l2 5 5 2-5 2-2 5-2-5-5-2 5-2z" fill="#7a4fd0"/></symbol>
  <symbol id="i-emit" viewBox="0 0 32 32"><rect x="5" y="3" width="18" height="24" fill="#fff" stroke="#6b6b6b"/><path d="M8 9h12M8 13h12M8 17h12M8 21h8" stroke="#6b8"/><path d="M20 20l8 8M28 20v8h-8" stroke="#2b7f52" stroke-width="2" fill="none"/></symbol>
  <symbol id="i-check" viewBox="0 0 32 32"><rect x="5" y="3" width="18" height="24" fill="#fff" stroke="#6b6b6b"/><path d="M8 9h12M8 13h12M8 17h8" stroke="#6b8"/><path d="M16 23l4 4 9-10" stroke="#2b7f52" stroke-width="3" fill="none"/></symbol>
  <symbol id="i-word" viewBox="0 0 32 32"><use href="#i-doc"/><rect x="2" y="15" width="13" height="12" fill="#2b5797"/><path d="M4 18l2 7 2-5 2 5 2-7" stroke="#fff" fill="none" stroke-width="1.2"/></symbol>
  <symbol id="i-link" viewBox="0 0 32 32"><rect x="3" y="11" width="15" height="10" rx="5" fill="none" stroke="#2b5797" stroke-width="3"/><rect x="14" y="11" width="15" height="10" rx="5" fill="none" stroke="#4f7fc7" stroke-width="3"/></symbol>
  <symbol id="i-ddt" viewBox="0 0 32 32"><use href="#i-doc"/><rect x="9" y="12" width="14" height="7" fill="#fff" stroke="#2b5797"/><text x="16" y="18" font-size="6" text-anchor="middle" fill="#2b5797" font-family="Arial" font-weight="bold">DDT</text></symbol>
  <symbol id="i-chart" viewBox="0 0 32 32"><rect x="4" y="4" width="24" height="24" fill="#fff" stroke="#6b6b6b"/><rect x="8" y="17" width="4" height="8" fill="#3aa76d"/><rect x="14" y="11" width="4" height="14" fill="#2b5797"/><rect x="20" y="14" width="4" height="11" fill="#3aa76d"/><path d="M7 9h18" stroke="#999"/></symbol>
  <symbol id="i-archive" viewBox="0 0 32 32"><rect x="5" y="5" width="20" height="22" fill="#fff" stroke="#6b6b6b"/><rect x="9" y="9" width="12" height="9" fill="#cfe0f6" stroke="#6b8bb8"/><path d="M9 22h12" stroke="#999"/></symbol>
  <symbol id="i-refresh" viewBox="0 0 32 32"><path d="M26 15a10 10 0 1 1-3-7" fill="none" stroke="#2f9e5a" stroke-width="4"/><path d="M19 3l6 5-7 3z" fill="#2f9e5a"/></symbol>
  <symbol id="i-funnel" viewBox="0 0 32 32"><path d="M4 5h24l-9 11v10l-6 3V16z" fill="#7d8a99" stroke="#4e5a68"/></symbol>
  <symbol id="i-print" viewBox="0 0 32 32"><rect x="9" y="3" width="14" height="9" fill="#fff" stroke="#6b6b6b"/><rect x="3" y="11" width="26" height="12" rx="2" fill="#7d8a99" stroke="#4e5a68"/><rect x="9" y="19" width="14" height="10" fill="#fff" stroke="#6b6b6b"/><circle cx="25" cy="15" r="1.5" fill="#6f6"/></symbol>
  <symbol id="i-report" viewBox="0 0 32 32"><use href="#i-doc"/><rect x="9" y="12" width="5" height="5" fill="#d33"/></symbol>
  <symbol id="i-mov" viewBox="0 0 32 32"><rect x="4" y="4" width="24" height="24" fill="#fff" stroke="#c62828" stroke-width="2"/><path d="M9 23L23 9" stroke="#c62828" stroke-width="3"/><path d="M23 9v6M23 9h-6" stroke="#c62828" stroke-width="2"/></symbol>
  <symbol id="i-flow" viewBox="0 0 32 32"><rect x="3" y="4" width="10" height="8" fill="#ccc"/><rect x="19" y="4" width="10" height="8" fill="#ddd"/><rect x="11" y="20" width="10" height="8" fill="#ccc"/><path d="M8 12v4h16v-4M16 16v4" stroke="#aaa" fill="none"/></symbol>
  <symbol id="i-excel" viewBox="0 0 32 32"><rect x="3" y="3" width="26" height="26" fill="#1d7044"/><path d="M10 9l12 14M22 9L10 23" stroke="#fff" stroke-width="3"/></symbol>
  <symbol id="i-grid" viewBox="0 0 32 32"><rect x="4" y="4" width="24" height="24" fill="#fff" stroke="#2b5797" stroke-width="2"/><path d="M4 12h24M4 20h24M14 4v24" stroke="#2b5797"/></symbol>
  <symbol id="i-pdf" viewBox="0 0 32 32"><use href="#i-doc"/><rect x="3" y="16" width="16" height="11" fill="#c62828"/><text x="11" y="25" font-size="8" text-anchor="middle" fill="#fff" font-family="Arial" font-weight="bold">PDF</text></symbol>
  <symbol id="i-folder" viewBox="0 0 16 16"><path d="M1 3h5l1 2h8v9H1z" fill="#f2c94c" stroke="#c49b1f"/></symbol>
  <symbol id="i-folderp" viewBox="0 0 16 16"><path d="M1 3h5l1 2h8v9H1z" fill="#f2c94c" stroke="#c49b1f"/><circle cx="5" cy="9" r="2" fill="#3a6fb5"/></symbol>
  <symbol id="i-view" viewBox="0 0 16 16"><path d="M1 2h10l-4 5v5l-2 1V7z" fill="#7d8a99" stroke="#4e5a68"/><rect x="9" y="9" width="6" height="6" fill="#fff" stroke="#4e5a68"/><path d="M10 11h4M10 13h4" stroke="#4e5a68"/></symbol>
  <symbol id="i-esci" viewBox="0 0 32 32"><path d="M14 4h14v24H14z" fill="#f2c069" stroke="#c79436"/><path d="M18 16H4M9 10l-6 6 6 6" fill="none" stroke="#3a6fb5" stroke-width="3"/></symbol>
  <symbol id="i-scad" viewBox="0 0 32 32"><rect x="3" y="6" width="22" height="20" fill="#fff" stroke="#6b6b6b"/><rect x="3" y="6" width="22" height="5" fill="#c62828"/><path d="M8 3v6M20 3v6" stroke="#555" stroke-width="2"/><path d="M6 15h4M12 15h4M18 15h4M6 19h4M12 19h4" stroke="#9aa" stroke-width="2"/><circle cx="24" cy="23" r="7" fill="#f6c343" stroke="#b88a00"/><text x="24" y="27" font-size="10" text-anchor="middle" fill="#6b4e00" font-family="Arial" font-weight="bold">€</text></symbol>
 </defs>
</svg>`);

/* ---------------- formattazione ---------------- */
const fmtDate = iso => { if(!iso) return ''; const [y,m,d] = iso.split('-'); return `${+d}/${m}/${y}`; };
const fmtNum = (v,dec=2) => v==null||v==='' ? '' : Number(v).toLocaleString('it-IT',{minimumFractionDigits:dec,maximumFractionDigits:dec,useGrouping:false});
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

function toast(msg){ const t=document.getElementById('toast'); t.textContent=msg; t.classList.add('on'); clearTimeout(t._h); t._h=setTimeout(()=>t.classList.remove('on'),2600); }
/* ---------------- componente griglia ---------------- */
class Grid {
  constructor(el, cols, opt={}) {
    this.el = el; this.cols = cols; this.opt = opt;
    this.rows = []; this.view = []; this.filters = {}; this.sort = null; this.cur = -1; this.checked = new Set();
    el.addEventListener('keydown', e => {
      if (e.key==='ArrowDown') { this.select(Math.min(this.cur+1, this.view.length-1)); e.preventDefault(); }
      if (e.key==='ArrowUp') { this.select(Math.max(this.cur-1, 0)); e.preventDefault(); }
      if (e.key==='Enter' && this.opt.onOpen && this.view[this.cur]) this.opt.onOpen(this.view[this.cur]);
    });
  }
  setRows(rows){ this.rows = rows; this.checked.clear(); this.cur = -1; this.apply(); if (this.view.length) this.select(0); else this.opt.onSelect?.(null); }
  text(c, r){ const v = r[c.key]; return c.fmt ? c.fmt(v, r) : (v ?? ''); }
  apply(){
    let v = this.rows.filter(r => Object.entries(this.filters).every(([k,f]) => {
      if (!f) return true; const c = this.cols.find(c=>c.key===k); return String(this.text(c,r)).toLowerCase().includes(f.toLowerCase());
    }));
    if (this.sort) { const {key,dir} = this.sort; v = [...v].sort((a,b) => (a[key]>b[key]?1:a[key]<b[key]?-1:0)*dir); }
    this.view = v; this.render();
    if (this.opt.countEl) this.opt.countEl.textContent = `Righe: ${v.length}`;
  }
  render(){
    const cols = this.cols, grouped = cols.some(c => c.group);
    const W = cols.reduce((s,c)=>s+(c.w||80),0);
    let h = `<table class="grid" style="width:${W}px"><colgroup>${cols.map(c=>`<col style="width:${c.w||80}px">`).join('')}</colgroup><thead class="${grouped?'':'single'}">`;
    const th = c => { const s = this.sort && c.key && this.sort.key===c.key ?(this.sort.dir>0?' ▲':' ▼') : '';
      return `${c.label ?? ''}${s}${c.arrow!==false && c.key ? '<span class="arr">▾</span>' : ''}`; };
    if (grouped) {
      h += '<tr class="h1">';
      for (let i=0;i<cols.length;i++){
        const c = cols[i];
        if (!c.group) { h += `<th rowspan="2" class="${c.key?'sortable':''} ${c.hcls||''}" data-k="${c.key||''}" style="height:40px">${th(c)}</th>`; continue; }
        let span = 1; while (cols[i+span]?.group === c.group) span++;
        h += `<th colspan="${span}">${c.group}</th>`; i += span-1;
      }
      h += '</tr><tr class="h2">' + cols.filter(c=>c.group).map(c=>`<th class="${c.key?'sortable':''}" data-k="${c.key||''}">${th(c)}</th>`).join('') + '</tr>';
    } else {
      h += '<tr class="h1">' + cols.map(c=>`<th class="${c.key?'sortable':''} ${c.hcls||''}" data-k="${c.key||''}">${th(c)}</th>`).join('') + '</tr>';
    }
    if (this.opt.filtri !== false) h += '<tr class="hf">' + cols.map((c,i)=> i===0 ? '<th class="fun">▼</th>' : `<th>${c.key && c.filter!==false ? `<input data-f="${c.key}" value="${esc(this.filters[c.key]||'')}">` : ''}</th>`).join('') + '</tr>';
    h += '</thead><tbody>';
    if (!this.view.length) h += `<tr><td colspan="${cols.length}" class="empty">Nessun dato da visualizzare</td></tr>`;
    this.view.forEach((r,i) => {
      h += `<tr data-i="${i}" class="${i===this.cur?'cur':''}">` + cols.map(c => {
        if (c.type==='ind') return `<td class="ind">${i===this.cur?'▶':''}</td>`;
        if (c.type==='chk') return `<td class="c"><input type="checkbox" data-chk="${i}" ${this.checked.has(r)?'checked':''}></td>`;
        if (c.render) return `<td class="${c.cls||''}">${c.render(r[c.key], r)}</td>`;
        return `<td class="${c.cls||''}" title="${esc(this.text(c,r))}">${esc(this.text(c,r))}</td>`;
      }).join('') + '</tr>';
    });
    // riempi: riga vuota che occupa lo spazio libero (la tabella deve essere alta quanto il contenitore)
    if (this.opt.riempi) h += `<tr class="riempi"><td colspan="${cols.length}"></td></tr>`;
    h += '</tbody>';
    // colonne con somma:true: totale delle righe visibili
    const somma = c => { const t = this.view.reduce((s,r) => s + (Number(r[c.key]) || 0), 0); return esc(c.fmt ? c.fmt(t) : t); };
    if (this.opt.totali) h += `<tfoot><tr>${cols.map((c,i) => `<td class="${c.somma ? c.cls||'' : ''}">${i===0 ? 'Tot:' : c.somma ? somma(c) : ''}</td>`).join('')}</tr></tfoot>`;
    h += '</table>';
    const ae = document.activeElement, focused = this.el.contains(ae) ? ae.dataset?.f : null, caret = ae?.selectionStart;
    this.el.innerHTML = h;
    if (focused) { const inp = this.el.querySelector(`input[data-f="${focused}"]`); if (inp) { inp.focus(); inp.setSelectionRange(caret,caret); } }
    this.el.querySelectorAll('th.sortable').forEach(t => t.onclick = e => { if (e.target.tagName==='INPUT') return;
      const k = t.dataset.k; this.sort = this.sort?.key===k ? (this.sort.dir>0 ? {key:k,dir:-1} : null) : {key:k,dir:1}; const sel=this.view[this.cur]; this.apply(); this.cur=this.view.indexOf(sel); this.render(); });
    this.el.querySelectorAll('input[data-f]').forEach(inp => inp.oninput = () => { this.filters[inp.dataset.f] = inp.value; this.apply(); this.select(this.view.length?0:-1); });
    this.el.querySelectorAll('tbody tr[data-i]').forEach(tr => {
      tr.onclick = e => { if (e.target.dataset.chk!==undefined) { const r=this.view[+e.target.dataset.chk]; e.target.checked?this.checked.add(r):this.checked.delete(r); return; } this.select(+tr.dataset.i); };
      tr.ondblclick = () => this.opt.onOpen?.(this.view[+tr.dataset.i]);
    });
  }
  select(i){
    if (i===this.cur && i>=0) return;
    this.cur = i;
    this.el.querySelectorAll('tbody tr').forEach(tr => { const on = +tr.dataset.i===i; tr.classList.toggle('cur', on); const ind = tr.querySelector('td.ind'); if (ind) ind.textContent = on?'▶':''; if (on) tr.scrollIntoView({block:'nearest'}); });
    this.opt.onSelect?.(this.view[i] || null);
  }
  current(){ return this.view[this.cur] || null; }
  toCSV(){
    const cols = this.cols.filter(c => c.key);
    const q = s => `"${String(s).replace(/"/g,'""')}"`;
    return [cols.map(c=>q((c.group?c.group+' ':'')+c.label)).join(';'), ...this.view.map(r => cols.map(c=>q(this.text(c,r))).join(';'))].join('\r\n');
  }
}

/* ---------------- caricamento dei pannelli ---------------- */
// Mostra l'attesa sul pannello e tiene valida solo l'ultima richiesta: una risposta lenta
// di una ricerca precedente non può sovrascrivere quella attuale.
class Caricamento {
  constructor(panel, testo){
    this.testo = testo;
    this.el = document.createElement('div'); this.el.className = 'attesa'; this.el.setAttribute('role','status');
    this.el.innerHTML = '<i></i><span></span>';
    panel.appendChild(this.el);
  }
  // undefined = richiesta superata da una più recente, null = errore già segnalato
  async esegui(path, params){
    this.annulla();
    const c = this.ctrl = new AbortController();
    this.mostra();
    const dati = await api(path, params, c.signal);
    if (this.ctrl !== c) return undefined;
    this.ctrl = null; this.nascondi();
    return dati;
  }
  annulla(){ this.ctrl?.abort(); this.ctrl = null; this.nascondi(); }
  mostra(){
    const t0 = Date.now(), span = this.el.lastChild;
    const scrivi = () => { const s = Math.round((Date.now()-t0)/1000); span.textContent = this.testo + (s>=2 ? ` ${s} s` : ''); };
    scrivi(); this._t = setInterval(scrivi, 1000);
    this._d = setTimeout(() => this.el.classList.add('on'), 150);  // niente lampeggio se la risposta è immediata
  }
  nascondi(){ clearInterval(this._t); clearTimeout(this._d); this.el.classList.remove('on'); }
}


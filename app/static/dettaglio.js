/* Dettaglio del singolo ordine (sola lettura). Usa le funzioni di index.html: api, toast, esc, fmtNum, Grid, Caricamento. */
window.Dettaglio = (() => {
  /* ---------------- campi ---------------- */
  const data = iso => iso ? iso.split('-').reverse().join('/') : '';
  // casella di testo; tipo: '' | 'sel' (elenco) | 'num' | 'data'
  const casella = (v, tipo='', off=false) => `<div class="d-v ${tipo} ${off?'off':''}" title="${esc(v)}">${esc(v)}</div>`;
  const riga = (etichetta, contenuto, cls='') => `<div class="d-r"><label class="${cls}">${esc(etichetta)}</label><div class="d-f">${contenuto}</div></div>`;
  const campo = (etichetta, v, tipo='', off=false) => riga(etichetta, casella(v, tipo, off), off?'off':'');
  const interruttore = (etichetta, on, cls='') => riga(etichetta, `<div class="d-sw ${on?'on':''}" role="img" aria-label="${on?'Sì':'No'}"></div>`, cls);
  const num = (v, dec=2) => fmtNum(v, dec);
  const sezione = (titolo, sx, dx, {chiudibile=false, piu=false}={}) =>
    `<section class="d-sez"><h3><span>${esc(titolo)}</span>${piu?'<a data-fare="Mostra di più">Mostra di più</a>':''}${chiudibile?'<button data-chiudi aria-label="Riduci o espandi">⌃</button>':''}</h3>
     <div class="d-cols"><div>${sx}</div><div>${dx}</div></div></section>`;
  const titoletto = t => `<h4>${esc(t)}</h4>`;
  const luogo = (o, tipoProv='', tipoStato='sel') => casella(o.provincia, tipoProv) + casella(o.cap) + casella(o.stato, tipoStato);

  /* ---------------- schede ---------------- */
  const SCHEDE = {
    generali: d => {
      const i = d.intestatario, c = d.consegna, a = d.altri;
      const agente = (t, x) => titoletto(t) + campo('Agente', x.agente, 'sel') + campo('Ruolo', x.ruolo, 'sel') + campo('% provvigione', num(x.provvigione), 'num') + campo('Capo area', x.capo_area, 'sel');
      return sezione('Dati generali',
        titoletto('Dati intestatario') + campo('Ragione sociale', i.ragione_sociale) + campo('Indirizzo', i.indirizzo) + campo('Comune', i.comune) +
        riga('', luogo(i)) + campo('Frazione', i.frazione) + campo('Partita IVA', i.partita_iva) + campo('Codice fiscale', i.codice_fiscale),
        titoletto('Luogo di consegna') + campo('Codice indirizzo', c.codice, 'sel') + campo('Ragione sociale', c.ragione_sociale) + campo('Indirizzo', c.indirizzo) +
        campo('', c.indirizzo2) + campo('Comune', c.comune, 'sel') + riga('', luogo(c)) + riga('Frazione', casella(c.frazione) + casella('')) + interruttore('Intestatario DDT', false, 'off'),
        {chiudibile:true, piu:true}) +
      sezione('Agenti', agente('Titolare', d.agenti[0]), agente('Secondario', d.agenti[1]), {chiudibile:true}) +
      sezione('Altri dati',
        campo('Rif. commessa', '', 'sel') + campo('Data consegna', data(a.data_consegna), 'num data') + campo('Divisione', a.divisione, 'sel') +
        campo('Centro di imputazione', a.centro, 'sel') + campo('Riferimento', a.riferimento) + campo('Contatto', '', 'sel'),
        interruttore('Conferma emessa', a.confermato) + interruttore('Blocca evasione', a.blocca_evasione, 'sott') +
        riga('Documento derivato', casella(a.derivato, 'sel') + casella(a.tipo_fattura, 'sel')) + campo('Valuta', a.valuta, 'sel') +
        campo('Cambio', num(a.cambio, 6), 'num sel', true) + campo('IVA no imp./agevolata', a.iva_agevolata, 'sel') +
        campo('Rilevazione addebiti', a.addebiti, 'sel') + campo('Lingua', a.lingua, 'sel'),
        {chiudibile:true});
    },
    condizioni: d => {
      const c = d.commerciali, f = d.finanziarie, a = d.fatturazione, t = d.destinatario_fattura, b = d.banca;
      return sezione('Commerciali',
        campo('Listino prioritario', c.listino_prioritario, 'sel') + campo('Listino ordinario', c.listino_ordinario, 'sel'),
        campo('Politica sconti', c.politica_sconti, 'sel') + campo('Zona', c.zona)) +
      sezione('Finanziarie',
        campo('Cond. pagamento', f.pagamento, 'sel') + campo('% sconto', num(f.sconto), 'num'),
        campo('Decorrenza scadenze', data(f.decorrenza), 'num data')) +
      sezione('Fatturazione',
        titoletto('Anagrafica di fatturazione') + campo('Codice', a.codice, 'sel') + campo('Indirizzo', a.indirizzo) + campo('', '') +
        campo('Comune', a.comune, 'sel') + riga('Provincia', luogo(a, 'sel')) + campo('Frazione', a.frazione) +
        riga('Territorialità IVA', casella(a.territorialita, 'sel') + casella('')) + interruttore('Cliente privato', a.privato, 'off'),
        titoletto('Destinatario Fattura') + campo('Numero indirizzo', t.numero, 'sel') + campo('Indirizzo', t.indirizzo) + campo('', '') +
        campo('Comune', t.comune, 'sel') + riga('Provincia', luogo(t, 'sel')) + campo('Frazione', t.frazione) +
        campo('Contatto', t.contatto, 'sel') + campo('e-mail', '')) +
      sezione('Estremi bancari', campo('Nostro conto banca', b.nostra, 'sel'),
        campo('Appoggio bancario', b.appoggio, 'sel') + campo('IBAN', '') + campo('Rif. banca estera', ''));
    },
    logistica: d => {
      const l = d.logistica;
      const doppia = (e, a, b, tipoB='') => riga(e, casella(a, 'sel') + casella(b, tipoB));
      const vettore = (n, x) => titoletto(`Vettore ${n}`) + campo('Vettore', x.vettore, 'sel') + campo('Ragione sociale', x.ragione_sociale) + campo('Indirizzo', x.indirizzo) +
        campo('', x.indirizzo2) + campo('Comune', x.comune) + riga('', luogo(x, '', '')) + campo('Partita IVA', x.partita_iva) + campo('N. iscrizione albo', x.albo);
      return sezione('Magazzini', doppia('Magazzino principale', l.magazzino, l.area, 'sel'), doppia('Magazzino secondario', l.magazzino_sec, l.area_sec, 'sel')) +
      sezione('Modalità di accompagnamento',
        doppia('Porto', l.porto, l.des_porto) + doppia('Causale trasporto', l.causale, l.des_causale),
        doppia('Trasporto a mezzo', l.trasporto, l.des_trasporto) + doppia('Aspetto beni', l.aspetto, l.des_aspetto)) +
      sezione('Vettori', vettore(1, d.vettori[0]), vettore(2, d.vettori[1])) +
      sezione('Pianificazione spedizioni',
        campo('Giro di consegna', l.giro, 'sel') + campo('Sequenza', l.sequenza, 'num', true),
        campo('Priorità ordine', '', 'num') + campo('Tipo evasione', '', 'sel'));
    },
  };
  const MENU = [['generali','Generali'],['utente','Campi utente'],['condizioni','Condizioni'],['logistica','Logistica'],['analitica','Analitica'],
    ['righe','Righe'],['spese','Spese/Sconti'],['totali','Totali'],['note','Note e allegati'],['emissione','Emissione']];

  /* ---------------- ribbon ---------------- */
  const ico = id => `<svg><use href="#${id}"/></svg>`;
  // grande(icona, testo, azione); azione vuota = disattivato come nella maschera
  const grande = (id, testo, azione) => `<div class="rbig ${azione?'':'dis'}" ${azione?`data-fare="${esc(azione)}"`:''}>${ico(id)}${testo}</div>`;
  const piccolo = (id, testo, azione) => `<div class="rsmall" data-fare="${esc(azione)}">${ico(id)}${testo}</div>`;
  const gruppo = (nome, corpo) => `<div class="rgroup"><div class="rbody">${corpo}</div><div class="rlabel">${nome}</div></div>`;
  const RIBBON = {
    azioni: gruppo('Navigazione', grande('d-esci','Abbandona<br>(F1)','abbandona')) +
      gruppo('Gestione', grande('d-matita','Varia<br>(F9)','Varia') + grande('d-salva','Salva<br>(END)') + grande('d-elimina','Elimina<br>(F8)','Elimina')) +
      gruppo('Dati documento', grande('i-view','Riferimenti','Riferimenti') + grande('d-matita','Nota','Nota') + grande('d-persona','Anagrafica<br>luogo consegna','Anagrafica luogo consegna') +
        grande('d-persona','Destinatari<br>documento','Destinatari documento') + grande('i-flow','Dati<br>FTE (F)','Dati FTE') + grande('i-grid','Identificativi<br>esterni','Identificativi esterni')) +
      gruppo('Altre funzioni', grande('d-persona','Variazione<br>intestatario') + grande('d-persona','Varia<br>agenti') + grande('i-refresh','Rideriva condizioni<br>commerciali') +
        grande('i-report','Report','Report') + grande('i-doc','Situazione<br>documento','Situazione documento')) +
      gruppo('Evasione', grande('i-dup','Evasione<br>▾')) +
      gruppo('Interrogazioni', grande('d-persona','Anagrafica','Anagrafica') + grande('i-check','Controllo<br>fido','Controllo fido') +
        `<div class="rcol">${piccolo('i-report','Interrogazione dichiarazioni d’intento','Interrogazione dichiarazioni d’intento')}${piccolo('i-doc','Esenzioni addebiti','Esenzioni addebiti')}</div>`) +
      gruppo('Archiviazione', grande('i-archive','Documenti<br>archiviati','Documenti archiviati')),
    condizioni: gruppo('Altri dati', grande('i-doc','Dettaglio<br>IBAN (F7)')) + gruppo('Altre funzioni', grande('i-refresh','Riapplica<br>condizioni (C)')),
    logistica: gruppo('Gestione', grande('d-camion','Altri Indirizzi<br>Vettore 1 (A)') + grande('d-camion','Altri Indirizzi<br>Vettore 2 (L)')),
  };

  /* ---------------- struttura ---------------- */
  const root = document.getElementById('dett');
  root.innerHTML = `<svg width="0" height="0" style="position:absolute"><defs>
    <symbol id="d-esci" viewBox="0 0 32 32"><path d="M14 4h14v24H14z" fill="#f2c069" stroke="#c79436"/><path d="M18 16H4M9 10l-6 6 6 6" fill="none" stroke="#3a6fb5" stroke-width="3"/></symbol>
    <symbol id="d-matita" viewBox="0 0 32 32"><path d="M5 3h12l6 6v20H5z" fill="#fff" stroke="#6b6b6b"/><path d="M28 13l-11 11-4 1 1-4 11-11z" fill="#5a7fb8" stroke="#34497d"/></symbol>
    <symbol id="d-salva" viewBox="0 0 32 32"><path d="M5 5h19l3 3v19H5z" fill="#8a9bc4" stroke="#5a6a94"/><path d="M10 5h11v8H10zM9 18h14v9H9z" fill="#fff"/></symbol>
    <symbol id="d-elimina" viewBox="0 0 32 32"><path d="M5 3h12l6 6v20H5z" fill="#fff" stroke="#6b6b6b"/><path d="M15 17l12 12M27 17L15 29" stroke="#c0392b" stroke-width="3"/></symbol>
    <symbol id="d-persona" viewBox="0 0 32 32"><circle cx="16" cy="10" r="6" fill="#3a6fb5"/><path d="M4 29c0-8 5-12 12-12s12 4 12 12z" fill="#3a6fb5"/></symbol>
    <symbol id="d-camion" viewBox="0 0 32 32"><path d="M2 8h18v14H2z" fill="#f2c069" stroke="#c79436"/><path d="M20 13h6l4 5v4H20z" fill="#bcd0e8" stroke="#5a7fb8"/><circle cx="8" cy="24" r="3" fill="#555"/><circle cx="25" cy="24" r="3" fill="#555"/></symbol>
  </defs></svg>
  <div class="menutabs"><div class="tab" data-tab="azioni">AZIONI</div><div class="tab contesto" data-tab="contesto" hidden></div><input class="search" placeholder="cerca nel manuale..."><div class="collapse">▲</div></div>
  <div class="ribbon"></div>
  <div class="d-titolo"></div><div class="d-sotto"></div>
  <div class="d-corpo"><nav class="d-menu">${MENU.map(([k,t])=>`<button data-scheda="${k}">${esc(t)}</button>`).join('')}</nav><div class="d-scheda"></div></div>`;
  const $ = s => root.querySelector(s);
  const attesa = new Caricamento($('.d-corpo'), 'Caricamento ordine…');
  let ordine = null, dati = null, scheda = 'generali', grigliaRighe = null, attesaRighe = null;

  function mostraRibbon(nome){
    const ctx = !!RIBBON[scheda];
    const contesto = $('[data-tab=contesto]');
    contesto.hidden = !ctx; contesto.style.display = ctx ? '' : 'none';
    contesto.textContent = ctx ? scheda.toUpperCase() : '';
    $('.menutabs').classList.toggle('ctx', ctx);
    $('[data-tab=azioni]').classList.toggle('sel', nome==='azioni');
    contesto.classList.toggle('sel', nome!=='azioni');
    $('.ribbon').innerHTML = RIBBON[nome];
  }
  function mostraScheda(k){
    scheda = k;
    root.querySelectorAll('.d-menu button').forEach(b => { b.classList.toggle('sel', b.dataset.scheda===k); if (b.dataset.scheda===k) b.setAttribute('aria-current','page'); else b.removeAttribute('aria-current'); });
    mostraRibbon(RIBBON[k] ? k : 'azioni');
    const el = $('.d-scheda');
    attesaRighe?.annulla(); grigliaRighe = attesaRighe = null;
    el.scrollTop = 0;
    if (!dati) { el.innerHTML = ''; return; }
    if (SCHEDE[k]) el.innerHTML = SCHEDE[k](dati);
    else if (k==='righe') mostraRighe(el);
    else el.innerHTML = `<div class="d-vuota">Scheda "${esc(MENU.find(m=>m[0]===k)[1])}" non ancora disponibile.</div>`;
  }
  async function mostraRighe(el){
    el.innerHTML = '<div class="d-righe panel"><div class="cnt">Righe: 0</div><div class="gwrap" tabindex="0"></div></div>';
    const pannello = el.firstChild, g = grigliaRighe = new Grid(pannello.querySelector('.gwrap'), detailCols, {countEl:pannello.querySelector('.cnt')});
    attesaRighe = new Caricamento(pannello, 'Caricamento righe…');
    const r = await attesaRighe.esegui(`/api/ordini/${ordine.id}/righe`);
    if (r !== undefined && g === grigliaRighe) g.setRows(r || []);
  }
  function titoli(){
    const o = dati || ordine, n = o.num_reg ?? '';
    $('.d-titolo').textContent = `Ordine da cliente n. ${n} del ${data(o.data_reg)}`;
    $('.d-sotto').textContent = dati
      ? `Tipo documento: ${dati.tipo ? `${dati.tipo} (${dati.cod_tipo})` : dati.cod_tipo} | Cliente: ${dati.cliente} (${dati.cod_cliente})`
      : `Cliente: ${o.ragione_sociale} (${o.cod_cliente})`;
  }

  /* ---------------- apertura e chiusura ---------------- */
  async function apri(o){
    ordine = o; dati = null;
    document.body.classList.add('in-dettaglio');
    titoli(); mostraScheda('generali');
    const d = await attesa.esegui(`/api/ordini/${o.id}/dettaglio`);
    if (d === undefined) return;
    if (d === null) return chiudi();  // errore già segnalato
    dati = d; titoli(); mostraScheda(scheda);
    if (d.avvisi.length) toast('Dati non disponibili: ' + d.avvisi.join(', '));
  }
  function chiudi(){
    attesa.annulla(); attesaRighe?.annulla(); grigliaRighe = attesaRighe = null; ordine = dati = null;
    document.body.classList.remove('in-dettaglio');
    document.getElementById('gMaster').focus();
  }
  const aperto = () => document.body.classList.contains('in-dettaglio');
  function fare(azione){
    if (azione==='abbandona') return chiudi();
    toast(`"${azione}": da collegare al servizio ERP`);
  }

  root.addEventListener('click', e => {
    const s = e.target.closest('[data-scheda]'); if (s) return mostraScheda(s.dataset.scheda);
    const t = e.target.closest('[data-tab]'); if (t) return mostraRibbon(t.dataset.tab==='azioni' ? 'azioni' : scheda);
    const c = e.target.closest('[data-chiudi]'); if (c) { c.textContent = c.closest('.d-sez').classList.toggle('chiusa') ? '⌄' : '⌃'; return; }
    const f = e.target.closest('[data-fare]'); if (f) fare(f.dataset.fare);
  });
  // in fase di cattura: nel dettaglio i tasti dell'elenco (F7, F11) non devono agire
  document.addEventListener('keydown', e => {
    if (!aperto()) return;
    const tasti = {F1:'abbandona', F8:'Elimina', F9:'Varia'};
    if (tasti[e.key]) { e.preventDefault(); e.stopPropagation(); fare(tasti[e.key]); }
    else if (e.key==='F7' || e.key==='F11') { e.preventDefault(); e.stopPropagation(); }
  }, true);

  return { apri, chiudi };
})();

/* Dettaglio del singolo ordine (sola lettura). Usa le funzioni di index.html: api, toast, esc, fmtNum, Grid, Caricamento. */
window.Dettaglio = (() => {
  /* ---------------- campi ---------------- */
  const data = iso => iso ? iso.split('-').reverse().join('/') : '';
  // casella di testo; tipo: '' | 'sel' (elenco) | 'num' | 'data'
  const casella = (v, tipo='', off=false) => `<div class="d-v ${tipo} ${off?'off':''}" title="${esc(v)}">${esc(v)}</div>`;
  const riga = (etichetta, contenuto, cls='') => `<div class="d-r"><label class="${cls}">${esc(etichetta)}</label><div class="d-f">${contenuto}</div></div>`;
  const campo = (etichetta, v, tipo='', off=false) => riga(etichetta, casella(v, tipo, off), off?'off':'');
  // on null = dato non disponibile
  const interruttore = (etichetta, on, cls='') => riga(etichetta, `<div class="d-sw ${on==null?'nd':on?'on':''}" role="img" aria-label="${on==null?'Non disponibile':on?'Sì':'No'}" ${on==null?'title="Non disponibile"':''}></div>`, cls);
  const num = (v, dec=2) => fmtNum(v, dec);
  const sezione = (titolo, sx, dx, {chiudibile=false, piu=''}={}) =>
    `<section class="d-sez"><h3><span>${esc(titolo)}</span>${piu?`<a data-fare="${piu}">${piu}</a>`:''}${chiudibile?'<button data-chiudi aria-label="Riduci o espandi">⌃</button>':''}</h3>
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
        {chiudibile:true, piu:'Mostra di più'}) +
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
  const piccolo = (id, testo, azione) => `<div class="rsmall ${azione?'':'dis'}" ${azione?`data-fare="${esc(azione)}"`:''}>${ico(id)}${testo}</div>`;
  const colonna = (...voci) => `<div class="rcol">${voci.join('')}</div>`;
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
    righe: gruppo('Nuovo', grande('d-piu','Aggiungi<br>(F4)') +
        colonna(piccolo('d-piu','Inserisci'), piccolo('i-dup','Duplica (Q)'), piccolo('i-dup','Copia ▾','Copia')) +
        colonna(piccolo('i-grid','Caricamento multiplo'), piccolo('i-check','Caricamento da elenco'))) +
      gruppo('Gestione', grande('d-lente','Dettaglio<br>(F7)','Dettaglio riga') + grande('d-elimina','Elimina<br>(F8)') +
        colonna(piccolo('d-forbici','Taglia riga'), piccolo('i-dup','Incolla Righe'), piccolo('d-elimina','Annulla taglia')) +
        colonna(piccolo('i-refresh','Ricalcolo subtotali'), piccolo('d-lente','Modifica tipo ricerca articolo'), piccolo('i-refresh','Variazione automatica righe (F3)'))) +
      gruppo('Terminalini', colonna(piccolo('i-flow','Caricamento/evasione righe con rif.ordine'), piccolo('i-flow','Evasione progressiva righe ordine'))) +
      gruppo('Evasione', colonna(piccolo('i-doc','Preventivi'), piccolo('i-doc','Ordini quadro'))) +
      gruppo('Avanzamento', colonna(piccolo('i-grid','Situazione riga ordine','Situazione riga ordine'), piccolo('i-link','Legami','Legami'))) +
      gruppo('Altre funzioni', colonna(piccolo('d-lente','Controllo marginalità'), piccolo('i-grid','Aggiorna dati proposti (F11)'), piccolo('i-chart','Collegamento a OdP tramite barcode')) +
        colonna(piccolo('i-archive','Assegna lotto minimo'), piccolo('d-lente','Controllo giacenza ▾','Controllo giacenza'))),
    interrogazioni: '<div class="d-nd">Voci non ancora disponibili</div>',
  };
  // linguette che si aggiungono ad AZIONI nelle varie schede
  const CONTESTO = {condizioni:['condizioni'], logistica:['logistica'], righe:['righe','interrogazioni']};

  /* ---------------- righe ---------------- */
  // quantità senza decimali superflui, come nella maschera
  const quantita = v => v==null || v==='' ? '' : Number(v).toLocaleString('it-IT', {maximumFractionDigits:5, useGrouping:false});
  const colonneRighe = valuta => [
    {type:'ind', w:18},
    {key:'stato_evasione', label:'E', w:48, cls:'c', render:v=>`<span class="stato ${v}" title="${v}"></span>`, fmt:v=>v},
    {key:'n', label:'Nr. riga', w:47, cls:'r', fmt:v=>fmtNum(v)},
    {key:'tipo_riga', label:'Tipo riga', w:47, cls:'r'},
    {key:'codice', label:'Codice', w:159},
    {key:'variante', label:'Variante', w:79},
    {key:'descrizione', label:'Descrizione', w:199},
    {key:'udm', label:'UdM', w:119},
    {key:'quantita', label:'Quantità', w:119, cls:'r', fmt:quantita},
    {key:'data_consegna_conf', label:'Data consegna confermata', w:95, cls:'r', fmt:fmtDate},
    {key:'data_spedizione', label:'Data spedizione', w:95, cls:'r', fmt:fmtDate},
    {key:'stato_impegno', label:'Stato impegno', w:111},
    {key:'rif_commessa', label:'Rif. Commessa', w:119},
    {key:'magazzino', label:'Mag. principale', w:79},
    {key:'listino', label:'Codice listino', w:79},
    {key:'prezzo', label:`Prezzo ${valuta}`.trim(), w:87, cls:'r', fmt:v=>fmtNum(v,4)},
  ];

  /* ---------------- struttura ---------------- */
  const menuHtml = voci => voci.map(([k,t]) => `<button data-scheda="${k}">${esc(t)}</button>`).join('');
  const marcaMenu = (el, k) => el.querySelectorAll('.d-menu button').forEach(b => { b.classList.toggle('sel', b.dataset.scheda===k); if (b.dataset.scheda===k) b.setAttribute('aria-current','page'); else b.removeAttribute('aria-current'); });
  const root = document.getElementById('dett');
  root.classList.add('d-fin');
  root.innerHTML = `<svg width="0" height="0" style="position:absolute"><defs>
    <symbol id="d-esci" viewBox="0 0 32 32"><path d="M14 4h14v24H14z" fill="#f2c069" stroke="#c79436"/><path d="M18 16H4M9 10l-6 6 6 6" fill="none" stroke="#3a6fb5" stroke-width="3"/></symbol>
    <symbol id="d-matita" viewBox="0 0 32 32"><path d="M5 3h12l6 6v20H5z" fill="#fff" stroke="#6b6b6b"/><path d="M28 13l-11 11-4 1 1-4 11-11z" fill="#5a7fb8" stroke="#34497d"/></symbol>
    <symbol id="d-salva" viewBox="0 0 32 32"><path d="M5 5h19l3 3v19H5z" fill="#8a9bc4" stroke="#5a6a94"/><path d="M10 5h11v8H10zM9 18h14v9H9z" fill="#fff"/></symbol>
    <symbol id="d-elimina" viewBox="0 0 32 32"><path d="M5 3h12l6 6v20H5z" fill="#fff" stroke="#6b6b6b"/><path d="M15 17l12 12M27 17L15 29" stroke="#c0392b" stroke-width="3"/></symbol>
    <symbol id="d-persona" viewBox="0 0 32 32"><circle cx="16" cy="10" r="6" fill="#3a6fb5"/><path d="M4 29c0-8 5-12 12-12s12 4 12 12z" fill="#3a6fb5"/></symbol>
    <symbol id="d-piu" viewBox="0 0 32 32"><path d="M4 10h24v18H4zM4 16h24M4 22h24M13 10v18" fill="#fff" stroke="#6b6b6b"/><path d="M8 1v12M2 7h12" stroke="#3aa76d" stroke-width="3"/></symbol>
    <symbol id="d-lente" viewBox="0 0 32 32"><path d="M3 4h24v20H3zM3 10h24M3 17h24M11 4v20" fill="#fff" stroke="#6b6b6b"/><circle cx="20" cy="19" r="6" fill="#e5eefa" stroke="#333" stroke-width="2"/><path d="M24 23l6 6" stroke="#333" stroke-width="3"/></symbol>
    <symbol id="d-forbici" viewBox="0 0 32 32"><circle cx="8" cy="24" r="4" fill="none" stroke="#555" stroke-width="2"/><circle cx="24" cy="24" r="4" fill="none" stroke="#555" stroke-width="2"/><path d="M10 21L23 3M22 21L9 3" stroke="#555" stroke-width="2"/></symbol>
    <symbol id="d-camion" viewBox="0 0 32 32"><path d="M2 8h18v14H2z" fill="#f2c069" stroke="#c79436"/><path d="M20 13h6l4 5v4H20z" fill="#bcd0e8" stroke="#5a7fb8"/><circle cx="8" cy="24" r="3" fill="#555"/><circle cx="25" cy="24" r="3" fill="#555"/></symbol>
  </defs></svg>
  <div class="menutabs"><div class="tab" data-tab="azioni">AZIONI</div><span class="d-ctx"></span><input class="search" placeholder="cerca nel manuale..."><div class="collapse">▲</div></div>
  <div class="ribbon"></div>
  <div class="d-titolo"></div><div class="d-sotto"></div>
  <div class="d-corpo"><nav class="d-menu">${menuHtml(MENU)}</nav><div class="d-scheda"></div></div>`;
  const $ = s => root.querySelector(s);
  const attesa = new Caricamento($('.d-corpo'), 'Caricamento ordine…');
  let ordine = null, dati = null, scheda = 'generali', grigliaRighe = null, attesaRighe = null;

  function mostraRibbon(nome){
    const linguette = CONTESTO[scheda] || [];
    $('.menutabs').classList.toggle('ctx', linguette.length > 0);
    $('[data-tab=azioni]').classList.toggle('sel', nome==='azioni');
    $('.d-ctx').innerHTML = linguette.map(k => `<div class="tab contesto ${k===nome?'sel':''}" data-tab="${k}">${k.toUpperCase()}</div>`).join('');
    $('.ribbon').innerHTML = RIBBON[nome];
  }
  function mostraScheda(k){
    scheda = k;
    marcaMenu(root, k);
    mostraRibbon(CONTESTO[k] ? k : 'azioni');
    const el = $('.d-scheda');
    attesaRighe?.annulla(); grigliaRighe = attesaRighe = null;
    el.scrollTop = 0;
    if (!dati) { el.innerHTML = ''; return; }
    if (SCHEDE[k]) el.innerHTML = SCHEDE[k](dati);
    else if (k==='righe') mostraRighe(el);
    else el.innerHTML = `<div class="d-vuota">Scheda "${esc(MENU.find(m=>m[0]===k)[1])}" non ancora disponibile.</div>`;
  }
  function mostraRighe(el){
    el.innerHTML = `<div class="d-righe panel"><div class="gtool">
      <svg data-righe="aggiorna"><title>Aggiorna</title><use href="#i-refresh"/></svg>
      <svg data-righe="stampa"><title>Stampa</title><use href="#i-print"/></svg>
      <svg data-righe="esporta"><title>Esporta in Excel</title><use href="#i-excel"/></svg>
      <select data-righe="zoom" aria-label="Zoom">${[80,90,100,110,125].map(z=>`<option ${z===100?'selected':''}>${z}%</option>`).join('')}</select>
      <svg data-righe="layout"><title>Layout griglia</title><use href="#i-grid"/></svg>
      <span class="cnt">Righe: 0</span></div><div class="gwrap" tabindex="0"></div></div>`;
    const pannello = el.firstChild, gwrap = pannello.querySelector('.gwrap');
    grigliaRighe = new Grid(gwrap, colonneRighe(dati.altri.valuta), {countEl:pannello.querySelector('.cnt'), filtri:false, totali:true, onOpen:apriRiga});
    attesaRighe = new Caricamento(pannello, 'Caricamento righe…');
    pannello.querySelector('select').onchange = e => gwrap.style.setProperty('--fs', 12*parseInt(e.target.value)/100 + 'px');
    caricaRigheDettaglio(false);
  }
  async function caricaRigheDettaglio(aggiorna){
    const g = grigliaRighe, r = await attesaRighe.esegui(`/api/ordini/${ordine.id}/righe`, aggiorna ? {aggiorna:true} : undefined);
    if (r !== undefined && g === grigliaRighe) g.setRows(r || []);
  }
  function apriRiga(){
    const r = grigliaRighe?.current(), gwrap = $('.d-righe .gwrap');
    if (!r) return toast('Selezionare una riga');
    const alto = gwrap.scrollTop, lato = gwrap.scrollLeft;
    DettaglioRiga.apri(ordine.id, r, () => { gwrap.scrollTop = alto; gwrap.scrollLeft = lato; gwrap.focus({preventScroll:true}); });
  }
  function azioneRighe(a){
    if (a==='aggiorna') return caricaRigheDettaglio(true);
    if (a==='stampa') return window.print();
    if (a==='layout') return fare('Layout griglia');
    if (a==='esporta') {
      const l = document.createElement('a'); l.href = URL.createObjectURL(new Blob(['\ufeff' + grigliaRighe.toCSV()], {type:'text/csv;charset=utf-8'}));
      l.download = `ordine_${ordine.num_reg ?? ordine.id}_righe.csv`; l.click(); setTimeout(() => URL.revokeObjectURL(l.href), 1000);
    }
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
    if (azione==='Dettaglio riga') return apriRiga();
    toast(`"${azione}": da collegare al servizio ERP`);
  }

  root.addEventListener('click', e => {
    const s = e.target.closest('[data-scheda]'); if (s) return mostraScheda(s.dataset.scheda);
    const t = e.target.closest('[data-tab]'); if (t) return mostraRibbon(t.dataset.tab);
    const q = e.target.closest('svg[data-righe]'); if (q) return azioneRighe(q.dataset.righe);
    const c = e.target.closest('[data-chiudi]'); if (c) { c.textContent = c.closest('.d-sez').classList.toggle('chiusa') ? '⌄' : '⌃'; return; }
    const f = e.target.closest('[data-fare]'); if (f) fare(f.dataset.fare);
  });
  // in fase di cattura: nel dettaglio i tasti dell'elenco (F7, F11) non devono agire
  document.addEventListener('keydown', e => {
    if (!aperto() || DettaglioRiga.aperta()) return;
    // nella scheda Righe F7 apre il dettaglio della riga ed Elimina è disattivato
    const tasti = scheda==='righe' ? {F1:'abbandona', F7:'Dettaglio riga', F9:'Varia'} : {F1:'abbandona', F8:'Elimina', F9:'Varia'};
    if (tasti[e.key]) { e.preventDefault(); e.stopPropagation(); fare(tasti[e.key]); }
    else if (e.key==='F7' || e.key==='F11') { e.preventDefault(); e.stopPropagation(); }
  }, true);

  return { apri, chiudi, ui: { data, casella, riga, campo, interruttore, num, quantita, sezione, grande, gruppo, menuHtml, marcaMenu } };
})();

/* Dettaglio della singola riga d'ordine (sola lettura). Usa i componenti di dettaglio.js e le funzioni di index.html. */
window.DettaglioRiga = (() => {
  const { data, casella, riga, campo, interruttore, num, quantita, sezione, grande, gruppo, menuHtml, marcaMenu } = Dettaglio.ui;
  const importo = v => v==null || v==='' ? '' : Number(v).toLocaleString('it-IT', {minimumFractionDigits:2, maximumFractionDigits:2, useGrouping:'always'});
  const bottone = t => `<span class="d-b">${t}</span>`;
  const caselle = (valori, tipo='', off=false) => valori.map(v => casella(v, tipo, off)).join('');
  // etichetta, unità di misura e quantità
  const misura = (etichetta, um, q, tipo='', off=true) => riga(etichetta, casella(um, tipo, off) + casella(quantita(q), 'num', off), off?'off':'');

  const SCHEDE = {
    generali: d => {
      const g = d.generali, c = d.condizioni, k = d.consegna, p = d.pesi;
      return sezione('Dati generali',
        riga('Articolo', casella(g.articolo, 'sel obb') + bottone('..')) + campo('Variante', g.variante, 'sel') +
        riga('Descrizione', `<div class="d-v d-testo" tabindex="0">${esc(g.descrizione)}</div>`) +
        riga('Formula', caselle(['','','',''], '', true), 'off') + riga('Variabile', caselle(g.variabili.map(quantita), 'num', true), 'off'),
        misura('UdM vendita', g.udm_imputare, g.qta_imputare, 'sel obb', false) + misura('Unità per collo', '', g.unita_collo) +
        misura('UdM vendita', g.udm, g.quantita, 'sel') + misura('UdM magazzino', g.udm_mag, g.qta_mag) + misura('UdM secondaria', '', g.qta_sec),
        {chiudibile:true, piu:'Mostra di più'}) +
      sezione('Condizioni commerciali',
        campo('Listino', c.listino, 'sel') + campo('Politica sconti', c.politica_sconti, 'sel') + campo('Promozione', '', '', true) +
        campo('Origine prezzo', '') + campo('Prezzo', num(c.prezzo, 4), 'num') + riga('Origine sconti', caselle(['','','','','',''])) +
        riga('% sconti', caselle(c.sconti.map(x => num(x)), 'num')) + campo('Origine sconto unitario', '') + campo('Sconto unitario', num(c.sconto_unitario, 4), 'num'),
        campo('Netto sconti', '', 'num') + riga('Importo', casella(c.valuta) + casella(importo(c.importo), 'num')) +
        interruttore('Rilevante spese/sconti', c.rilevante_spese) + interruttore('Riga da stampare', null),
        {chiudibile:true, piu:'Mostra di meno'}) +
      sezione('Consegna',
        riga('Data richiesta/confermata', casella(data(k.data_richiesta), 'num data obb') + casella(data(k.data_confermata), 'num data obb')) +
        campo('Data spedizione', data(k.data_spedizione), 'num data obb') + campo('Stato impegno', k.stato_impegno, 'sel') +
        riga('Rif. Commessa', casella(k.rif_commessa, 'sel') + bottone('..')) +
        riga('Riferimenti lotto', casella(k.lotto, 'sel') + bottone('..') + casella(data(k.lotto_data), 'num data') + casella(quantita(k.lotto_numero), 'num sel')) +
        campo('Data scadenza lotto', '', 'data', true) + campo('Riferimento riga', k.riferimento, 'sel'),
        riga('Mag. principale', casella(k.magazzino, 'sel obb') + casella(k.area, 'sel')) + riga('Nota interna', casella(k.nota) + bottone('⌕')) +
        interruttore('Blocca evasione', k.blocca_evasione) + interruttore('Sollecitata', k.sollecitata) + interruttore('Riga saldata', k.saldata),
        {chiudibile:true}) +
      sezione('Pesi e volume',
        campo('Peso lordo unitario', quantita(p.lordo), 'num') + campo('Tara unitaria', quantita(p.tara), 'num'),
        campo('Peso netto', quantita(p.netto), 'num') + campo('Volume', quantita(p.volume), 'num'), {chiudibile:true});
    },
  };
  const MENU = [['generali','Generali'],['estesa','Descrizione estesa'],['contabili','Contabili'],['analitica','Analitica'],['agenti','Agenti'],['note','Note e allegati']];
  const RIBBON = {
    azioni: gruppo('Navigazione', grande('d-esci','Abbandona<br>(F1)','abbandona')) +
      gruppo('Altre funzioni', grande('i-flow','Dati<br>FTE (F)','Dati FTE') + grande('i-chart','Scorpora<br>prezzo (S)') +
        grande('i-archive','Assegna<br>lotto minimo') + grande('d-lente','Controllo<br>giacenza ▾','Controllo giacenza')),
    help: '<div class="d-nd">Voci non ancora disponibili</div>',
  };

  const root = document.getElementById('driga');
  root.classList.add('d-fin');
  root.innerHTML = `<div class="menutabs"><div class="tab" data-tab="azioni">AZIONI</div><div class="tab" data-tab="help">HELP</div><input class="search" placeholder="cerca nel manuale..."><div class="collapse">▲</div></div>
  <div class="ribbon"></div><div class="d-titolo"></div><div class="d-sotto"></div>
  <div class="d-corpo"><nav class="d-menu">${menuHtml(MENU)}</nav><div class="d-scheda"></div></div>`;
  const $ = s => root.querySelector(s);
  const attesa = new Caricamento($('.d-corpo'), 'Caricamento riga…');
  const finestra = document.getElementById('wintitle');
  let dati = null, scheda = 'generali', titoloPrima = '', allaChiusura = null;

  function mostraRibbon(nome){
    root.querySelectorAll('[data-tab]').forEach(t => t.classList.toggle('sel', t.dataset.tab===nome));
    $('.ribbon').innerHTML = RIBBON[nome];
  }
  function mostraScheda(k){
    scheda = k; marcaMenu(root, k);
    const el = $('.d-scheda'); el.scrollTop = 0;
    el.innerHTML = !dati ? '' : SCHEDE[k] ? SCHEDE[k](dati) : `<div class="d-vuota">Scheda "${esc(MENU.find(m=>m[0]===k)[1])}" non ancora disponibile.</div>`;
  }
  function titoli(r){
    $('.d-titolo').textContent = `Tipo riga: ${[r.tipo_riga, r.des_tipo].filter(x => x!=null && x!=='').join(' - ')}`;
    const articolo = [r.codice, r.descrizione].filter(Boolean).join(' - ');
    $('.d-sotto').textContent = `Nr. riga: ${quantita(r.n)}` + (articolo ? ` | ${r.codice ? 'Articolo: ' : ''}${articolo}` : '');
  }
  const aperta = () => document.body.classList.contains('in-riga');

  // r: riga della griglia; chiusa: funzione da chiamare al ritorno
  async function apri(idOrdine, r, chiusa){
    dati = null; allaChiusura = chiusa;
    if (!aperta()) titoloPrima = finestra.textContent;
    finestra.textContent = titoloPrima.replace(' - Ditta', ' - Riga corpo - Ditta');
    document.body.classList.add('in-riga');
    titoli(r); mostraRibbon('azioni'); mostraScheda('generali');
    const d = await attesa.esegui(`/api/ordini/${idOrdine}/righe/${r.id_riga}`);
    if (d === undefined) return;
    if (d === null) return chiudi();  // errore già segnalato
    dati = d; titoli(d); mostraScheda(scheda);
    if (d.avvisi.length) toast('Dati non disponibili: ' + d.avvisi.join(', '));
  }
  function chiudi(){
    if (!aperta()) return;
    attesa.annulla(); dati = null;
    document.body.classList.remove('in-riga');
    finestra.textContent = titoloPrima;
    allaChiusura?.(); allaChiusura = null;
  }
  root.addEventListener('click', e => {
    const s = e.target.closest('[data-scheda]'); if (s) return mostraScheda(s.dataset.scheda);
    const t = e.target.closest('[data-tab]'); if (t) return mostraRibbon(t.dataset.tab);
    const c = e.target.closest('[data-chiudi]'); if (c) { c.textContent = c.closest('.d-sez').classList.toggle('chiusa') ? '⌄' : '⌃'; return; }
    const f = e.target.closest('[data-fare]'); if (!f) return;
    if (f.dataset.fare==='abbandona') chiudi(); else toast(`"${f.dataset.fare}": da collegare al servizio ERP`);
  });
  // in fase di cattura: i tasti dell'ordine e dell'elenco non devono agire
  document.addEventListener('keydown', e => {
    if (!aperta() || !['F1','F7','F8','F9','F11'].includes(e.key)) return;
    e.preventDefault(); e.stopImmediatePropagation();
    if (e.key==='F1') chiudi();
  }, true);

  return { apri, chiudi, aperta };
})();

# Elenco ordini di vendita – prototipo Python

Riproduzione della maschera "Elenco ordini di vendita" dell'ERP, servita da un backend FastAPI.

## Struttura
```
GestioneOrdiniEsolver/
  requirements.txt
  app/
    main.py            # API FastAPI + pagina
    esolver.py         # servizi REST di eSolver (token, ordini, quantità) e mappatura dei campi
    dettaglio.py       # dati del singolo ordine e della singola riga, con le descrizioni dai report
    scadenzario.py     # interrogazione scadenzario clienti (servizio ES_PC_SCAD)
    static/comune.*    # parti comuni alle pagine: stili, icone, griglia, attesa durante il caricamento
    static/index.html  # interfaccia (ribbon, viste, filtri, griglia testata + righe)
    static/dettaglio.* # maschera di dettaglio dell'ordine (schede Generali, Condizioni, Logistica, Righe)
    static/riga.js     # maschera di dettaglio della riga (schede Generali e Analitica)
    static/scadenzario.html # interrogazione scadenzario clienti
    esolver_mcp.py     # alternativa: lettura dal server MCP ES_VENDITE (login OAuth, sola lettura)
    static/snapshot.json # fotografia di ordini reali: NON è nel repository (vedi sotto)
```

## Avvio
```
py -3.14 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000
```
Apri: http://127.0.0.1:8000/?ditta=WM&ragsoc=DITTA%20DEMO&utente=UTENTE

Scadenzario clienti: http://127.0.0.1:8000/scadenzario?ditta=WM&ragsoc=DITTA%20DEMO&utente=UTENTE
(solo con la sorgente `esolver`)

### Sorgente dati (variabile `ERP_DATA`)
- `esolver` (default): tempo reale dai servizi REST, senza passare dall'MCP
  ([swagger](https://apiesolver.sistemi.com/swagger/ui/index)). Copiare `.env.example` in `.env`, poi:
  ```
  .venv\Scripts\python -m app.esolver cifra    (mostra lo SHA256 della password, da riportare in .env)
  .venv\Scripts\python -m app.esolver test     (verifica accesso, ordini e report quantità)
  ```
  Il token si ottiene con `/auth/App-{AppId}/Token`, resta solo in memoria e si rinnova da solo.
  Il file `.env` è escluso da git: lo SHA256 vale quanto la password.
- `snapshot`: `app/static/snapshot.json`, una fotografia di ordini letti da eSolver.
  **Il file contiene dati reali ed è escluso da git**: dopo un clone non c'è e va creato, nel formato
  `{"ordini": [...], "righe": {"<id ordine>": [...]}}` con i campi prodotti da `map_ordine` e `map_riga`.

  La maschera si apre sugli ultimi 30 giorni: se lo snapshot è più vecchio, allargare il filtro
  "Data registrazione" per vederne gli ordini.

- `mcp`: tramite il server MCP ES_VENDITE (sola lettura, login nel browser):
  ```
  python -m app.esolver_mcp login
  set ERP_DATA=mcp
  set ESOLVER_GROUP=WM
  ```
  Il token è salvato in `%LOCALAPPDATA%/GestioneOrdiniEsolver`. Le quantità consegnate e residue arrivano
  da DOCVEN_MCP, che non contiene tutti gli ordini: dove mancano la cella resta vuota.

## Cosa funziona
- Filtri rapidi (date, numero registrazione, intestatario, saldato) → chiamata a `/api/ordini`
- Viste nell'albero (Recenti, Da confermare, Da saldare)
- Griglia testate: intestazioni a due livelli, ordinamento al clic, riga filtro per colonna, frecce su/giù
- Selezionando un ordine si caricano le righe (`/api/ordini/{id}/righe`)
- Doppio clic / F7 / "Dettaglio": maschera dell'ordine in sola lettura (F1 per tornare); F11 aggiorna; F5 stampa
- Esportazione CSV per Excel, zoom griglie, splitter ridimensionabile, pannelli richiudibili
- Le altre voci del ribbon mostrano un avviso "da collegare al servizio ERP"

### Interrogazione scadenzario clienti (`/scadenzario`)
- Si apre dal pulsante "Scadenzario cliente" del ribbon dell'elenco ordini, nella stessa scheda e filtrata sul
  cliente dell'ordine selezionato; "Abbandona" (F1) o Indietro del browser riportano all'elenco
- Filtri: clienti (codici separati da virgola), numero documento, data scadenza e data documento,
  scadenze aperte (tutte, scadute, non scadute) e/o chiuse, data di riferimento dello scaduto,
  situazione al, insoluti, bloccate. Scorciatoie nel ribbon: "Solo scadute", "In scadenza nel mese"
- Riepilogo: residuo totale, scaduto per fasce (30/60/90 giorni e oltre), a scadere,
  acconti e note di credito (residuo negativo), rischio insoluto
- Griglia con totali; doppio clic / F7 apre la scheda completa della scadenza; F11 aggiorna; F5 stampa; CSV per Excel
- Ragione sociale e descrizione della condizione di pagamento vengono da CLIENTIELENCO_MCP e CONDPAGELENCO_MCP;
  il tipo di pagamento resta col codice
- Solo clienti: il servizio fornitori `ES_PC_SCAD/FornitoreLeggi` risponde HTTP 500 con corpo vuoto
  ogni volta che ci sono scadenze da restituire (e anche se non si indicano le anagrafiche)

## API
| Metodo | URL | Descrizione |
|---|---|---|
| GET | `/api/ordini` | elenco con filtri: `reg_da, reg_a, doc_da, doc_a, num_da, num_a, num_doc, intestatario, saldato (Si/No/Tutti), vista` |
| GET | `/api/ordini/{id}` | testata ordine |
| GET | `/api/ordini/{id}/dettaglio` | dati delle schede dell'ordine |
| GET | `/api/ordini/{id}/righe` | righe ordine (`aggiorna=true` le rilegge da eSolver) |
| GET | `/api/ordini/{id}/righe/{id_riga}` | dettaglio della singola riga |
| GET | `/api/scadenzario` | scadenze dei clienti: `aperte, tipo_aperte (tutte/scadute/non_scadute), chiuse, clienti, scad_da, scad_a, doc_da, doc_a, riferimento, situazione, num_doc, insolute, bloccate (tutte/si/no)` |
| GET | `/docs` | documentazione interattiva (Swagger) |

## Note sul servizio eSolver
- L'elenco viene dal report DOCVEN_MCP (circa 2 s). Le colonne che il report non espone restano vuote:
  comune, frazione, stato, destinatario.
- Il dettaglio viene da LeggiElenco; le descrizioni da TIPIDOC, CONDPAGELENCO, CLIENTIELENCO, CLIENTIINDIRIZZI,
  AGENTIELENCO e, per zona e capo area, DOCVEN (`_MCP`). Restano vuoti i campi che nessuno espone (rif. commessa, contatto, IBAN,
  rif. banca estera, e-mail, intestatario DDT, priorità, tipo evasione) e senza descrizione divisione, centro, stato, valuta.
- Il dettaglio della riga viene da LeggiElenco; tipo riga e nome del magazzino da DOCVEN (vuoti se la riga manca),
  UdM magazzino da ARTELENCO (`_MCP`). Vuoti: origine prezzo e sconti, promozione, netto sconti, formula, codice UdM secondaria,
  scadenza lotto. "Riga da stampare" non si usa: il servizio restituisce sempre 0, anche se in eSolver è attivo.
- **Il report non contiene tutti gli ordini**: mancano anche alcuni definitivi (4 su 58 nel periodo
  24/10-22/11/2026, causa da chiarire), che quindi non compaiono nell'elenco.
- "Saldato" vale Sì se lo sono tutte le righe presenti nel report: può differire dal filtro di eSolver.
- La vista "Da confermare" usa LeggiElenco, perché il report non espone la conferma: è completa ma impiega
  circa 1 s per ordine, dato che il servizio restituisce anche tutte le righe.
- Le righe dell'ordine selezionato vengono da LeggiElenco, che non riporta le quantità consegnate e residue:
  si aggiungono dal report; dove la riga manca la cella resta vuota.
- Queste note valgono per `ERP_DATA=esolver`: con `mcp` l'elenco viene sempre da LeggiElenco.
- Il "Riferimento" è ricostruito come anno.1.numero registrazione: il "1" centrale è un'ipotesi da verificare.

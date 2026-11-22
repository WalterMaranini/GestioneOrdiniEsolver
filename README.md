# Elenco ordini di vendita – prototipo Python

Riproduzione della maschera "Elenco ordini di vendita" dell'ERP, servita da un backend FastAPI.

## Struttura
```
GestioneOrdiniEsolver/
  requirements.txt
  app/
    main.py            # API FastAPI + pagina
    esolver.py         # servizi REST di eSolver (token, ordini, quantità) e mappatura dei campi
    static/index.html  # interfaccia (ribbon, viste, filtri, griglia testata + righe)
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
- Doppio clic / F7 / "Dettaglio": scheda dell'ordine; F11 aggiorna; F5 stampa
- Esportazione CSV per Excel, zoom griglie, splitter ridimensionabile, pannelli richiudibili
- Le altre voci del ribbon mostrano un avviso "da collegare al servizio ERP"

## API
| Metodo | URL | Descrizione |
|---|---|---|
| GET | `/api/ordini` | elenco con filtri: `reg_da, reg_a, doc_da, doc_a, num_da, num_a, num_doc, intestatario, saldato (Si/No/Tutti), vista` |
| GET | `/api/ordini/{id}` | testata ordine |
| GET | `/api/ordini/{id}/righe` | righe ordine |
| GET | `/docs` | documentazione interattiva (Swagger) |

## Note sul servizio eSolver
- LeggiElenco restituisce testata **e righe complete** (~260 KB per ordine): l'elenco
  carica tutto in una volta e le righe vengono servite dalla cache, senza nuove chiamate.
  Con molti ordini conviene usare per l'elenco il report DOCVEN_MCP e il servizio solo per il dettaglio.
- Il servizio non riporta le quantità evase/consegnate: si leggono dal report DOCVEN_MCP quando si apre
  un ordine. Il report non contiene tutti gli ordini (esclude i provvisori): dove manca la cella resta vuota.
- Il "Riferimento" è ricostruito come anno.1.numero registrazione: il "1" centrale è un'ipotesi da verificare.

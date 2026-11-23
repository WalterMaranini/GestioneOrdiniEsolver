"""
Backend FastAPI che serve la maschera "Elenco ordini di vendita".

Avvio (dalla cartella erp_ordini):
    uvicorn app.main:app --host 127.0.0.1 --port 8000

Sorgente dati (variabile d'ambiente ERP_DATA):
    esolver   (default) lettura in tempo reale dai servizi REST (vedi esolver.py per la configurazione)
    snapshot  fotografia dei dati eSolver in app/static/snapshot.json
    mcp       lettura in tempo reale dal server MCP ES_VENDITE (vedi esolver_mcp.py: serve il login)

Apri:  http://127.0.0.1:8000/?ditta=WM&ragsoc=DITTA%20DEMO&utente=UTENTE
(in produzione questi parametri arrivano dal launcher richiamato dal menu dell'ERP,
meglio se sostituiti da un token firmato).
"""
import os
from datetime import date
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .esolver import EsolverError, EsolverRepository, SnapshotRepository
from .scadenzario import Scadenzario

STATIC = Path(__file__).parent / "static"

app = FastAPI(title="ERP Tools - Ordini di vendita")


def _repository():
    load_dotenv()  # file .env del progetto; le variabili già impostate hanno la precedenza
    sorgente = os.environ.get("ERP_DATA") or "esolver"
    if sorgente == "mcp":
        from .esolver_mcp import McpRepository  # importato qui: lo snapshot non richiede l'SDK MCP
        return McpRepository()
    if sorgente == "snapshot":
        return SnapshotRepository(STATIC / "snapshot.json")
    if sorgente != "esolver":
        raise RuntimeError(f"ERP_DATA non valido: {sorgente} (valori ammessi: esolver, snapshot, mcp)")
    return EsolverRepository()


repo = _repository()


@app.exception_handler(EsolverError)
def errore_esolver(request: Request, exc: EsolverError):
    return JSONResponse({"detail": str(exc)}, status_code=exc.status)


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/ordini")
def lista_ordini(
    reg_da: Optional[date] = None,
    reg_a: Optional[date] = None,
    doc_da: Optional[date] = None,
    doc_a: Optional[date] = None,
    num_da: Optional[int] = None,
    num_a: Optional[int] = None,
    num_doc: str = "",
    intestatario: str = "",
    saldato: str = Query("Tutti", pattern="^(Si|No|Tutti)$"),
    vista: str = "recenti",
):
    return repo.lista_ordini(reg_da=reg_da, reg_a=reg_a, doc_da=doc_da, doc_a=doc_a,
                             num_da=num_da, num_a=num_a, num_doc=num_doc,
                             intestatario=intestatario, saldato=saldato, vista=vista)


@app.get("/api/ordini/{oid}")
def dettaglio_ordine(oid: int):
    o = repo.ordine(oid)
    if o is None:
        raise HTTPException(404, "Ordine non trovato")
    return o


@app.get("/api/ordini/{oid}/dettaglio")
def schede_ordine(oid: int):
    d = repo.dettaglio(oid)
    if d is None:
        raise HTTPException(404, "Ordine non trovato")
    return d


@app.get("/api/ordini/{oid}/righe")
def righe_ordine(oid: int, aggiorna: bool = False):
    if aggiorna:
        repo.dimentica(oid)
    r = repo.righe_ordine(oid)
    if r is None:
        raise HTTPException(404, "Ordine non trovato")
    return r


@app.get("/api/ordini/{oid}/righe/{id_riga}")
def riga_ordine(oid: int, id_riga: int):
    r = repo.riga(oid, id_riga)
    if r is None:
        raise HTTPException(404, "Riga non trovata")
    return r


# ----------------------------------------------------------------- scadenzario clienti

class ScadenzarioNonDisponibile(EsolverError):
    status = 501

    def __init__(self):
        super().__init__("Lo scadenzario si legge solo dai servizi REST: avviare con ERP_DATA=esolver")


# il server MCP e lo snapshot non espongono il servizio
scadenzario = Scadenzario(repo) if type(repo) is EsolverRepository else None


@app.get("/scadenzario", include_in_schema=False)
def pagina_scadenzario():
    return FileResponse(STATIC / "scadenzario.html")


@app.get("/api/scadenzario")
def leggi_scadenzario(
    aperte: bool = True,
    tipo_aperte: str = Query("tutte", pattern="^(tutte|scadute|non_scadute)$"),
    chiuse: bool = False,
    clienti: str = "",
    scad_da: Optional[date] = None,
    scad_a: Optional[date] = None,
    doc_da: Optional[date] = None,
    doc_a: Optional[date] = None,
    riferimento: Optional[date] = None,
    situazione: Optional[date] = None,
    num_doc: str = "",
    insolute: str = Query("tutte", pattern="^(tutte|si|no)$"),
    bloccate: str = Query("tutte", pattern="^(tutte|si|no)$"),
):
    if scadenzario is None:
        raise ScadenzarioNonDisponibile()
    return scadenzario.leggi(aperte=aperte, tipo_aperte=tipo_aperte, chiuse=chiuse, clienti=clienti,
                             scad_da=scad_da, scad_a=scad_a, doc_da=doc_da, doc_a=doc_a,
                             riferimento=riferimento, situazione=situazione, num_doc=num_doc,
                             insolute=insolute, bloccate=bloccate)


app.mount("/static", StaticFiles(directory=STATIC), name="static")

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
def righe_ordine(oid: int):
    r = repo.righe_ordine(oid)
    if r is None:
        raise HTTPException(404, "Ordine non trovato")
    return r


app.mount("/static", StaticFiles(directory=STATIC), name="static")

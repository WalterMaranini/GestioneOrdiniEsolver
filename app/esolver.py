"""
Collegamento a eSolver tramite il servizio ES_SRV_ORVLeggiElenco (ordini di vendita).

Contiene:
- map_ordine / map_riga: traducono la risposta di eSolver nei campi usati dalla maschera
- EsolverRepository: chiama il web service in tempo reale
- SnapshotRepository: legge una fotografia dei dati salvata in JSON (utile per demo e test)

Configurazione di EsolverRepository tramite variabili d'ambiente (file config\\.env):
    ESOLVER_ORV_URL   URL completo del servizio ES_SRV_ORVLeggiElenco (POST)
    ESOLVER_GROUP     codice gruppo (header X-BC-GROUP), es. WM
    ESOLVER_AUTH      valore dell'header Authorization (es. "Bearer xxx" o "Basic xxx")
"""
from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import Optional

import httpx

class EsolverError(RuntimeError):
    """Errore nella lettura dei dati da eSolver."""

    status = 502  # codice HTTP restituito al browser


# ----------------------------------------------------------------- mappatura campi

def map_riga(r: dict) -> dict:
    q = float(r.get("Quantita") or 0)
    saldata = bool(r.get("RigaSaldata"))
    # ES_SRV_ORVLeggiElenco non riporta le quantità evase: per quelle serve il report DOCVEN_MCP.
    cons = q if saldata else 0.0
    return {
        "stato_evasione": "evasa" if saldata else "aperta",
        "id_riga": r.get("IdRigaDoc"),
        "n": r.get("NumProgrRiga"),
        "tipo_riga": r.get("TipoRiga"),
        "codice": r.get("CodArt", ""),
        "variante": r.get("VarianteArt", ""),
        "descrizione": r.get("DesArt", ""),
        "data_consegna": r.get("DataConsegnaConf") or r.get("DataConsegnaRich") or "",
        "data_spedizione": r.get("DataSpedizione") or "",
        "udm": r.get("UnitaMisura", ""),
        "quantita": q,
        "qta_in_spedizione": 0.0,
        "qta_consegnata": cons,
        "qta_residua": q - cons,
        "prezzo": r.get("Prezzo"),
        "importo": r.get("ImportoValuta"),
    }


def map_ordine(o: dict) -> dict:
    righe = o.get("Righe") or []
    data_reg = o.get("DataRegistrazione") or ""
    anno = int(data_reg[:4]) if data_reg else None
    return {
        "id": o["IdDocumento"],
        "num_reg": o.get("NumRegistraz"),
        "data_reg": data_reg,
        # Riferimento come appare in eSolver (anno.sezionale.numero): il sezionale "1" è un'ipotesi
        "riferimento": f"{anno}.1.{o.get('NumRegistraz')}" if anno else "",
        "num_doc": o.get("NumDocOriginale", ""),
        "data_doc": o.get("DataOriginale") or "",
        "cod_cliente": str(o.get("CodCliFor", "")),
        "ragione_sociale": o.get("CliForRagSoc1", ""),
        "comune": o.get("CliForLocalita1", ""),
        "frazione": o.get("CliForLocalita2", ""),
        "provincia": o.get("CliForProv", ""),
        "stato": o.get("SpedCodStatoUe", ""),
        "esercizio": anno,
        "destinatario": o.get("DatiSpedRagSoc1", ""),
        "saldato": bool(righe) and all(r.get("RigaSaldata") for r in righe),
        "confermato": bool(o.get("OrdineConfermato")),
        "n_righe": len(righe),
        "totale": round(sum(float(r.get("ImportoValuta") or 0) for r in righe), 2),
    }


# ----------------------------------------------------------------- filtri comuni

def filtra(ordini: list[dict], reg_da=None, reg_a=None, doc_da=None, doc_a=None,
           num_da=None, num_a=None, num_doc="", intestatario="", saldato="Tutti",
           vista="recenti") -> list[dict]:
    out = []
    for o in ordini:
        if reg_da and o["data_reg"] < reg_da.isoformat(): continue
        if reg_a and o["data_reg"] > reg_a.isoformat(): continue
        if o["data_doc"]:
            if doc_da and o["data_doc"] < doc_da.isoformat(): continue
            if doc_a and o["data_doc"] > doc_a.isoformat(): continue
        if num_da is not None and (o["num_reg"] or 0) < num_da: continue
        if num_a is not None and (o["num_reg"] or 0) > num_a: continue
        if num_doc and num_doc.lower() not in o["num_doc"].lower(): continue
        if intestatario and intestatario.lower() not in f'{o["cod_cliente"]} {o["ragione_sociale"]}'.lower():
            continue
        if saldato == "Si" and not o["saldato"]: continue
        if saldato == "No" and o["saldato"]: continue
        if vista == "da_confermare" and o["confermato"]: continue
        if vista == "da_saldare" and o["saldato"]: continue
        out.append(o)
    return sorted(out, key=lambda o: -o["id"])


# ----------------------------------------------------------------- repository

class SnapshotRepository:
    """Dati letti da un file JSON nel formato {ordini: [...], righe: {id: [...]}}."""

    def __init__(self, path: Path):
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        self._ordini = d["ordini"]
        self._righe = {int(k): v for k, v in d["righe"].items()}

    def lista_ordini(self, **filtri) -> list[dict]:
        return filtra(self._ordini, **filtri)

    def ordine(self, oid: int) -> Optional[dict]:
        return next((o for o in self._ordini if o["id"] == oid), None)

    def righe_ordine(self, oid: int) -> Optional[list[dict]]:
        return self._righe.get(oid)


class EsolverRepository:
    """Legge in tempo reale da eSolver con ES_SRV_ORVLeggiElenco."""

    PAGE = 20

    def __init__(self, url: str | None = None, group: str | None = None, auth: str | None = None):
        self.url = url or os.environ["ESOLVER_ORV_URL"]
        self.group = group or os.environ.get("ESOLVER_GROUP", "WM")
        headers = {"X-BC-GROUP": self.group, "Content-Type": "application/json"}
        if auth or os.environ.get("ESOLVER_AUTH"):
            headers["Authorization"] = auth or os.environ["ESOLVER_AUTH"]
        self.http = httpx.Client(headers=headers, timeout=120)
        self._cache_righe: dict[int, list[dict]] = {}
        self._cache_ordini: dict[int, dict] = {}

    def _chiama(self, payload: dict) -> list[dict]:
        """Chiama il servizio paginando con Skip/Take e restituisce i documenti grezzi."""
        dati, skip = [], 0
        while True:
            r = self.http.post(self.url, json={**payload, "Skip": skip, "Take": self.PAGE})
            r.raise_for_status()
            d = r.json()
            if d.get("Risposta", {}).get("Esito") != 1:
                raise EsolverError(f"eSolver: {d.get('Risposta', {}).get('Errori')}")
            pagina = d.get("Dati") or []
            dati += pagina
            if len(pagina) < self.PAGE:
                return dati
            skip += self.PAGE

    def lista_ordini(self, reg_da: Optional[date] = None, reg_a: Optional[date] = None,
                     num_da: Optional[int] = None, num_a: Optional[int] = None,
                     intestatario: str = "", saldato: str = "Tutti", vista: str = "recenti",
                     **altri) -> list[dict]:
        payload: dict = {"TipoAnagrafica": 1}
        if reg_da: payload["DataRegistrazioneDa"] = reg_da.isoformat()
        if reg_a: payload["DataRegistrazioneA"] = reg_a.isoformat()
        if num_da: payload["NumeroRegistrazDa"] = num_da
        if num_a and num_a < 9999999: payload["NumeroRegistrazA"] = num_a
        if intestatario.strip().isdigit(): payload["ElencoCodCliFor"] = intestatario.strip()
        payload["Saldato"] = {"No": 1, "Si": 2}.get(saldato, 0)
        if vista == "da_confermare": payload["OrdineConfermato"] = 1
        if vista == "da_saldare": payload["Saldato"] = 1

        ordini = []
        for raw in self._chiama(payload):
            o = map_ordine(raw)
            self._cache_ordini[o["id"]] = o
            self._cache_righe[o["id"]] = [map_riga(r) for r in raw.get("Righe") or []]
            ordini.append(o)
        # i filtri non gestiti dal servizio (ragione sociale, date documento...) si applicano qui
        return filtra(ordini, intestatario=intestatario, saldato=saldato, vista=vista, **altri)

    def ordine(self, oid: int) -> Optional[dict]:
        if oid not in self._cache_ordini:
            self._carica(oid)
        return self._cache_ordini.get(oid)

    def righe_ordine(self, oid: int) -> Optional[list[dict]]:
        if oid not in self._cache_righe:
            self._carica(oid)
        return self._cache_righe.get(oid)

    def _carica(self, oid: int):
        for raw in self._chiama({"ElencoIdDocumento": str(oid)}):
            self._cache_ordini[oid] = map_ordine(raw)
            self._cache_righe[oid] = [map_riga(r) for r in raw.get("Righe") or []]

"""
Collegamento diretto ai servizi REST di eSolver (swagger: https://apiesolver.sistemi.com/swagger/ui/index).

Contiene:
- map_ordine / map_riga / map_report: traducono la risposta di eSolver nei campi usati dalla maschera
- EsolverRest: client REST (token, gruppo, errori)
- EsolverRepository: legge gli ordini in tempo reale
- SnapshotRepository: legge una fotografia dei dati salvata in JSON (utile per demo e test)

Servizi usati, tutti di sola lettura:
- /auth/App-{AppId}/Token                   token di accesso, richiesto di nuovo quando scade
- /report/App-{AppId}/RunReport/DOCVEN_MCP  elenco degli ordini, quantità consegnate e residue. È veloce ma
  non contiene tutti gli ordini (mancano anche alcuni definitivi) né tutte le colonne: quelle che non
  espone restano vuote, e dove manca la riga le quantità restano vuote (None), non 0.
- /api/ES_ORV/App-{AppId}/LeggiElenco       righe dell'ordine selezionato e vista "Da confermare" (il report
  non espone la conferma). Completo, ma impiega circa 1 s per ordine.

Configurazione tramite variabili d'ambiente o file .env nella cartella del progetto (vedi .env.example):
    ESOLVER_USER              utente eSolver
    ESOLVER_PASSWORD_SHA256   password cifrata SHA256 (comando: python -m app.esolver cifra)
    ESOLVER_GROUP             codice gruppo, es. WM
    ESOLVER_GROUP_PWD_SHA256  eventuale password del gruppo, cifrata SHA256
    ESOLVER_APPID             "Sistemi" (default) o la ApiKey fornita per le installazioni SIR
    ESOLVER_URL               indirizzo dei servizi (default: https://apiesolver.sistemi.com)

Comandi:
    python -m app.esolver cifra   chiede una password e ne mostra lo SHA256
    python -m app.esolver test    verifica accesso, ordini e report quantità
"""
from __future__ import annotations

import getpass
import hashlib
import json
import logging
import os
import ssl
import sys
import threading
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv

log = logging.getLogger(__name__)

ESOLVER_URL = "https://apiesolver.sistemi.com"
DOCVEN = "DOCVEN_MCP"
TIPO_MOVIMENTO_ORDINE = "4"


class EsolverError(RuntimeError):
    """Errore nella lettura dei dati da eSolver."""

    status = 502  # codice HTTP restituito al browser


class ConfigurazioneMancante(EsolverError):
    """Mancano le credenziali per i servizi REST."""

    status = 503


# ----------------------------------------------------------------- mappatura campi

def _data(v) -> str:
    """Data ISO senza ora. I servizi REST usano date-time: il valore nullo può arrivare come anno 1 o 1900."""
    v = str(v or "")[:10]
    return "" if v[:4] in ("0001", "1900") else v


def map_riga(r: dict) -> dict:
    q = float(r.get("Quantita") or 0)
    saldata = bool(r.get("RigaSaldata"))
    # LeggiElenco non riporta le quantità evase: si aggiungono dopo con il report DOCVEN_MCP.
    cons = q if saldata else 0.0
    return {
        "stato_evasione": "evasa" if saldata else "aperta",
        "id_riga": r.get("IdRigaDoc"),
        "n": r.get("NumProgrRiga"),
        "tipo_riga": r.get("TipoRiga"),
        "codice": r.get("CodArt") or "",
        "variante": r.get("VarianteArt") or "",
        "descrizione": r.get("DesArt") or "",
        "data_consegna": _data(r.get("DataConsegnaConf")) or _data(r.get("DataConsegnaRich")),
        "data_spedizione": _data(r.get("DataSpedizione")),
        "udm": r.get("UnitaMisura") or "",
        "quantita": q,
        "qta_in_spedizione": 0.0,
        "qta_consegnata": cons,
        "qta_residua": q - cons,
        "prezzo": r.get("Prezzo"),
        "importo": r.get("ImportoValuta"),
    }


def map_ordine(o: dict) -> dict:
    righe = o.get("Righe") or []
    data_reg = _data(o.get("DataRegistrazione"))
    anno = int(data_reg[:4]) if data_reg else None
    return {
        "id": o["IdDocumento"],
        "num_reg": o.get("NumRegistraz"),
        "data_reg": data_reg,
        # Riferimento come appare in eSolver (anno.sezionale.numero): il sezionale "1" è un'ipotesi
        "riferimento": f"{anno}.1.{o.get('NumRegistraz')}" if anno else "",
        "num_doc": o.get("NumDocOriginale") or "",
        "data_doc": _data(o.get("DataOriginale")),
        "cod_cliente": str(o.get("CodCliFor") or ""),
        "ragione_sociale": o.get("CliForRagSoc1") or "",
        "comune": o.get("CliForLocalita1") or "",
        "frazione": o.get("CliForLocalita2") or "",
        "provincia": o.get("CliForProv") or "",
        "stato": o.get("SpedCodStatoUe") or "",
        "esercizio": anno,
        "destinatario": o.get("DatiSpedRagSoc1") or "",
        "saldato": bool(righe) and all(r.get("RigaSaldata") for r in righe),
        "confermato": bool(o.get("OrdineConfermato")),
        "n_righe": len(righe),
        "totale": round(sum(float(r.get("ImportoValuta") or 0) for r in righe), 2),
    }


def map_report(righe: list[dict]) -> dict:
    """Testata dell'ordine dalle sue righe nel report DOCVEN; ciò che il report non espone resta vuoto."""
    r = righe[0]
    data_reg = _data(r.get("DataRegistraz"))
    esercizio = r.get("EsercizioContabile")
    return {
        "id": r["IdDocumento"],
        "num_reg": r.get("NumRegistraz"),
        "data_reg": data_reg,
        # come in map_ordine: il sezionale "1" è un'ipotesi
        "riferimento": f"{data_reg[:4]}.1.{r.get('NumRegistraz')}" if data_reg else "",
        "num_doc": r.get("NumDocumento") or "",
        "data_doc": _data(r.get("DataDoc")),
        "cod_cliente": str(r.get("CliForCod") or ""),
        "ragione_sociale": r.get("RagSocCompleta") or "",
        "comune": "",
        "frazione": "",
        "provincia": r.get("CliForProv") or "",
        "stato": "",
        "esercizio": int(esercizio) if esercizio else None,
        "destinatario": "",
        "saldato": all(x.get("DesFlussoSaldato") == "Si" for x in righe),
        "confermato": None,
        # non esposti, e non ricavabili: in alcuni ordini il report non contiene tutte le righe
        "n_righe": None,
        "totale": None,
    }


def applica_quantita(riga: dict, docven: dict | None) -> dict:
    """Aggiunge le quantità di DOCVEN; se la riga non c'è restano sconosciute (None)."""
    cons = docven.get("QtTotCarScarUmDoc") if docven else None
    residua = docven.get("QtOrdImpUmDoc") if docven else None
    stato = riga["stato_evasione"]
    if stato != "evasa" and cons:
        stato = "parziale"
    return {**riga, "stato_evasione": stato, "qta_in_spedizione": None,
            "qta_consegnata": cons, "qta_residua": residua}


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


class EsolverRest:
    """Client dei servizi REST: ottiene il token, lo rinnova quando scade e traduce gli errori."""

    def __init__(self, transport: httpx.BaseTransport | None = None):
        self.base = (os.environ.get("ESOLVER_URL") or ESOLVER_URL).rstrip("/")
        self.app = "App-" + (os.environ.get("ESOLVER_APPID") or "Sistemi")
        self.user = os.environ.get("ESOLVER_USER") or ""
        self.key = os.environ.get("ESOLVER_PASSWORD_SHA256") or ""
        self.group = os.environ.get("ESOLVER_GROUP") or "WM"
        headers = {"X-BC-Gruppo": self.group}
        if os.environ.get("ESOLVER_GROUP_PWD_SHA256"):
            headers["X-BC-GruppoPwd"] = os.environ["ESOLVER_GROUP_PWD_SHA256"]
        # i certificati sono quelli di Windows, compresi quelli aziendali
        self.http = httpx.Client(headers=headers, timeout=120, transport=transport,
                                 verify=ssl.create_default_context())
        self._token = ""
        self._lock = threading.Lock()

    def leggi_ordini(self, payload: dict) -> dict:
        return self._post(f"/api/ES_ORV/{self.app}/LeggiElenco", payload)

    def report(self, nome: str, payload: dict):
        return self._post(f"/report/{self.app}/RunReport/{nome}", payload)

    def accedi(self, scaduto: str = "") -> str:
        """Restituisce il token; se è assente o è quello scaduto ne chiede uno nuovo."""
        with self._lock:
            # un altro thread può averlo già rinnovato
            if not self._token or self._token == scaduto:
                self._token = ""
                self._token = self._nuovo_token()
            return self._token

    def _post(self, percorso: str, payload: dict):
        token = self.accedi()
        r = self._invia(percorso, payload, {"X-BC-Authorization": token})
        if self._rifiutato(r):  # token scaduto: si accede di nuovo, una volta sola
            token = self.accedi(scaduto=token)
            r = self._invia(percorso, payload, {"X-BC-Authorization": token})
        if not r.is_success:
            raise EsolverError(f"eSolver: HTTP {r.status_code} da {percorso} {r.text[:200]}".rstrip())
        return self._json(r, percorso)

    @staticmethod
    def _rifiutato(r: httpx.Response) -> bool:
        # lo swagger documenta 401, ma senza token il server risponde 400 senza testo
        return r.status_code == 401 or (r.status_code == 400 and not r.content)

    def _nuovo_token(self) -> str:
        if not self.user or not self.key:
            raise ConfigurazioneMancante(
                "Credenziali eSolver mancanti: impostare ESOLVER_USER e ESOLVER_PASSWORD_SHA256 nel file .env")
        percorso = f"/auth/{self.app}/Token"
        r = self._invia(percorso, {"User": self.user, "Key": self.key}, {})
        if not r.is_success:  # il testo della risposta non si riporta: è il servizio delle credenziali
            raise EsolverError(f"Accesso a eSolver rifiutato (HTTP {r.status_code}): verificare utente e password")
        token = self._json(r, percorso)
        if not isinstance(token, str) or not token.strip():
            raise EsolverError("Accesso a eSolver: il servizio Token non ha restituito un token")
        return token.strip()

    def _invia(self, percorso: str, payload: dict, headers: dict) -> httpx.Response:
        try:
            return self.http.post(self.base + percorso, json=payload, headers=headers)
        except httpx.HTTPError as e:
            raise EsolverError(f"eSolver non raggiungibile: {type(e).__name__}: {e}") from e

    @staticmethod
    def _json(r: httpx.Response, percorso: str):
        try:
            return r.json()
        except ValueError:
            raise EsolverError(f"eSolver: risposta non valida da {percorso}") from None


class EsolverRepository:
    """Legge gli ordini in tempo reale dai servizi REST."""

    PAGE = 20
    ELENCO_DA_REPORT = True

    def __init__(self, rest: EsolverRest | None = None):
        self.rest = rest or EsolverRest()
        self._azzera()

    def _azzera(self):
        self._cache_righe: dict[int, list[dict]] = {}
        self._cache_ordini: dict[int, dict] = {}
        self._con_quantita: set[int] = set()

    def _chiama(self, payload: dict) -> list[dict]:
        """Legge tutti i documenti grezzi, una pagina alla volta."""
        dati: list[dict] = []
        visti: set[int] = set()
        while True:
            nuovi = documenti_nuovi(
                self.rest.leggi_ordini({**payload, "Skip": len(dati), "Take": self.PAGE}), visti)
            if not nuovi:
                return dati
            dati += nuovi

    def _righe_docven(self, filtri: list[dict]) -> list[dict]:
        # Take 0 = tutte le righe: senza un ordinamento garantito le pagine potrebbero ripetersi
        d = self.rest.report(DOCVEN, {"Skip": 0, "Take": 0, "Filters": filtri, "Digits": []})
        righe = d.get("result") if isinstance(d, dict) else d
        if not isinstance(righe, list):
            raise EsolverError(f"{DOCVEN}: risposta inattesa")
        return righe

    def lista_ordini(self, **filtri) -> list[dict]:
        # il report non espone la conferma: quella vista si legge dal servizio
        if self.ELENCO_DA_REPORT and filtri.get("vista") != "da_confermare":
            return self._lista_report(**filtri)
        return self._lista_servizio(**filtri)

    def _lista_report(self, reg_da: Optional[date] = None, reg_a: Optional[date] = None,
                      intestatario: str = "", **altri) -> list[dict]:
        filtri = [
            {"Name": "TipoMovimento", "Operators": 11, "Values": [TIPO_MOVIMENTO_ORDINE]},
            {"Name": "DesTipoAnagrafica", "Operators": 11, "Values": ["CLIENTE"]},
            {"Name": "DataRegistraz", "Operators": 3, "Values": [
                reg_da.strftime("%d%m%Y") if reg_da else "01011800",
                reg_a.strftime("%d%m%Y") if reg_a else "31122099"]},
        ]
        if intestatario.strip().isdigit():
            filtri.append({"Name": "CliForCod", "Operators": 11, "Values": [intestatario.strip()]})
        # il saldato non si filtra nel report: lavora per riga e falserebbe lo stato dell'ordine
        per_ordine: dict[int, list[dict]] = {}
        for r in self._righe_docven(filtri):
            per_ordine.setdefault(r["IdDocumento"], []).append(r)
        self._azzera()  # le righe degli ordini vanno rilette dopo ogni aggiornamento dell'elenco
        return filtra([map_report(r) for r in per_ordine.values()],
                      reg_da=reg_da, reg_a=reg_a, intestatario=intestatario, **altri)

    def _lista_servizio(self, reg_da: Optional[date] = None, reg_a: Optional[date] = None,
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
            ordini.append(self._memorizza(raw))
        # i filtri non gestiti dal servizio (ragione sociale, date documento...) si applicano qui
        return filtra(ordini, intestatario=intestatario, saldato=saldato, vista=vista, **altri)

    def _memorizza(self, raw: dict) -> dict:
        o = map_ordine(raw)
        self._con_quantita.discard(o["id"])
        self._cache_ordini[o["id"]] = o
        self._cache_righe[o["id"]] = [map_riga(r) for r in raw.get("Righe") or []]
        return o

    def ordine(self, oid: int) -> Optional[dict]:
        if oid not in self._cache_ordini:
            self._carica(oid)
        return self._cache_ordini.get(oid)

    def righe_ordine(self, oid: int) -> Optional[list[dict]]:
        if oid not in self._cache_righe:
            self._carica(oid)
        righe, ordine = self._cache_righe.get(oid), self._cache_ordini.get(oid)
        # ordine None: un altro aggiornamento dell'elenco ha appena svuotato la cache
        if righe is None or ordine is None or oid in self._con_quantita:
            return righe
        try:
            evaso = self._quantita(ordine)
        except EsolverError as e:
            if e.status == 503:  # accesso mancante: va segnalato
                raise
            log.warning("Quantità evase non disponibili per l'ordine %s: %s", oid, e)
            return [applica_quantita(r, None) for r in righe]
        righe = [applica_quantita(r, evaso.get(r["id_riga"])) for r in righe]
        self._cache_righe[oid] = righe
        self._con_quantita.add(oid)
        return righe

    def _quantita(self, o: dict) -> dict[int, dict]:
        """Righe DOCVEN dell'ordine. Il report non filtra per IdDocumento: si usano cliente e data."""
        giorno = date.fromisoformat(o["data_reg"]).strftime("%d%m%Y")
        righe = self._righe_docven([
            {"Name": "TipoMovimento", "Operators": 11, "Values": [TIPO_MOVIMENTO_ORDINE]},
            {"Name": "CliForCod", "Operators": 11, "Values": [o["cod_cliente"]]},
            {"Name": "DataRegistraz", "Operators": 3, "Values": [giorno, giorno]},
        ])
        return {r["IdRigaDoc"]: r for r in righe if r.get("IdDocumento") == o["id"]}

    def _carica(self, oid: int):
        for raw in self._chiama({"ElencoIdDocumento": str(oid)}):
            if raw["IdDocumento"] == oid:
                self._memorizza(raw)


def documenti_nuovi(d: dict, visti: set[int]) -> list[dict]:
    """Controlla l'esito di LeggiElenco e restituisce gli ordini non ancora visti.

    NumeroDocumenti conta la pagina, non il totale: si prosegue finché arrivano ordini nuovi.
    """
    risposta = (d.get("Risposta") if isinstance(d, dict) else None) or {}
    if risposta.get("Esito") != 1:
        errori = [str(e.get("MSG")) if isinstance(e, dict) else str(e) for e in risposta.get("Errori") or []]
        raise EsolverError("eSolver: " + ("; ".join(errori) or "risposta inattesa"))
    nuovi = []
    for o in d.get("Dati") or []:
        if o["IdDocumento"] not in visti:
            visti.add(o["IdDocumento"])
            nuovi.append(o)
    return nuovi


# ----------------------------------------------------------------- comandi

def main(argv: list[str]) -> int:
    load_dotenv()
    comando = argv[0] if argv else ""
    if comando == "cifra":
        print(hashlib.sha256(getpass.getpass("Password: ").encode("utf-8")).hexdigest())
        return 0
    if comando != "test":
        print(__doc__)
        return 2
    repo = EsolverRepository()
    try:
        repo.rest.accedi()
        print(f"Accesso riuscito (gruppo {repo.rest.group}).")
        oggi = date.today()
        ordini = repo.lista_ordini(reg_da=oggi - timedelta(days=7), reg_a=oggi)
        print(f"Ordini degli ultimi 7 giorni: {len(ordini)}")
        if ordini:
            trovate = repo._quantita(ordini[0])
            print(f"Report {DOCVEN}: {len(trovate)} righe per l'ordine {ordini[0]['id']}")
    except EsolverError as e:
        print(f"Errore: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

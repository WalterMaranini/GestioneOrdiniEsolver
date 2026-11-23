"""
Interrogazione scadenzario clienti: servizio REST ES_PC_SCAD/ClienteLeggi (sola lettura).

Il servizio restituisce le scadenze con i soli codici: ragione sociale e descrizione della condizione
di pagamento vengono dai report CLIENTIELENCO_MCP e CONDPAGELENCO_MCP. Se un report non risponde
l'elenco si mostra lo stesso, senza quelle descrizioni e con un avviso.

La variante fornitori (ES_PC_SCAD/FornitoreLeggi) non si usa: risponde HTTP 500 con corpo vuoto
ogni volta che ci sono scadenze da restituire.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from .esolver import EsolverError, EsolverRepository

log = logging.getLogger(__name__)

PERCORSO = "/api/ES_PC_SCAD/App-{app}/ClienteLeggi"
# valori dei filtri a tre stati: Tutte / Solo con / Solo senza
TRE_STATI = {"tutte": -1, "si": 1, "no": 0}
TIPO_APERTE = {"tutte": -1, "scadute": 1, "non_scadute": 0}


class FiltroNonValido(EsolverError):
    status = 422


def _testo(v) -> str:
    return str(v if v is not None else "").strip()


def _iso(d: Optional[date]) -> str:
    return d.isoformat() if d else ""


def elenco_codici(testo: str) -> str:
    """Codici anagrafica separati da virgola, come li vuole il servizio. Accetta anche spazi e punti e virgola."""
    codici = [c for c in testo.replace(";", ",").replace(" ", ",").split(",") if c]
    if not all(c.isdigit() for c in codici):
        raise FiltroNonValido("Indicare i clienti con il codice numerico, separati da virgola")
    return ",".join(codici)


def parametri(aperte: bool = True, tipo_aperte: str = "tutte", chiuse: bool = False,
              clienti: str = "", scad_da: Optional[date] = None, scad_a: Optional[date] = None,
              doc_da: Optional[date] = None, doc_a: Optional[date] = None,
              riferimento: Optional[date] = None, situazione: Optional[date] = None,
              num_doc: str = "", insolute: str = "tutte", bloccate: str = "tutte") -> dict:
    """Parametri della richiesta; quelli vuoti si omettono e il servizio usa i suoi default."""
    p = {
        "FlagScadenzeAperte": int(aperte), "ScadenzeAperte": TIPO_APERTE.get(tipo_aperte, -1),
        "FlagScadenzeChiuse": int(chiuse),
        "ElencoAnagrafiche": elenco_codici(clienti),
        "DataScadenzaDal": _iso(scad_da), "DataScadenzaAl": _iso(scad_a),
        "DataDocumentoDal": _iso(doc_da), "DataDocumentoAl": _iso(doc_a),
        "DataRiferimentoScaduto": _iso(riferimento or date.today()), "SituazioneAl": _iso(situazione),
        "NumeroDocumento": num_doc.strip(),
        "ScadenzeInsolute": TRE_STATI.get(insolute, -1), "ScadenzeBloccate": TRE_STATI.get(bloccate, -1),
    }
    return {k: v for k, v in p.items() if v != ""}


def map_scadenza(s: dict, clienti: dict[str, str], pagamenti: dict[str, str]) -> dict:
    cliente = _testo(s.get("CodiceAnagrafica"))
    cond = _testo(s.get("CondPagamento"))
    giorni = s.get("GiorniScadutoAl") or 0
    residuo = s.get("ResiduoUdc") or 0
    return {
        "id": f"{s.get('IdDocumento')}.{s.get('IDRigaDocumento')}.{s.get('NumProgScadenza')}",
        "id_documento": s.get("IdDocumento"), "n_scadenza": s.get("NumProgScadenza"),
        "data_scadenza": _testo(s.get("ScadenzaData")),
        "giorni_scaduto": giorni if residuo > 0 and giorni > 0 else 0,
        # chiusa / credito del cliente (acconto, nota di credito: residuo negativo) / scaduta / non scaduta
        "stato": "chiusa" if not residuo else "credito" if residuo < 0 else "scaduta" if giorni > 0 else "aperta",
        "bloccata": bool(s.get("ScadenzaBloccata")), "insoluto": bool(s.get("ScadenzaInsoluto")),
        "sollecito": _testo(s.get("ScadenzaSollecito")), "inesigibile": bool(s.get("CreditiInesigibili")),
        "cod_cliente": cliente, "cliente": clienti.get(cliente, ""), "conto": _testo(s.get("CodConto")),
        "sigla": _testo(s.get("SiglaDocumento")), "num_doc": _testo(s.get("NumeroDocumento")),
        "data_doc": _testo(s.get("DataDocumento")),
        "num_reg": _testo(s.get("NumeroRegistrazione")), "data_reg": _testo(s.get("DataRegistrazione")),
        "registro": _testo(s.get("RifRegistro")),
        "tipo_pagamento": _testo(s.get("TipoPagamento")),
        "cond_pagamento": " - ".join(x for x in (cond, pagamenti.get(cond, "")) if x),
        "banca": s.get("CodBanca") or "", "agente": s.get("CodAgente") or "",
        "commessa": _testo(s.get("RifCommessa")), "valuta": _testo(s.get("CodiceValuta")),
        "totale_doc": s.get("TotDocumento"), "apertura": s.get("AperturaUdc"),
        "storno": s.get("StornoCompensUdc"), "inesigibili": s.get("CredInesigibiliUdc"),
        "incassato": s.get("IncassatoUdc"), "incassato_no_cont": s.get("IncassatoNoContabilUdc"),
        "residuo": residuo, "rischio_insoluto": s.get("RischioInsolutoUdc"),
    }


class Scadenzario:
    """Legge le scadenze dei clienti; le descrizioni dei codici restano in memoria."""

    def __init__(self, repo: EsolverRepository):
        self.repo = repo
        self._clienti: dict[str, str] = {}
        self._pagamenti: dict[str, str] | None = None

    def leggi(self, **filtri) -> dict:
        rest = self.repo.rest
        d = rest._post(PERCORSO.format(app=rest.app.removeprefix("App-")), {"Parametri": parametri(**filtri)})
        risposta = (d.get("Risposta") if isinstance(d, dict) else None) or {}
        if risposta.get("Esito") != 1:
            errori = [_testo(e.get("MSG")) for e in risposta.get("Errori") or [] if isinstance(e, dict)]
            raise EsolverError("eSolver: " + ("; ".join(errori) or "risposta inattesa"))
        grezze = d.get("Scadenze") or []
        avvisi: list[str] = []
        clienti = self._nomi({_testo(s.get("CodiceAnagrafica")) for s in grezze}, avvisi)
        pagamenti = self._condizioni(avvisi) if grezze else {}
        scadenze = [map_scadenza(s, clienti, pagamenti) for s in grezze]
        scadenze.sort(key=lambda s: (s["data_scadenza"], s["cod_cliente"], s["num_doc"]))
        return {"scadenze": scadenze, "avvisi": avvisi}

    def _report(self, nome: str, filtri: list[dict], cosa: str, avvisi: list[str]) -> list[dict]:
        try:
            return self.repo._righe_report(nome, filtri)
        except EsolverError as e:
            if e.status == 503:  # accesso mancante: va segnalato
                raise
            log.warning("Scadenzario, %s non disponibile (%s): %s", cosa, nome, e)
            avvisi.append(cosa)
            return []

    def _nomi(self, codici: set[str], avvisi: list[str]) -> dict[str, str]:
        mancanti = sorted(c for c in codici - set(self._clienti) if c)
        if mancanti:
            righe = self._report("CLIENTIELENCO_MCP", [{"Name": "CodCliFor", "Operators": 11, "Values": mancanti}],
                                 "ragione sociale dei clienti", avvisi)
            self._clienti.update({_testo(r.get("CodCliFor")): _testo(r.get("RagSocCompleta")) for r in righe})
        return self._clienti

    def _condizioni(self, avvisi: list[str]) -> dict[str, str]:
        if self._pagamenti is None:
            righe = self._report("CONDPAGELENCO_MCP", [], "descrizione delle condizioni di pagamento", avvisi)
            pagamenti = {_testo(r.get("CodCondizPagamento")): _testo(r.get("Des")) for r in righe}
            if righe:  # se il report non ha risposto si riprova alla prossima lettura
                self._pagamenti = pagamenti
            return pagamenti
        return self._pagamenti
